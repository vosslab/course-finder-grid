"""Email transport via AppleScript and Mail.app for schedule change alerts."""

# Standard Library
import logging
import subprocess
import time

# PIP3 modules
import applescript

# Recipients for schedule change alerts
RECIPIENTS = ("rseiser@roosevelt.edu", "nvoss@roosevelt.edu")
STARTUP_TEST_RECIPIENT = "nvoss@roosevelt.edu"


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
def compose_startup_test_applescript() -> str:
	"""
	Build the plain test message used to verify Mail.app automation access.

	Returns:
		AppleScript source for one test email to the daemon operator.
	"""
	script_text = 'tell application "Mail"\n'
	script_text += '\tactivate\n'
	script_text += '\tdelay 3\n'
	script_text += '\tset theMessage to make new outgoing message with properties '
	script_text += '{subject:"Course finder daemon startup test", '
	script_text += 'content:"Mail.app automation is available to the course finder daemon.", '
	script_text += 'visible:true}\n'
	script_text += '\ttell theMessage\n'
	script_text += '\t\tmake new to recipient with properties '
	script_text += f'{{address:"{STARTUP_TEST_RECIPIENT}"}}\n'
	script_text += '\t\tdelay 2\n'
	script_text += '\t\tsend\n'
	script_text += '\tend tell\n'
	script_text += 'end tell\n'
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
def send_startup_test_email() -> None:
	"""
	Send one startup test email to verify Mail.app automation access.

	A failure propagates to the launcher so the daemon does not start without a
	working Mail.app transport.
	"""
	script_text = compose_startup_test_applescript()
	logging.info("Sending daemon startup test email to %s", STARTUP_TEST_RECIPIENT)
	subprocess.run(["open", "-a", "Mail"], check=False)
	time.sleep(3)
	scpt = applescript.AppleScript(script_text)
	# Record authorization denial or Mail control failure before failing closed
	# (ASVS 16.3.2 and 16.3.4).
	try:
		scpt.run()
	except applescript.ScriptError as exc:
		logging.error("Daemon startup test email failed: %s", exc)
		raise
	logging.info("Daemon startup test email sent successfully")


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
