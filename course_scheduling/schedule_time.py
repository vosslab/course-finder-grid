"""
Time-block helpers for the schedule grid.

Provides common-hour conflict checks, official provost time-block validation,
military-time conversion, and 15-minute rounding used when placing classes.
"""

# Standard Library
import datetime


#============================================

# Common hour: Tuesday/Thursday 12:20pm - 1:20pm
COMMON_HOUR_START = datetime.datetime.strptime("12:20", "%H:%M").time()
COMMON_HOUR_END = datetime.datetime.strptime("13:20", "%H:%M").time()

# Provost-assigned official start times by day (military HHMM)
OFFICIAL_TIME_BLOCKS = {
	"M": {800, 930, 1100, 1230, 1400, 1530, 1630, 1800},
	"W": {800, 930, 1100, 1230, 1400, 1530, 1630, 1800},
	"T": {800, 930, 1100, 1215, 1330, 1530, 1630, 1800},
	"R": {800, 930, 1100, 1215, 1330, 1530, 1630, 1800},
	"F": {930, 1230, 1530, 1800},
	"S": {930, 1230},
}


#============================================

def is_common_hour_conflict(days: list, start_time: datetime.time, end_time: datetime.time) -> bool:
	"""
	Check if a meeting overlaps the T/R common hour but is not fully contained in it.

	Args:
		days: List of normalized day tokens (e.g. ["T", "R"]).
		start_time: datetime.time for meeting start.
		end_time: datetime.time for meeting end.

	Returns:
		True if the meeting partially overlaps the common hour on T or R.
	"""
	# Must include Tuesday or Thursday
	has_tr = any(d in ("T", "R") for d in days)
	if not has_tr:
		return False
	# Check overlap: start < common_end AND end > common_start
	if start_time >= COMMON_HOUR_END or end_time <= COMMON_HOUR_START:
		return False
	# Fully contained is OK (not a conflict)
	if start_time >= COMMON_HOUR_START and end_time <= COMMON_HOUR_END:
		return False
	return True


#============================================

def time_to_military(t: datetime.time) -> int:
	"""
	Convert a datetime.time object to military-style integer (e.g. 13:30 -> 1330).

	Args:
		t: A datetime.time object.

	Returns:
		Integer in HHMM format.
	"""
	military = t.hour * 100 + t.minute
	return military


#============================================

def is_official_time_block(days: list, start_time: datetime.time) -> bool:
	"""
	Check if a meeting starts on an official provost-assigned time block.

	Args:
		days: List of normalized day tokens.
		start_time: datetime.time for meeting start.

	Returns:
		True if the start time is an official block for all days in the meeting.
	"""
	if not days or start_time is None:
		return True
	military = time_to_military(start_time)
	for day in days:
		allowed = OFFICIAL_TIME_BLOCKS.get(day)
		if allowed is None:
			# Unknown day, skip check
			continue
		if military not in allowed:
			return False
	return True


#============================================

def time_to_slot(time_str: str) -> datetime.time | None:
	"""
	Convert time string in military format without colons (e.g., '1000' or '1800') to a time object.

	Args:
		time_str: Time in string format like '1000' for 10:00 AM or '1800' for 6:00 PM.

	Returns:
		A datetime.time object, or None if the string cannot be parsed.
	"""
	if time_str.endswith('.0'):
		time_str = time_str[:-2]
	if len(time_str) < 3:
		return None
	try:
		# Convert military time string (e.g., '1000') to a time object
		return datetime.datetime.strptime(time_str, '%H%M').time()
	except ValueError:
		return None


#============================================

def round_down_to_nearest_15(dt: datetime.datetime) -> datetime.datetime:
	"""
	Round down the given datetime object to the nearest 15-minute interval.

	Args:
		dt: The datetime object to be rounded.

	Returns:
		The rounded datetime object.
	"""
	# Find how many minutes past the last 15-minute mark we are
	minutes = dt.minute % 15
	# Subtract the extra minutes to round down
	if minutes == 0:
		return dt
	rounded_dt = dt - datetime.timedelta(minutes=minutes)
	return rounded_dt
