# Standard Library
import dataclasses

# local repo modules
import course_scheduling.course_label
import course_scheduling.lab_filter


#============================================

@dataclasses.dataclass
class FilterSpec:
	"""
	Filter state carried through the library, replacing the argparse Namespace.

	Fields mirror the filter flags parsed at the command layer:
		subjects: selected subject codes (e.g. ["BIOL", "CHEM"]) or None.
		campus: selected campus names (e.g. ["CHICAGO CAMPUS"]) or None.
		levels: selected levels ("U", "G") or None.
		number: selected course-number series (100, 200, 300, 400) or None.
		lab_only: keep only likely lab sections when True.
	"""
	subjects: list[str] | None = None
	campus: list[str] | None = None
	levels: list[str] | None = None
	number: list[int] | None = None
	lab_only: bool = False


#============================================

def evaluate_class_inclusion(
	filter_spec: FilterSpec,
	label: str | None,
	subject: str | None,
	course_number: object,
	level: str | None,
	campus: str | None,
	course_text: str | None = None,
	attributes_text: str | None = None,
) -> tuple:
	"""
	Evaluate whether a class passes all active filters and return reason metadata.
	"""
	if subject is None and label:
		subject = label[:4]
	if course_number is None and label:
		course_number = course_scheduling.course_label.extract_course_number(label)

	# Filter by subject (if subjects are provided)
	if subject and filter_spec.subjects and subject not in filter_spec.subjects:
		return False, "subject_filter"

	course_integer = None
	if course_number is not None:
		try:
			course_integer = int(course_number)
		except ValueError:
			return False, "invalid_course_number"

		# Filter by level: if it's a graduate class but the course number is below 400, skip it
		if course_integer < 400 and level == "G":
			return False, "grad_level_number_mismatch"

		# Filter by level: if it's a undergraduate class but the course number is above 400, skip it
		if course_integer > 399 and level == "U":
			return False, "undergrad_level_number_mismatch"

		# Filter by series number (100, 200, 300, 400)
		if filter_spec.number and course_integer // 100 * 100 not in filter_spec.number:
			return False, "number_filter"

	# Filter by level (if provided, and if the row doesn't match any level)
	if level and filter_spec.levels and level not in filter_spec.levels:
		return False, "level_filter"

	# Filter by campus (if provided)
	if campus and filter_spec.campus and campus not in filter_spec.campus:
		return False, "campus_filter"

	if filter_spec.lab_only:
		lab_filter_details = course_scheduling.lab_filter.get_lab_filter_details(label, course_text, attributes_text=attributes_text)
		if not lab_filter_details["is_probable_lab"]:
			return False, f"lab_filter:{lab_filter_details['reason']}"

	return True, "included"


#============================================

def should_include_class(
	filter_spec: FilterSpec,
	label: str | None,
	subject: str | None,
	course_number: object,
	level: str | None,
	campus: str | None,
	course_text: str | None = None,
) -> bool:
	"""
	Return whether a class passes all active filters.

	Args:
		filter_spec: Active filter state.
		label: Course label string, or None.
		subject: Subject code, or None.
		course_number: Course number as int, str, or None.
		level: Level letter ("U" or "G"), or None.
		campus: Campus name, or None.
		course_text: Combined class and title text for lab matching.

	Returns:
		True when the class passes every active filter.
	"""
	include_row, exclusion_reason = evaluate_class_inclusion(
		filter_spec, label, subject, course_number, level, campus, course_text
	)
	return include_row
