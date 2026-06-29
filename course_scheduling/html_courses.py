"""
HTML source loader: parsed course records -> grid rows.

Applies the FilterSpec and expands parsed course records into per-meeting grid
rows. HTML parsing itself lives in course_scheduling.banner_parser; this module
does no parsing, only filtering and expansion.
"""

# Standard Library
import datetime

# local repo modules
import course_scheduling.banner_parser
import course_scheduling.crosslist_resolver
import course_scheduling.course_filter


#============================================

def expand_courses_to_grid_rows(courses: list, lab_only: bool = False) -> list:
	"""
	Expand intermediate course dicts into per-meeting grid rows.

	Args:
		courses: List of intermediate course dicts.
		lab_only: When True, keep only the longest meeting per course
			and append its room to the label.

	Returns:
		List of grid row dicts with Label, Days, Start, End, Waitlisted, Enrollment_Ratio.
	"""
	grid_rows = []
	for course in courses:
		meetings = course["meetings"]
		# In lab-only mode with multiple meetings, keep only the longest (the lab)
		if lab_only and len(meetings) > 1:
			def meeting_duration(m: dict) -> float:
				# Compute duration in minutes from Start and End time objects
				start_dt = datetime.datetime.combine(datetime.datetime.min, m["Start"])
				end_dt = datetime.datetime.combine(datetime.datetime.min, m["End"])
				delta = (end_dt - start_dt).total_seconds() / 60.0
				return delta
			meetings = [max(meetings, key=meeting_duration)]

		label_display = course["label"].replace(' ', '\n')
		# In lab-only mode, append room from first meeting to label
		if lab_only:
			room = meetings[0].get("Room", "") if meetings else ""
			if room:
				label_display += "\n" + room

		for meeting in meetings:
			days = meeting["Days"]
			start_time = meeting["Start"]
			end_time = meeting["End"]
			# Skip invalid meetings
			if start_time is None or end_time is None:
				continue
			if not days:
				continue
			row = {
				"Label": label_display,
				"Days": days,
				"Start": start_time,
				"End": end_time,
				"Waitlisted": course["waitlisted"],
				"Enrollment_Ratio": course["enrollment_ratio"],
			}
			grid_rows.append(row)
	return grid_rows


#============================================

def load_grid_rows(html_files: list, filter_spec: course_scheduling.course_filter.FilterSpec) -> tuple[list, list, list, list]:
	"""
	Load grid rows from saved Course Finder HTML files.

	Parses each HTML file into course records, merges cross-listed sections,
	and expands the survivors into per-meeting grid rows. The companion raw and
	lab-debug audit rows and the merged course list are returned alongside so
	callers can write the analysis tables.

	Args:
		html_files: List of saved HTML file paths to parse.
		filter_spec: Filter state controlling which courses are kept.

	Returns:
		Tuple of (grid_rows, raw_rows, lab_debug_rows, merged_courses).
	"""
	all_courses = []
	raw_rows = []
	lab_debug_rows = []
	for input_file in html_files:
		parsed_courses, parsed_raw_rows, parsed_lab_debug_rows = course_scheduling.banner_parser.load_and_parse_class_data_from_file(input_file, filter_spec)
		all_courses.extend(parsed_courses)
		raw_rows.extend(parsed_raw_rows)
		lab_debug_rows.extend(parsed_lab_debug_rows)

	# Merge cross-listed courses, then expand into per-meeting grid rows
	merged_courses = course_scheduling.crosslist_resolver.merge_cross_listed_courses(all_courses)
	# Pass lab_only flag to keep only the longest meeting per course on lab grids
	grid_rows = expand_courses_to_grid_rows(merged_courses, lab_only=filter_spec.lab_only)

	return grid_rows, raw_rows, lab_debug_rows, merged_courses
