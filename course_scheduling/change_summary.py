"""Human-readable change summary builders for schedule diff reports."""

# Standard Library
import re

# local repo modules
import course_scheduling.course_title
import course_scheduling.html_tokens
import course_scheduling.lab_filter

# Display labels for columns shown in change summaries
COLUMN_DISPLAY_NAMES = {
	"CRN": "course reference number",
	"Title": "title",
	"Instructor": "instructor",
	"Attributes": "format",
	"Campus": "campus",
	"Cross_Listed_With": "cross-listing",
	"Level": "level",
}

COURSE_TYPE_SUFFIX_RE = re.compile(
	r"\s*(?:-\s*)?(?:LAB|LABORATORY|LEC|LECT|LECTURE)\s*$",
	re.IGNORECASE,
)


#============================================
def format_change_value(value: str) -> str:
	"""
	Normalize a CSV field value for compact change summaries.
	"""
	cleaned = " ".join(str(value).split()).strip()
	if not cleaned:
		return "(blank)"
	return cleaned


#============================================
def format_display_title(raw_title: str) -> str:
	"""
	Normalize and title-case a course title for report display.

	Args:
		raw_title: Title text straight from a snapshot row or full event.

	Returns:
		Readable title case text, or "(blank)" when the title is empty.
	"""
	cleaned = format_change_value(raw_title)
	if cleaned == "(blank)":
		return cleaned
	display_title = course_scheduling.course_title.smart_title_case(cleaned)
	return display_title


#============================================
def describe_when_where_changes(old_when: str, new_when: str) -> str:
	"""
	Describe schedule/location changes as a readable sentence.

	Args:
		old_when: Previous Banner When / Where text.
		new_when: Current Banner When / Where text.

	Returns:
		A sentence describing the changed schedule details.
	"""
	old_blocks = course_scheduling.html_tokens.parse_meeting_blocks(old_when)
	new_blocks = course_scheduling.html_tokens.parse_meeting_blocks(new_when)
	if not old_blocks or not new_blocks:
		description = (
			f'The schedule changed from "{format_change_value(old_when)}" to '
			f'"{format_change_value(new_when)}"'
		)
		return description

	old_first = old_blocks[0]
	new_first = new_blocks[0]
	descriptions = []

	old_days = "".join(old_first["Days"])
	new_days = "".join(new_first["Days"])
	if old_days != new_days:
		descriptions.append(f"meeting days changed from {old_days} to {new_days}")

	old_time = (
		f"{old_first['Start'].strftime('%I:%M %p').lstrip('0')}-"
		f"{old_first['End'].strftime('%I:%M %p').lstrip('0')}"
	)
	new_time = (
		f"{new_first['Start'].strftime('%I:%M %p').lstrip('0')}-"
		f"{new_first['End'].strftime('%I:%M %p').lstrip('0')}"
	)
	if old_time != new_time:
		descriptions.append(f"meeting time changed from {old_time} to {new_time}")

	old_room = format_change_value(old_first.get("Room", ""))
	new_room = format_change_value(new_first.get("Room", ""))
	if old_room != new_room:
		descriptions.append(f'room changed from "{old_room}" to "{new_room}"')

	if len(old_blocks) != len(new_blocks):
		descriptions.append(
			f"number of meetings changed from {len(old_blocks)} to {len(new_blocks)}"
		)

	if not descriptions:
		description = (
			f'The schedule changed from "{format_change_value(old_when)}" to '
			f'"{format_change_value(new_when)}"'
		)
		return description
	description = "The " + "; the ".join(descriptions)
	return description


#============================================
def describe_field_change(column_name: str, old_value: str, new_value: str) -> str:
	"""
	Describe a changed CSV field as a readable sentence.

	Args:
		column_name: Snapshot column whose value changed.
		old_value: Previous snapshot value.
		new_value: Current snapshot value.

	Returns:
		A sentence describing the field change.
	"""
	if column_name == "When_Where":
		return describe_when_where_changes(old_value, new_value)

	label = COLUMN_DISPLAY_NAMES.get(column_name)
	if label is None:
		label = column_name.replace("_", " ").lower()
	if column_name == "Title":
		old_text = format_display_title(old_value)
		new_text = format_display_title(new_value)
		description = f'The {label} changed from "{old_text}" to "{new_text}"'
		return description

	old_text = format_change_value(old_value)
	new_text = format_change_value(new_value)
	description = f'The {label} changed from "{old_text}" to "{new_text}"'
	return description


#============================================
def title_without_course_type(raw_title: str) -> str:
	"""
	Remove a trailing lab/lecture designation for comparison only.

	Args:
		raw_title: Banner course title.

	Returns:
		The title without a trailing lab or lecture token.
	"""
	cleaned = format_change_value(raw_title)
	base_title = COURSE_TYPE_SUFFIX_RE.sub("", cleaned).strip()
	return base_title


#============================================
def detect_course_type_designation(label: str, old_row: dict, new_row: dict) -> str | None:
	"""
	Detect a newly explicit lab or lecture designation.

	The parser's many audit flags are deliberately translated back into one
	operator-facing fact. This also recognizes removal of a conflicting
	"Lab Course" attribute from a title already marked LEC/LECT.

	Args:
		label: Normalized course-section label.
		old_row: Previous snapshot row.
		new_row: Current snapshot row.

	Returns:
		"lab" or "lecture" for a semantic assignment, otherwise None.
	"""
	old_details = course_scheduling.lab_filter.get_lab_filter_details(
		label,
		old_row.get("Title", ""),
		old_row.get("Attributes", ""),
	)
	new_details = course_scheduling.lab_filter.get_lab_filter_details(
		label,
		new_row.get("Title", ""),
		new_row.get("Attributes", ""),
	)

	lecture_token_added = (
		new_details["has_lec_token"] and not old_details["has_lec_token"]
	)
	lab_attribute_removed_from_lecture = (
		old_details["has_lab_attribute"]
		and not new_details["has_lab_attribute"]
		and new_details["has_lec_token"]
	)
	if lecture_token_added or lab_attribute_removed_from_lecture:
		return "lecture"

	lab_token_added = (
		new_details["has_lab_token"] and not old_details["has_lab_token"]
	)
	if lab_token_added and not new_details["has_lec_token"]:
		return "lab"

	if old_details["is_probable_lab"] != new_details["is_probable_lab"]:
		if new_details["is_probable_lab"]:
			return "lab"
		return "lecture"
	return None


#============================================
def describe_course_type_change(label: str, changed_fields: list,
		old_row: dict, new_row: dict) -> tuple[list, set]:
	"""
	Build a concise course-type description and name fields it replaces.

	Args:
		label: Normalized course-section label.
		changed_fields: Reportable snapshot columns that changed.
		old_row: Previous snapshot row.
		new_row: Current snapshot row.

	Returns:
		A tuple containing readable descriptions and fields already described.
	"""
	designation = detect_course_type_designation(label, old_row, new_row)
	if designation is None:
		return [], set()

	descriptions = [f"The section was assigned to be a {designation}"]
	consumed_fields = set()
	if "Title" in changed_fields:
		old_base = title_without_course_type(old_row.get("Title", ""))
		new_base = title_without_course_type(new_row.get("Title", ""))
		if old_base.lower() == new_base.lower():
			consumed_fields.add("Title")
	if "Attributes" in changed_fields:
		new_format = format_change_value(new_row.get("Attributes", ""))
		descriptions.append(f'The format is now "{new_format}"')
		consumed_fields.add("Attributes")
	return descriptions, consumed_fields


#============================================
def describe_change_count(count: int, action: str) -> str:
	"""
	Return a correctly pluralized subject-summary count.

	Args:
		count: Number of affected classes.
		action: Past-tense action shown after the class noun.

	Returns:
		A count phrase such as "1 class added".
	"""
	noun = "class" if count == 1 else "classes"
	description = f"{count} {noun} {action}"
	return description


#============================================
def build_change_summary(changed_subjects: list, change_details: dict) -> str:
	"""
	Build a human-readable summary of what changed across subjects.

	Args:
		changed_subjects: List of subject codes that changed.
		change_details: Dict keyed by subject with diff details from evaluate_subject_changes.

	Returns:
		Multi-line summary string suitable for email body.
	"""
	lines = []
	for subject in changed_subjects:
		details = change_details[subject]
		added = details["added"]
		removed = details["removed"]
		modified = details["modified"]
		full_events = details["full_events"]
		new_total = details["new_total"]
		label_titles = details["label_titles"]
		# Subject header with total class count
		parts = []
		if added:
			parts.append(describe_change_count(len(added), "added"))
		if removed:
			parts.append(describe_change_count(len(removed), "removed"))
		if modified:
			parts.append(describe_change_count(len(modified), "updated"))
		if full_events:
			parts.append(describe_change_count(len(full_events), "now full"))
		summary_text = ", ".join(parts) if parts else "changed"
		lines.append(f"{subject} ({new_total} classes): {summary_text}")
		# List specific added/removed classes, each named by its course title
		for label in added:
			added_line = f"  + {label} {format_display_title(label_titles[label])} was added."
			lines.append(added_line)
		for label in removed:
			# Removed classes take their title from the old cached snapshot,
			# which is still on disk when the diff runs.
			removed_line = f"  - {label} {format_display_title(label_titles[label])} was removed."
			lines.append(removed_line)
		# Show what changed for each modified class
		field_changes = details["field_changes"]
		for fc in field_changes:
			old_row = fc["old_row"]
			new_row = fc["new_row"]
			field_descriptions, consumed_fields = describe_course_type_change(
				fc["label"], fc["fields"], old_row, new_row
			)
			for field_name in fc["fields"]:
				if field_name in consumed_fields:
					continue
				description = describe_field_change(
					field_name,
					old_row.get(field_name, ""),
					new_row.get(field_name, ""),
				)
				field_descriptions.append(description)
			fields_str = ". ".join(field_descriptions) + "."
			# The displayed title is the current (new row) title, so the line
			# names the class as it stands now even when Title itself changed;
			# the old title still shows inside the field description.
			modified_title = format_display_title(label_titles[fc["label"]])
			modified_line = f"  ~ {fc['label']} {modified_title}: {fields_str}"
			lines.append(modified_line)
		# Show full-section events from the memory path. A capacity bump over a
		# previously remembered full capacity is annotated for the operator.
		for event in full_events:
			full_line = (
				f"  * {event['label']} {format_display_title(event['title'])} is now full "
				f"({event['enrolled']} of {event['capacity']} seats filled)."
			)
			if event["prev_capacity"] is not None:
				full_line += (
					" It was previously reported full at a capacity of "
					f"{event['prev_capacity']}."
				)
			lines.append(full_line)
	summary = "\n".join(lines)
	return summary
