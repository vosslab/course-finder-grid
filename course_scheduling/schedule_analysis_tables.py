"""
Schedule analysis table writers for the HTML schedule grid.

Provides xlsx writers for two policy-audit tables: courses that partially
overlap the T/R common hour, and courses that do not start on official
provost time blocks.
"""

# PIP3 modules
import openpyxl

# local repo modules
import course_scheduling.schedule_time


#============================================

# Fixed column order for both analysis tables
ANALYSIS_COLUMNS = ["Label", "Days", "Start", "End", "Room"]


#============================================

def write_analysis_rows(rows: list, output_path: str, sheet_name: str) -> None:
	"""
	Write analysis rows to a single-sheet xlsx (no index column).

	When there are no rows the sheet is left empty, matching the prior
	empty-DataFrame output.

	Args:
		rows: List of dict rows keyed by ANALYSIS_COLUMNS.
		output_path: Path for the output xlsx file.
		sheet_name: Name for the single worksheet.
	"""
	workbook = openpyxl.Workbook()
	worksheet = workbook.active
	worksheet.title = sheet_name
	# Only emit a header and data when there is at least one row
	if rows:
		worksheet.append(ANALYSIS_COLUMNS)
		for row in rows:
			worksheet.append([row[column] for column in ANALYSIS_COLUMNS])
	workbook.save(output_path)


#============================================

def write_common_hour_table(courses: list, output_path: str) -> None:
	"""
	Write a table of courses that partially overlap the T/R common hour.

	Args:
		courses: List of intermediate course dicts (post-merge).
		output_path: Path for the output xlsx file.
	"""
	rows = []
	for course in courses:
		for meeting in course["meetings"]:
			days = meeting["Days"]
			start_time = meeting["Start"]
			end_time = meeting["End"]
			if start_time is None or end_time is None or not days:
				continue
			if course_scheduling.schedule_time.is_common_hour_conflict(days, start_time, end_time):
				rows.append({
					"Label": course["label"],
					"Days": " ".join(days),
					"Start": start_time.strftime("%H:%M"),
					"End": end_time.strftime("%H:%M"),
					"Room": meeting.get("Room", ""),
				})
	write_analysis_rows(rows, output_path, "common_hour_conflicts")
	print(f"Common hour conflicts saved to:\n\t{output_path}")


#============================================

def write_timeblock_table(courses: list, output_path: str) -> None:
	"""
	Write a table of courses that do not start on official provost time blocks.

	Args:
		courses: List of intermediate course dicts (post-merge).
		output_path: Path for the output xlsx file.
	"""
	rows = []
	for course in courses:
		for meeting in course["meetings"]:
			days = meeting["Days"]
			start_time = meeting["Start"]
			end_time = meeting["End"]
			if start_time is None or not days:
				continue
			if not course_scheduling.schedule_time.is_official_time_block(days, start_time):
				rows.append({
					"Label": course["label"],
					"Days": " ".join(days),
					"Start": start_time.strftime("%H:%M"),
					"End": end_time.strftime("%H:%M") if end_time else "",
					"Room": meeting.get("Room", ""),
				})
	write_analysis_rows(rows, output_path, "nonstandard_timeblocks")
	print(f"Non-standard time blocks saved to:\n\t{output_path}")
