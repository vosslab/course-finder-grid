"""Email transport through the CourseFinderMailer.app Mail capability."""

# Standard Library
import json
import logging
import os
import pathlib
import subprocess
import tempfile
import time


#============================================
def _get_repo_root() -> pathlib.Path:
	"""
	Resolve the repository root through Git.

	Returns:
		The absolute repository root path.
	"""
	# Fixed argv elements avoid shell interpretation (ASVS 1.2.5).
	completed = subprocess.run(
		["git", "rev-parse", "--show-toplevel"],
		capture_output=True,
		check=True,
		cwd=pathlib.Path(__file__).resolve().parent,
		text=True,
	)
	return pathlib.Path(completed.stdout.strip())


# Recipients for schedule change alerts
RECIPIENTS = ("rseiser@roosevelt.edu", "nvoss@roosevelt.edu")
STARTUP_TEST_RECIPIENT = "nvoss@roosevelt.edu"
ALLOWED_RECIPIENTS = frozenset(RECIPIENTS)

REPO_ROOT = _get_repo_root()
MAILER_APP_PATH = REPO_ROOT / "CourseFinderMailer.app"
MAILER_EXECUTABLE_PATH = MAILER_APP_PATH / "Contents" / "MacOS" / "CourseFinderMailer"
MAILER_TIMEOUT_SECONDS = 120
MAIL_REQUEST_VERSION = 1
MAIL_RESULT_MAX_BYTES = 16_384


class MailHelperError(RuntimeError):
	"""CourseFinderMailer could not validate, launch, or send a request."""


#============================================
def build_mail_request(
	recipients: tuple[str, ...],
	subject: str,
	body: str,
	attachment_path: str | None,
) -> dict:
	"""
	Build the bounded request consumed by CourseFinderMailer.app.

	Args:
		recipients: Approved email addresses.
		subject: Email subject line.
		body: Email body text.
		attachment_path: Optional POSIX path to the xlsx attachment.

	Returns:
		A JSON-serializable mail request.

	Raises:
		ValueError: A recipient is empty, duplicated, or outside the allowlist.
		FileNotFoundError: The requested attachment does not exist.
	"""
	# Limit the helper capability to the two established report recipients
	# (ASVS 2.2.1 and 8.1.1).
	recipient_set = set(recipients)
	if not recipients or len(recipient_set) != len(recipients):
		raise ValueError("Mail recipients must be nonempty and unique.")
	if not recipient_set.issubset(ALLOWED_RECIPIENTS):
		raise ValueError("Mail request contains an unapproved recipient.")

	resolved_attachment = None
	if attachment_path is not None:
		resolved_attachment = str(pathlib.Path(attachment_path).resolve(strict=True))

	request = {
		"version": MAIL_REQUEST_VERSION,
		"recipients": list(recipients),
		"subject": subject,
		"body": body,
		"attachment_path": resolved_attachment,
	}
	return request


#============================================
def _write_private_request(request_path: pathlib.Path, request: dict) -> None:
	"""
	Write one mail request with owner-only permissions.

	Args:
		request_path: Internally generated path for the JSON request.
		request: JSON-serializable helper request.
	"""
	# Create the request by descriptor inside tempfile's private directory; no
	# caller-controlled filename reaches the filesystem (ASVS 5.3.2).
	open_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
	file_descriptor = os.open(request_path, open_flags, 0o600)
	with os.fdopen(file_descriptor, 'w', encoding='utf-8') as request_file:
		json.dump(request, request_file, ensure_ascii=True)


#============================================
def _read_mail_result(result_path: pathlib.Path) -> None:
	"""
	Validate the helper result and raise when Mail did not send.

	Args:
		result_path: Expected JSON result path beside the private request.

	Raises:
		MailHelperError: The result is missing, oversized, or reports failure.
	"""
	if not result_path.is_file():
		raise MailHelperError("CourseFinderMailer exited without a result.")
	if result_path.stat().st_size > MAIL_RESULT_MAX_BYTES:
		raise MailHelperError("CourseFinderMailer returned an oversized result.")
	try:
		with result_path.open(encoding='utf-8') as result_file:
			result = json.load(result_file)
	except (OSError, UnicodeError, json.JSONDecodeError) as exc:
		raise MailHelperError("CourseFinderMailer returned invalid result JSON.") from exc
	if not isinstance(result, dict):
		raise MailHelperError("CourseFinderMailer returned an invalid result object.")
	try:
		status = result["status"]
	except KeyError as exc:
		raise MailHelperError("CourseFinderMailer returned an incomplete result.") from exc
	# The helper's status is authoritative. Swift may omit its optional error
	# detail after a successful send (ASVS 1.5.2, 2.2.1, and 16.5.3).
	if status == "sent":
		return
	if status != "failed":
		raise MailHelperError("CourseFinderMailer returned an unknown result status.")
	if "error" in result and isinstance(result["error"], str):
		error_message = result["error"]
		raise MailHelperError(f"CourseFinderMailer failed: {error_message}")
	raise MailHelperError("CourseFinderMailer failed without error detail.")


#============================================
def _send_with_helper(
	recipients: tuple[str, ...],
	subject: str,
	body: str,
	attachment_path: str | None,
) -> None:
	"""
	Launch the stable app identity and wait for its explicit result.

	Args:
		recipients: Approved email addresses.
		subject: Email subject line.
		body: Email body text.
		attachment_path: Optional POSIX path to the xlsx attachment.

	Raises:
		MailHelperError: The helper is absent, times out, exits, or reports failure.
	"""
	if not MAILER_EXECUTABLE_PATH.is_file():
		raise MailHelperError(
			"CourseFinderMailer.app is missing; run "
			"./build_course_finder_mailer.sh first."
		)

	request = build_mail_request(recipients, subject, body, attachment_path)
	with tempfile.TemporaryDirectory(prefix="course_finder_mailer_") as temp_dir:
		request_path = pathlib.Path(temp_dir) / "request.json"
		result_path = pathlib.Path(f"{request_path}.result.json")
		_write_private_request(request_path, request)

		# Pass only an internally generated path as an argv element. Dynamic mail
		# fields never enter a shell command or AppleScript source (ASVS 1.2.5).
		command = [
			"/usr/bin/open",
			"-n",
			"-W",
			str(MAILER_APP_PATH),
			"--args",
			str(request_path),
		]
		try:
			completed = subprocess.run(command, check=False, timeout=MAILER_TIMEOUT_SECONDS)
		except subprocess.TimeoutExpired as exc:
			raise MailHelperError("CourseFinderMailer timed out.") from exc
		if completed.returncode != 0:
			raise MailHelperError(
				f"CourseFinderMailer launch exited with status {completed.returncode}."
			)
		_read_mail_result(result_path)


#============================================
def _reopen_and_retry(
	recipients: tuple[str, ...],
	subject: str,
	body: str,
	attachment_path: str,
) -> None:
	"""
	Reopen Mail.app and retry the helper send once.

	The delay lets a transient send failure settle before Mail is reopened. The
	second wait gives Mail time to initialize; any retry failure propagates to
	the caller so the report is never logged as sent.

	Args:
		recipients: Approved email addresses.
		subject: Email subject line.
		body: Email body text.
		attachment_path: POSIX path to the xlsx attachment.
	"""
	logging.info("Retrying in 30 seconds after reopening Mail")
	time.sleep(30)
	subprocess.run(["/usr/bin/open", "-a", "Mail"], check=False)
	time.sleep(10)
	_send_with_helper(recipients, subject, body, attachment_path)


#============================================
def send_startup_test_email() -> None:
	"""
	Send one startup test through the stable Mail.app helper identity.

	A failure propagates to the launcher so the daemon does not start without a
	working Mail.app transport.
	"""
	subject = "Course finder daemon startup test"
	body = "Mail.app automation is available to the course finder daemon."
	recipients = (STARTUP_TEST_RECIPIENT,)
	logging.info("Sending daemon startup test email to %s", STARTUP_TEST_RECIPIENT)
	# Record authorization denial or helper failure before failing closed
	# (ASVS 16.3.2, 16.3.4, and 16.5.3).
	try:
		_send_with_helper(recipients, subject, body, None)
	except MailHelperError as exc:
		logging.error("Daemon startup test email failed: %s", exc)
		raise
	logging.info("Daemon startup test email sent successfully")


#============================================
def send_email(
	recipients: tuple[str, ...],
	subject: str,
	body: str,
	attachment_path: str,
) -> None:
	"""
	Send the schedule email through CourseFinderMailer.app.

	Args:
		recipients: Approved email addresses.
		subject: Email subject line.
		body: Email body text.
		attachment_path: POSIX path to the xlsx attachment.
	"""
	logging.info("Sending email to %s", ", ".join(recipients))
	try:
		_send_with_helper(recipients, subject, body, attachment_path)
	except MailHelperError as exc:
		logging.warning("First send attempt failed: %s", exc)
		_reopen_and_retry(recipients, subject, body, attachment_path)
	logging.info("Email sent successfully")
