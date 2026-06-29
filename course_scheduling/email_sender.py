"""Email transport via AppleScript and Mail.app for schedule change alerts."""

# Standard Library
import logging
import subprocess
import time

# PIP3 modules
import applescript

# Recipients for schedule change alerts
RECIPIENTS = ("rseiser@roosevelt.edu", "nvoss@roosevelt.edu")


#============================================
def compose_email_applescript(recipients: tuple, subject: str, body: str, attachment_path: str) -> str:
	"""
	Build an AppleScript that sends an email with an attachment via Mail.app.

	Args:
		recipients: Tuple of email addresses.
		subject: Email subject line.
		body: Email body text.
		attachment_path: POSIX path to the xlsx attachment.

	Returns:
		AppleScript source text.
	"""
	# Escape backslashes and double quotes for AppleScript strings
	safe_subject = subject.replace('\\', '\\\\').replace('"', '\\"')
	safe_body = body.replace('\\', '\\\\').replace('"', '\\"')
	# Build recipient blocks
	recipient_lines = ""
	for addr in recipients:
		recipient_lines += f'\t\t\tmake new to recipient with properties {{address:"{addr}"}}\n'
	script_text = f'''
	tell application "Mail"
		activate
		delay 3
		set theMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_body}", visible:true}}
		tell theMessage
{recipient_lines}
			set theAttachment to POSIX file "{attachment_path}"
			make new attachment with properties {{file name:theAttachment}} at after the last paragraph
			delay 2
			send
		end tell
	end tell
	'''
	return script_text


#============================================
def _reopen_and_retry(scpt: applescript.AppleScript) -> None:
	"""
	Reopen Mail.app and retry the AppleScript send once.

	Waits 30 seconds, reopens Mail.app, waits another 10 seconds, then runs the
	script again. A failure on this second attempt is allowed to propagate so the
	caller's change cache stays untouched.

	Args:
		scpt: The compiled AppleScript send to retry.
	"""
	logging.info("Retrying in 30 seconds after reopening Mail")
	time.sleep(30)
	subprocess.run(["open", "-a", "Mail"], check=False)
	time.sleep(10)
	# Second attempt; if this fails, the exception propagates so cache stays untouched
	scpt.run()


#============================================
def send_email(recipients: tuple, subject: str, body: str, attachment_path: str) -> None:
	"""
	Compose and execute AppleScript to send the schedule email.

	Args:
		recipients: Tuple of email addresses.
		subject: Email subject line.
		body: Email body text.
		attachment_path: POSIX path to the xlsx attachment.
	"""
	script_text = compose_email_applescript(recipients, subject, body, attachment_path)
	logging.info("Sending email to %s", ", ".join(recipients))
	logging.info("AppleScript:\n%s", script_text)
	# Pre-open Mail.app in case it is closed; failure here is not fatal
	subprocess.run(["open", "-a", "Mail"], check=False)
	time.sleep(10)
	scpt = applescript.AppleScript(script_text)
	try:
		scpt.run()
	except applescript.ScriptError as exc:
		logging.warning("First send attempt failed: %s", exc)
		_reopen_and_retry(scpt)
	logging.info("Email sent successfully")
