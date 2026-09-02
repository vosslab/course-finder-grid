#!/usr/bin/env python3
"""Send the Mail.app permission test email used before daemon startup."""

# local repo modules
import course_scheduling.email_sender
import course_scheduling.report_logging


#============================================
def main() -> None:
	"""Send one test email to verify Mail.app automation permission."""
	course_scheduling.report_logging.setup_logging()
	print("Allow Mail.app Automation access if macOS asks.", flush=True)
	course_scheduling.email_sender.send_startup_test_email()
	print("Test email sent to nvoss@roosevelt.edu.", flush=True)


if __name__ == '__main__':
	main()
