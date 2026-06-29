"""
Course-label parsing and normalization helpers.

Splits Banner course labels into subject, course number, and section parts,
normalizes label text and keys, derives level information, and encodes section
strings as sortable integers.
"""

# Standard Library
import re


#============================================

def split_course_label(label: str) -> tuple | None:
	"""
	Split a strict 'SUBJ NUM-SEC' label into its parts.

	Args:
		label: Course label like "BIOL 301-01D".

	Returns:
		Tuple of (subject_code, course_number, section), or None if no match.
	"""
	regex = r'^([A-Z]+)\s(\d+)-(\d+[A-Z]?)$'
	match = re.match(regex, label)
	if match:
		subject_code = match.group(1)  # First capture group: Subject code (e.g., BIOL)
		course_number = int(match.group(2))  # Second capture group: Course number (e.g., 301)
		section = match.group(3)        # Third capture group: Section number with optional letter (e.g., 01D or 24)
		return subject_code, course_number, section
	else:
		return None


#============================================

def extract_course_number(course_string: str) -> int | None:
	"""
	Extract the integer course number from a strict course label.

	Args:
		course_string: Course label like "BIOL 301-01D".

	Returns:
		The course number as an integer, or None if the label does not match.
	"""
	# split_course_label returns None on a non-matching label; guard before unpack
	result = split_course_label(course_string)
	if result is None:
		return None
	subject_code, course_number, section = result
	if course_number:
		# Convert the matched string to an integer
		return course_number
	print(f'error: {course_string}')
	return None  # Return None if no match is found


#============================================

def normalize_course_label(label: str | None) -> tuple:
	"""
	Normalize free-form label text into structured parts.

	Args:
		label: Raw label text that may contain extra whitespace, or None.

	Returns:
		Tuple of (subject, course_number, section, normalized_label); each
		structured field is None when the label does not match the pattern.
	"""
	if label is None:
		return None, None, None, None

	label_text = " ".join(label.split())
	match = re.search(r'([A-Z]{2,5})\s+(\d+)-(\d+[A-Z]?)', label_text)
	if not match:
		return None, None, None, label_text

	subject = match.group(1)
	course_number = int(match.group(2))
	section = match.group(3)
	normalized_label = f"{subject} {course_number}-{section}"
	return subject, course_number, section, normalized_label


#============================================

def normalize_label_key(label: str | None) -> str:
	"""
	Collapse a label into a single-spaced key for dict lookups.

	Args:
		label: Raw label text that may contain newlines, or None.

	Returns:
		The label with newlines and runs of whitespace collapsed to single
		spaces, or an empty string when label is None.
	"""
	if label is None:
		return ""
	return " ".join(label.replace("\n", " ").split()).strip()


#============================================

def course_number_to_level(course_number: object) -> int | None:
	"""
	Map a course number to a 1-4 level used for color lightness.

	Args:
		course_number: Course number as int, str, or None.

	Returns:
		The hundreds-level (1-4, capped at 4), or None when below 100 or
		unparseable.
	"""
	if course_number is None:
		return None
	try:
		course_integer = int(course_number)
	except ValueError:
		return None
	if course_integer < 100:
		return None
	level = course_integer // 100
	if level < 1:
		return None
	if level > 4:
		return 4
	return level


#============================================

def infer_level_from_course_number(course_number: object) -> str | None:
	"""
	Infer an undergraduate/graduate level letter from a course number.

	Args:
		course_number: Course number as int, str, or None.

	Returns:
		"G" for 400 and above, "U" below 400, or None when unparseable.
	"""
	if course_number is None:
		return None
	try:
		course_integer = int(course_number)
	except ValueError:
		return None
	if course_integer >= 400:
		return "G"
	return "U"


#============================================

def convert_section_number(section: str) -> int:
	"""
	Convert a section string into a sortable integer.

	Args:
		section: Section string like "01" or "20B".

	Returns:
		An integer combining the numeric and letter parts so sections sort
		consistently.
	"""
	# Separate the numeric part from the letter (if present)
	numeric_part = ''
	letter_part = ''

	for char in section:
		if char.isdigit():
			numeric_part += char
		elif char.isalpha():
			letter_part += char

	# Convert numeric part to an integer
	if numeric_part:
		number = int(numeric_part)
	else:
		number = 0

	# If there's a letter part, encode it as a base-26 value (A=1, B=2, ..., Z=26)
	if letter_part:
		letter_value = ord(letter_part.upper()) - ord('A') + 1
		# Combine the numeric part with the letter's value in a consistent way
		# Example: multiply the numeric part by 100 and add the letter's value
		result = number * 100 + letter_value
	else:
		# If no letter, return the numeric part as is
		result = number

	return result


#============================================

def parse_merged_label(label: str) -> tuple:
	"""
	Parse both regular and slash-format merged course labels.

	Args:
		label: Course label like "BIOL 318-01" or "BIOL 318/418-01/20".

	Returns:
		Tuple of (subject, course_number, section) using the lowest course
		number and first section, or None if parsing fails.
	"""
	# Try regular format first
	result = split_course_label(label)
	if result is not None:
		return result
	# Try merged slash format: SUBJ NUM/NUM-SEC/SEC
	merged_re = r'^([A-Z]+)\s+(\d+(?:/\d+)*)-(\d+[A-Z]?(?:/\d+[A-Z]?)*)$'
	match = re.match(merged_re, label)
	if match:
		subject_code = match.group(1)
		# Take the lowest (first) course number
		course_number = int(match.group(2).split('/')[0])
		# Take the first section
		section = match.group(3).split('/')[0]
		return subject_code, course_number, section
	return None
