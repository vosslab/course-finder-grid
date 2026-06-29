"""
CSV source loader: spreadsheet rows -> grid rows.

Reads a draft-schedule CSV with csv.DictReader, applies the FilterSpec, and
produces per-meeting grid rows. Blank cells read as empty strings; the former
DataFrame is-NA checks become explicit empty / numeric-parse checks so output
matches the previous DataFrame read path.
"""

# Standard Library
import csv
import datetime

# local repo modules
import course_scheduling.grid_model
import course_scheduling.course_label
import course_scheduling.course_filter
import course_scheduling.schedule_time

REQUIRED_COLUMNS = ('Meeting_Days', 'Begin_Time', 'End_Time')


#============================================

def _numeric_or_none(raw: str) -> float | None:
	"""
	Parse a CSV time cell to a float, returning None for blank or non-numeric.

	The draft CSV stores Begin_Time / End_Time as numeric values the prior
	DataFrame read as float64. Blank cells were NaN before; here they parse to None.

	Args:
		raw: Raw cell string from csv.DictReader.

	Returns:
		The float value, or None when the cell is blank or not numeric.
	"""
	if raw is None or raw == "":
		return None
	try:
		return float(raw)
	except ValueError:
		return None


#============================================

def _slot_from_value(value: float | None) -> datetime.time | None:
	"""
	Convert a numeric military-time value to a time slot.

	Mirrors the former DataFrame path, which passed str(float_cell) into
	time_to_slot (so 1400.0 -> "1400.0" -> 14:00). A None value reproduces the
	NaN path, which str() rendered as "nan" and parsed to None.

	Args:
		value: Numeric military time (for example 1400.0), or None.

	Returns:
		A datetime.time slot, or None when the value cannot be parsed.
	"""
	# str(None-as-NaN) was "nan" before; time_to_slot returns None for it.
	time_text = "nan" if value is None else str(value)
	slot = course_scheduling.schedule_time.time_to_slot(time_text)
	return slot


#============================================

def load_grid_rows(input_file: str, filter_spec: course_scheduling.course_filter.FilterSpec) -> list:
	"""
	Load grid rows from a draft-schedule CSV file.

	Args:
		input_file: Path to the CSV file with class data.
		filter_spec: Filter state controlling which courses are kept.

	Returns:
		List of grid row dicts with Label, Days, Start, End, Waitlisted,
		Enrollment_Ratio.

	Raises:
		ValueError: If a required column is missing from a non-empty CSV.
	"""
	class_data = []
	with open(input_file, "r", encoding="utf-8", newline="") as handle:
		reader = csv.DictReader(handle)
		# An empty file has no header row; csv.DictReader leaves fieldnames None.
		# Treat that as zero rows and a clean exit (was an empty-data error).
		if reader.fieldnames is None:
			print(f"Loaded 0 classes from {input_file}")
			return class_data

		# Ensure required fields are present before iterating rows.
		for column in REQUIRED_COLUMNS:
			if column not in reader.fieldnames:
				raise ValueError(f"Required column '{column}' not found in CSV file: {input_file}")

		for row in reader:
			# Skip if Begin_Time is blank or parses to less than 600.
			begin_value = _numeric_or_none(row['Begin_Time'])
			if begin_value is None or begin_value < 600:
				continue

			# Skip if Meeting_Days is blank or empty after stripping.
			days_text = row['Meeting_Days']
			if not days_text or not days_text.strip():
				continue
			# Convert string into a list of individual days.
			days = list(days_text.strip())

			# Validate and extract subject/course/section/label in one pass.
			# A row missing those fields raises ValueError and is skipped.
			try:
				subject, course_number, section_number, label = course_scheduling.grid_model.validate_and_extract_course(row)
			except ValueError:
				continue

			start_time = _slot_from_value(begin_value)
			end_time = _slot_from_value(_numeric_or_none(row['End_Time']))

			level = row.get('Level')
			campus = row.get('Campus_Desc')
			course_status = row.get('Course_Status')
			waitlisted = False

			if course_status != 'Active':
				continue

			if start_time is None or start_time == 0:
				continue

			if days is None or len(days) == 0:
				continue

			if subject is None:
				subject = label[:4]
			if course_number is None:
				course_number = course_scheduling.course_label.extract_course_number(label)

			if not course_scheduling.course_filter.should_include_class(filter_spec, label, subject, course_number, level, campus):
				continue

			label = label.replace(' ', '\n')
			# Add processed data and other extracted info
			processed_row = {
				"Label": label,
				"Days": days,
				"Start": start_time,
				"End": end_time,
				"Waitlisted": waitlisted,
				"Enrollment_Ratio": None,
			}
			class_data.append(processed_row)

	print(f"Loaded {len(class_data)} classes from {input_file}")
	return class_data
