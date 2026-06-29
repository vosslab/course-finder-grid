"""Human-readable change summary builders for schedule diff reports."""

# local repo modules
import course_scheduling.html_tokens

# Display labels for columns shown in change summaries
COLUMN_DISPLAY_NAMES = {
	"Title": "title",
	"Attributes": "format",
	"Campus": "campus",
	"Cross_Listed_With": "cross-listing",
	"Level": "level",
}


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
def describe_when_where_changes(old_when: str, new_when: str) -> str:
	"""
	Describe compact schedule/location changes from When_Where text.
	"""
	old_blocks = course_scheduling.html_tokens.parse_meeting_blocks(old_when)
	new_blocks = course_scheduling.html_tokens.parse_meeting_blocks(new_when)
	if not old_blocks or not new_blocks:
		return (
			f"schedule: {format_change_value(old_when)}->"
			f"{format_change_value(new_when)}"
		)

	old_first = old_blocks[0]
	new_first = new_blocks[0]
	descriptions = []

	old_days = "".join(old_first["Days"])
	new_days = "".join(new_first["Days"])
	if old_days != new_days:
		descriptions.append(f"day {old_days}->{new_days}")

	old_time = (
		f"{old_first['Start'].strftime('%I:%M%p').lstrip('0')}-"
		f"{old_first['End'].strftime('%I:%M%p').lstrip('0')}"
	)
	new_time = (
		f"{new_first['Start'].strftime('%I:%M%p').lstrip('0')}-"
		f"{new_first['End'].strftime('%I:%M%p').lstrip('0')}"
	)
	if old_time != new_time:
		descriptions.append(f"time {old_time}->{new_time}")

	old_room = format_change_value(old_first.get("Room", ""))
	new_room = format_change_value(new_first.get("Room", ""))
	if old_room != new_room:
		descriptions.append(f"room {old_room}->{new_room}")

	if len(old_blocks) != len(new_blocks):
		descriptions.append(f"meetings {len(old_blocks)}->{len(new_blocks)}")

	if not descriptions:
		return (
			f"schedule: {format_change_value(old_when)}->"
			f"{format_change_value(new_when)}"
		)
	return ", ".join(descriptions)


#============================================
def describe_field_change(column_name: str, old_value: str, new_value: str) -> str:
	"""
	Describe a changed CSV field using compact old->new output.
	"""
	if column_name == "When_Where":
		return describe_when_where_changes(old_value, new_value)

	label = COLUMN_DISPLAY_NAMES.get(column_name)
	if label is None:
		label = column_name.replace("_", " ").lower()
	old_text = format_change_value(old_value)
	new_text = format_change_value(new_value)
	description = f"{label}: {old_text}->{new_text}"
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
		# Subject header with total class count
		parts = []
		if added:
			parts.append(f"{len(added)} added")
		if removed:
			parts.append(f"{len(removed)} removed")
		if modified:
			parts.append(f"{len(modified)} modified")
		if full_events:
			parts.append(f"{len(full_events)} now full")
		summary_text = ", ".join(parts) if parts else "changed"
		lines.append(f"{subject} ({new_total} classes): {summary_text}")
		# List specific added/removed classes
		for label in added:
			lines.append(f"  + {label}")
		for label in removed:
			lines.append(f"  - {label}")
		# Show what changed for each modified class
		field_changes = details["field_changes"]
		for fc in field_changes:
			old_row = fc["old_row"]
			new_row = fc["new_row"]
			field_descriptions = []
			for field_name in fc["fields"]:
				description = describe_field_change(
					field_name,
					old_row.get(field_name, ""),
					new_row.get(field_name, ""),
				)
				field_descriptions.append(description)
			fields_str = ", ".join(field_descriptions)
			lines.append(f"  ~ {fc['label']}: {fields_str}")
		# Show full-section events from the memory path. A capacity bump over a
		# previously remembered full capacity is annotated for the operator.
		for event in full_events:
			full_line = (
				f"  * {event['label']} {event['title']}  "
				f"FULL {event['enrolled']}/{event['capacity']}"
			)
			if event["prev_capacity"] is not None:
				full_line += f"  (was full at {event['prev_capacity']})"
			lines.append(full_line)
	summary = "\n".join(lines)
	return summary
