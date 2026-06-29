"""
Pure in-memory schedule grid model and column/placement math.

Builds the day/time-slot grid data structure and computes where each class
lands. Holds no openpyxl or rendering logic; xlsx_writer consumes this model
to produce the spreadsheet.
"""

# Standard Library
import datetime
import collections.abc

# local repo modules
import course_scheduling.course_label
import course_scheduling.schedule_time


#============================================

# Grid spans 07:00 through 23:45 in 15-minute steps (68 slots).
GRID_START_TIME = datetime.datetime.strptime("07:00", "%H:%M").time()
GRID_END_TIME = datetime.datetime.strptime("23:45", "%H:%M").time()


#============================================

def generate_time_slots() -> list:
	"""
	Generate the grid's 15-minute time-slot labels from 07:00 to 23:45.

	Returns:
		List of 'HH:MM' strings, one per 15-minute slot (inclusive of both ends).
	"""
	# Walk from the grid start to the grid end in 15-minute steps
	slots = []
	current = datetime.datetime.combine(datetime.date.today(), GRID_START_TIME)
	end = datetime.datetime.combine(datetime.date.today(), GRID_END_TIME)
	while current <= end:
		slots.append(current.strftime("%H:%M"))
		current += datetime.timedelta(minutes=15)
	return slots


#============================================

def validate_and_extract_course(row: collections.abc.Mapping) -> tuple:
	"""
	Validates course information and extracts subject, course number, and section.
	If `SUBJ_CRSE_SEC` is available but individual fields are missing, attempts to split it.

	Args:
		row (Mapping): A mapping of column name to value (dict or Series-like row).

	Returns:
		tuple: (subject, course_number, section, label)

	Raises:
		ValueError: If required fields are missing and cannot be derived.
	"""

	label = row.get('SUBJ_CRSE_SEC')
	subject = row.get('SUBJ')
	course_number = row.get('CRSE')
	section_number = row.get('SEC')

	# Try to fill missing values from label
	if label and not (subject and course_number and section_number):
		subject, course_number, section_number = course_scheduling.course_label.split_course_label(label)

	# Final validation: All three must be present
	if not (subject and course_number and section_number):
		error_details = {
			'SUBJ_CRSE_SEC': label,
			'SUBJ': subject,
			'CRSE': course_number,
			'SEC': section_number,
		}
		raise ValueError(f"Missing required fields for row: {error_details}")

	# Ensure we always have a label
	if label is None:
		label = f"{subject} {course_number}-{section_number}"

	return subject, course_number, section_number, label


#============================================

def populate_schedule_grid(parsed_classes: list) -> dict:
	"""
	Populate the schedule grid with class labels.

	Args:
		parsed_classes: List of parsed class dictionaries.

	Returns:
		Updated schedule grid as a dictionary with days and times as keys.
	"""
	# Initialize an empty grid with all days and time slots populated
	schedule_grid = {}
	days_of_week = ["M", "T", "W", "R", "F", "S"]
	time_range = generate_time_slots()

	# Create an empty list for each day and each time slot
	for day in days_of_week:
		schedule_grid[day] = {}
		for time_str in time_range:
			schedule_grid[day][time_str] = []  # Initialize an empty list for each time slot

	# Populate the grid with class information
	for class_info in parsed_classes:
		label = class_info["Label"]
		days = class_info["Days"]
		start_time = class_info["Start"]
		end_time = class_info["End"]

		# Convert times to datetime objects for stepping in 15-minute intervals
		start_datetime = datetime.datetime.combine(datetime.datetime.today(), start_time)
		end_datetime = datetime.datetime.combine(datetime.datetime.today(), end_time)

		# Loop through the days and time slots and append the class label to each corresponding time slot
		for day in days:
			# Round the start time down to the nearest 15-minute interval
			rounded_start_datetime = course_scheduling.schedule_time.round_down_to_nearest_15(start_datetime)
			rounded_end_datetime = end_datetime - datetime.timedelta(minutes=1)

			# Iterate over the time range in 15-minute intervals
			current_datetime = rounded_start_datetime
			while current_datetime <= rounded_end_datetime:
				time_str = current_datetime.strftime("%H:%M")  # Convert time to 'HH:MM' format

				# Append the class label to the corresponding time slot for this day
				schedule_grid[day][time_str].append(label)
				current_datetime += datetime.timedelta(minutes=15)

	return schedule_grid


#============================================

def time_slot_to_row_number(time_obj: datetime.time | str) -> int:
	"""
	Convert a time slot (e.g., '10:00') to the corresponding row number in the Excel sheet.
	First row (1) is reserved for labels, so time '07:00' corresponds to row 2.

	Args:
		time_obj: A time object (or string) in 'HH:MM' format (e.g., '10:00').

	Returns:
		The corresponding row number for the given time.
	"""
	# Define the start time (07:00 corresponds to row 2)
	base_time = datetime.datetime.strptime("07:00", "%H:%M").time()

	# If the input is a string, convert it to a time object
	if isinstance(time_obj, str):
		time_obj = datetime.datetime.strptime(time_obj, "%H:%M").time()

	# Calculate the difference in minutes between the given time and the base time
	diff_minutes = (datetime.datetime.combine(datetime.datetime.today(), time_obj) -
					datetime.datetime.combine(datetime.datetime.today(), base_time)).total_seconds() // 60

	# Calculate the row number: Each row represents 15 minutes, row 2 starts at 07:00
	row_number = int(diff_minutes // 15) + 2

	return row_number


#============================================

def find_available_column(filled_grid_status: dict, start_column: int, begin_row_number: int, end_row_number: int) -> int:
	"""
	Find the first available column in the grid within a given row range.

	Args:
		filled_grid_status (dict): Maps (row, column) to True when occupied.
		start_column (int): The column number to start searching from.
		begin_row_number (int): The starting row number of the range to check.
		end_row_number (int): The ending row number of the range to check.

	Returns:
		int: The first available column number that is free in the given row range.
	"""
	current_column = start_column

	# Continue checking columns until we find an available one
	while True:
		# Assume the column is empty unless we find evidence otherwise
		is_empty = True

		# Check each row in the column
		for row_number in range(begin_row_number, end_row_number + 1):
			if filled_grid_status[(row_number, current_column)] is True:
				is_empty = False
				break  # No need to check further rows in this column, move to the next column

		# If the column is empty, return it
		if is_empty:
			return current_column

		# Move to the next column
		current_column += 1


#============================================

def fill_the_status_grid(filled_grid_status: dict, begin_row_number: int, end_row_number: int, column_num: int) -> None:
	"""
	Mark a column's row range as occupied in the placement grid.

	Args:
		filled_grid_status: Maps (row, column) to True when occupied.
		begin_row_number: First row of the range to mark.
		end_row_number: Last row of the range to mark (inclusive).
		column_num: Column number being occupied.
	"""
	for row in range(begin_row_number, end_row_number+1):
		filled_grid_status[(row, column_num)] = True


#============================================

def compute_columns_info(schedule_grid: dict, start_column: int = 2) -> tuple:
	"""
	Compute both the columns_needed and starting_columns for each day based on the schedule_grid.

	Args:
		schedule_grid (dict): A dictionary where keys are days of the week, and values are dictionaries
			with time slots as keys and class labels as values.
		start_column (int): The column number to start from (defaults to 2, which corresponds to Excel column 'B').

	Returns:
		tuple: A tuple containing two dictionaries:
			- columns_needed: Number of columns needed per day.
			- starting_columns: Starting column for each day.
	"""
	days_of_week = list(schedule_grid.keys())  # Ensure order if needed

	# Step 1: Determine how many columns are needed for each day
	columns_needed = {day: 0 for day in days_of_week}
	for day in days_of_week:
		for time, label_list in schedule_grid[day].items():
			# Find the maximum number of overlapping labels for each time slot
			columns_needed[day] = max(len(label_list), columns_needed[day])
		columns_needed[day] += 2

	# Step 2: Compute the starting column for each day with incremental gaps
	starting_columns = {}
	current_column = start_column
	for day, num_columns in columns_needed.items():
		starting_columns[day] = current_column
		current_column += num_columns

	return columns_needed, starting_columns
