#!/usr/bin/env python3
"""Test CourseFinderMailer's permission to automate Mail.app."""

# local repo modules
import course_scheduling.email_sender
import course_scheduling.report_logging


#============================================
def main() -> None:
	"""Send one test email through CourseFinderMailer's Automation grant."""
	course_scheduling.report_logging.setup_logging()
	print("Allow CourseFinderMailer to control Mail if macOS asks.", flush=True)
	course_scheduling.email_sender.send_startup_test_email()
	print("Test email sent to nvoss@roosevelt.edu.", flush=True)


if __name__ == '__main__':
	main()
