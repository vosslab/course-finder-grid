"""
Course-record builder for saved Course Finder (Banner) HTML pages.

Loads a saved HTML file, iterates over course result boxes, and produces
filtered course dicts plus raw and lab-debug audit rows.
"""

# Standard Library
import os

# PIP3 modules
import lxml.html

# local repo modules
import course_scheduling.html_tokens
import course_scheduling.course_label
import course_scheduling.lab_filter
import course_scheduling.course_filter
import course_scheduling.enrollment_parse


#============================================

def load_and_parse_class_data_from_file(input_file: str, filter_spec: course_scheduling.course_filter.FilterSpec) -> tuple[list, list, list]:
	"""
	Load and parse class data from the provided HTML file.

	Args:
		input_file: HTML file to parse.
		filter_spec: Filter state controlling which courses are kept.

	Returns:
		Tuple of (filtered_class_rows, raw_rows, lab_debug_rows).
	"""
	if not os.path.exists(input_file):
		raise FileNotFoundError(f"File '{input_file}' not found.")

	with open(input_file, "r", encoding="utf-8") as handle:
		html_text = handle.read()

	root = lxml.html.fromstring(html_text)
	course_boxes = root.xpath("//div[contains(@class,'courseResultsBox') and .//div[contains(@class,'dataLabel') and normalize-space()='Class']]")

	class_data = []
	raw_rows = []
	lab_debug_rows = []
	for course_box in course_boxes:
		class_element = course_scheduling.html_tokens.find_data_value_element(course_box, "Class")
		class_text = course_scheduling.html_tokens.extract_text(class_element)
		subject, course_number, section, label = course_scheduling.course_label.normalize_course_label(class_text)
		title_element = course_scheduling.html_tokens.find_first_data_value_element(course_box, [
			"Title",
			"Subject / Course and Title",
			"Subject/Course and Title",
			"Course Title",
		])
		title_text = course_scheduling.html_tokens.extract_text(title_element)

		box_text = course_scheduling.html_tokens.normalize_label_text(course_box.text_content())
		upper_text = box_text.upper()
		waitlisted = "WAITLISTED" in upper_text or "CLOSED" in upper_text

		when_element = course_scheduling.html_tokens.find_data_value_element(course_box, "When / Where")
		when_text = course_scheduling.html_tokens.extract_text(when_element)

		enrolled_element = course_scheduling.html_tokens.find_data_value_element(course_box, "Enrolled")
		enrolled_text = course_scheduling.html_tokens.extract_text(enrolled_element)
		enrollment_ratio = course_scheduling.enrollment_parse.parse_enrollment_ratio(enrolled_text)

		# Extract attributes (e.g. "Lab Course and Natural Science")
		attributes_element = course_scheduling.html_tokens.find_data_value_element(course_box, "Attributes")
		attributes_text = course_scheduling.html_tokens.extract_text(attributes_element)

		# Extract instructor name
		instructor_element = course_scheduling.html_tokens.find_data_value_element(course_box, "Instructor")
		instructor_text = course_scheduling.html_tokens.extract_text(instructor_element)

		# Extract CRN (course reference number). The live Course Finder page
		# exposes this as a dataLabel of exactly "CRN" with a sibling dataValue
		# holding the numeric reference (for example 11194). When a section has
		# no CRN value, fall back to its own Label so every row keeps a
		# populated CRN for downstream per-term memory keying.
		crn_element = course_scheduling.html_tokens.find_data_value_element(course_box, "CRN")
		crn_text = course_scheduling.html_tokens.extract_text(crn_element)
		if not crn_text:
			crn_text = label

		# Extract cross-listing info
		crosslist_element = course_scheduling.html_tokens.find_data_value_element(course_box, "Cross-listed With")
		crosslist_text = course_scheduling.html_tokens.extract_text(crosslist_element)
		crosslist_labels = []
		if crosslist_text:
			# Split on " and " to get individual cross-listed course labels
			crosslist_labels = [s.strip() for s in crosslist_text.split(" and ") if s.strip()]

		meetings = []
		if when_text:
			meetings = course_scheduling.html_tokens.parse_meeting_blocks(when_text)

		campus = course_scheduling.html_tokens.infer_campus_from_text(when_text) if when_text else None
		level = course_scheduling.course_label.infer_level_from_course_number(course_number) if course_number is not None else None
		course_text_for_filters = f"{class_text} {title_text}"
		lab_filter_details = course_scheduling.lab_filter.get_lab_filter_details(
			label, course_text_for_filters, attributes_text=attributes_text
		)

		include_row = False
		exclusion_reason = "label_parse_error"
		if label is not None and subject is not None and course_number is not None and section is not None:
			include_row, exclusion_reason = course_scheduling.course_filter.evaluate_class_inclusion(
				filter_spec, label, subject, course_number, level, campus,
				course_text=course_text_for_filters, attributes_text=attributes_text,
			)

		raw_row = {
			"Source_File": os.path.basename(input_file),
			"Class_Raw": class_text,
			"Label": label,
			"CRN": crn_text,
			"Subject": subject,
			"Course_Number": course_number,
			"Section": section,
			"Title": title_text,
			"Instructor": instructor_text,
			"When_Where": when_text,
			"Enrolled": enrolled_text,
			"Enrollment_Ratio": enrollment_ratio,
			"Attributes": attributes_text,
			"Cross_Listed_With": crosslist_text,
			"Campus": campus,
			"Level": level,
			"Meetings_Count": len(meetings),
			"Waitlisted": waitlisted,
			"Whitelist_Key": lab_filter_details["whitelist_key"],
			"Whitelist_Lab_Course": lab_filter_details["whitelist_lab_course"],
			"Section_Is_B_Lab": lab_filter_details["section_is_lab"],
			"Has_LAB_Token": lab_filter_details["has_lab_token"],
			"Has_LEC_Token": lab_filter_details["has_lec_token"],
			"Has_Lab_Attribute": lab_filter_details["has_lab_attribute"],
			"Potential_False_Negative": lab_filter_details["potential_false_negative"],
			"Lab_Probable": lab_filter_details["is_probable_lab"],
			"Lab_Reason": lab_filter_details["reason"],
			"Included_By_Current_Filters": include_row,
			"Exclusion_Reason": exclusion_reason,
		}
		lab_debug_row = {
			"Source_File": os.path.basename(input_file),
			"Label": label,
			"Section": section,
			"Title": title_text,
			"Instructor": instructor_text,
			"Whitelist_Key": lab_filter_details["whitelist_key"],
			"Whitelist_Lab_Course": lab_filter_details["whitelist_lab_course"],
			"Section_Is_B_Lab": lab_filter_details["section_is_lab"],
			"Has_LAB_Token": lab_filter_details["has_lab_token"],
			"Has_LEC_Token": lab_filter_details["has_lec_token"],
			"Has_Lab_Attribute": lab_filter_details["has_lab_attribute"],
			"Potential_False_Negative": lab_filter_details["potential_false_negative"],
			"Lab_Probable": lab_filter_details["is_probable_lab"],
			"Lab_Reason": lab_filter_details["reason"],
			"Included_By_Current_Filters": include_row,
			"Exclusion_Reason": exclusion_reason,
		}

		if label is None or subject is None or course_number is None or section is None:
			raw_rows.append(raw_row)
			lab_debug_rows.append(lab_debug_row)
			continue

		if not when_text:
			raw_row["Included_By_Current_Filters"] = False
			raw_row["Exclusion_Reason"] = "missing_when_where"
			lab_debug_row["Included_By_Current_Filters"] = False
			lab_debug_row["Exclusion_Reason"] = "missing_when_where"
			raw_rows.append(raw_row)
			lab_debug_rows.append(lab_debug_row)
			continue

		if not meetings:
			raw_row["Included_By_Current_Filters"] = False
			raw_row["Exclusion_Reason"] = "no_meetings"
			lab_debug_row["Included_By_Current_Filters"] = False
			lab_debug_row["Exclusion_Reason"] = "no_meetings"
			raw_rows.append(raw_row)
			lab_debug_rows.append(lab_debug_row)
			continue

		if not include_row:
			raw_rows.append(raw_row)
			lab_debug_rows.append(lab_debug_row)
			continue

		raw_rows.append(raw_row)
		lab_debug_rows.append(lab_debug_row)

		# Build intermediate course dict for cross-list merging
		intermediate_course = {
			"label": label,
			"subject": subject,
			"course_number": course_number,
			"section": section,
			"meetings": meetings,
			"waitlisted": waitlisted,
			"enrollment_ratio": enrollment_ratio,
			"crosslist_labels": crosslist_labels,
		}
		class_data.append(intermediate_course)

	return class_data, raw_rows, lab_debug_rows
