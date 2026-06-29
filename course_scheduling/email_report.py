"""
Email subject and body composition for the schedule change report.

Builds the operator-facing email text from the detected changes: a subject line
keyed to today's date, a header noting the last run and the gap since, and the
human-readable change summary. Holds no transport logic; email_sender delivers.
"""

# Standard Library
import datetime


#============================================

def build_email_subject(today: datetime.date) -> str:
	"""
	Build the email subject line for a report run.

	Args:
		today: The date the report is generated.

	Returns:
		Subject line like "Course Schedule Grid for Mon, June 29".
	"""
	day_name = today.strftime("%a")
	month_day = today.strftime("%B %-d")
	subject = f"Course Schedule Grid for {day_name}, {month_day}"
	return subject


#============================================

def build_date_header(today: datetime.date, last_run: datetime.date | None) -> str:
	"""
	Build the date header showing the last run and the gap since then.

	Args:
		today: The date the report is generated.
		last_run: Date of the previous successful run, or None on a first run.

	Returns:
		Header text ending with a blank line.
	"""
	today_str = today.strftime("%a, %B %-d")
	if last_run is not None:
		last_run_str = last_run.strftime("%a, %B %-d")
		gap_days = (today - last_run).days
		header = f"Last run: {last_run_str} | Today: {today_str} | Gap: {gap_days} days\n\n"
	else:
		header = f"First run: {today_str}\n\n"
	return header


#============================================

def build_email_body(today: datetime.date, last_run: datetime.date | None,
		changed_subjects: list, total_count: int, change_summary: str) -> str:
	"""
	Build the email body from the detected changes.

	Args:
		today: The date the report is generated.
		last_run: Date of the previous successful run, or None on a first run.
		changed_subjects: Subject codes with meaningful changes.
		total_count: Total number of subjects checked this run.
		change_summary: Human-readable summary of what changed.

	Returns:
		Email body text (without the attachment line, appended by the caller).
	"""
	change_count = len(changed_subjects)
	subjects_str = ", ".join(changed_subjects)
	body = build_date_header(today, last_run)
	body += f"{change_count} of {total_count} subjects have updated course data: {subjects_str}\n\n"
	body += f"Changes detected:\n{change_summary}\n"
	return body
