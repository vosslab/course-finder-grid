"""
Deterministic pastel fill colors for schedule grid cells.

Maps course labels to stable hex colors using subject hues, course level for
lightness, and enrollment/waitlist state for emphasis. Colors are derived
deterministically so the same label always renders the same color.
"""

# Standard Library
import colorsys

# local repo modules
import course_scheduling.course_label


#============================================

# Hue, saturation, and lightness constants for course fill colors
WAITLISTED_HUE_DEGREES = 0
HIGH_FILL_HUE_DEGREES = 30
HIGH_FILL_THRESHOLD = 0.80
DEFAULT_SATURATION = 0.70
HIGH_FILL_SATURATION = 0.85
DEFAULT_LIGHTNESS = 0.88
LEVEL_LIGHTNESS = {
	1: 0.90,
	2: 0.85,
	3: 0.80,
	4: 0.75,
}
SUBJECT_HUES = {
	"BIOL": 120,
	"PHYS": 55,
	"CHEM": 210,
	"BCHM": 275,
}


#============================================

def hls_to_hex(hue_degrees: float, lightness: float, saturation: float) -> str:
	"""
	Convert HLS color components to a 6-digit hex string.

	Args:
		hue_degrees: Hue in degrees (wrapped modulo 360).
		lightness: Lightness from 0.0 to 1.0.
		saturation: Saturation from 0.0 to 1.0.

	Returns:
		Lowercase 'rrggbb' hex color string without a leading '#'.
	"""
	hue = (hue_degrees % 360) / 360.0
	rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
	rgb_255 = tuple(int(x * 255) for x in rgb)
	hex_color = f'{rgb_255[0]:02x}{rgb_255[1]:02x}{rgb_255[2]:02x}'
	return hex_color


#============================================

# string_to_anger is a deterministic base-26 hash of the label, used as a hue seed.
def string_to_anger(s: str) -> int:
	"""
	Encode a string as a deterministic base-26 integer hue seed.

	Args:
		s: Input string, typically a subject code.

	Returns:
		Integer where each uppercased letter contributes A=1..Z=26 in base 26.
	"""
	# Ensure the string is in uppercase for uniformity
	s = s.upper()

	# Initialize the result (anger value)
	anger_value = 0

	# Iterate over each letter in the string
	for char in s:
		# Convert the character to a number (A = 1, B = 2, ..., Z = 26)
		letter_value = ord(char) - ord('A') + 1

		# Treat this as a base-26 number, so shift the previous anger value and add the new letter value
		anger_value = anger_value * 26 + letter_value

	return anger_value


#============================================

def label_to_pastel_hex(label: str | None, waitlisted: bool = False, enrollment_ratio: float | None = None) -> str:
	"""
	Map a course label to a deterministic pastel hex color.

	Args:
		label: Course label string, or None.
		waitlisted: When True, render the waitlisted/closed hue.
		enrollment_ratio: Enrolled/capacity ratio used to flag near-full classes.

	Returns:
		Lowercase 'rrggbb' hex color string without a leading '#'.
	"""
	# Normalize newlines out of the label before parsing
	clean_label = course_scheduling.course_label.normalize_label_key(label)
	result = course_scheduling.course_label.split_course_label(clean_label)
	if result is not None:
		subject_code, course_number, section = result
	else:
		# Try merged label format (e.g. "BIOL 318/418-01/20")
		merged_result = course_scheduling.course_label.parse_merged_label(clean_label)
		if merged_result is not None:
			subject_code, course_number, section = merged_result
		else:
			parsed = course_scheduling.course_label.normalize_course_label(clean_label)
			subject_code = parsed[0]
			course_number = parsed[1]
			section = parsed[2]

	level = course_scheduling.course_label.course_number_to_level(course_number)
	if level is None:
		lightness = DEFAULT_LIGHTNESS
	else:
		lightness = LEVEL_LIGHTNESS.get(level, DEFAULT_LIGHTNESS)

	if waitlisted:
		return hls_to_hex(WAITLISTED_HUE_DEGREES, lightness, DEFAULT_SATURATION)

	if enrollment_ratio is not None and enrollment_ratio >= HIGH_FILL_THRESHOLD:
		return hls_to_hex(HIGH_FILL_HUE_DEGREES, lightness, HIGH_FILL_SATURATION)

	if subject_code in SUBJECT_HUES:
		return hls_to_hex(SUBJECT_HUES[subject_code], lightness, DEFAULT_SATURATION)

	# Fallback: keep distinct hues when subject is unknown.
	if course_number is None or not (100 <= course_number <= 499):
		return 'a0a0a0'

	modulated_number = (course_number * 37 * 7) % 160
	subject_code_auger = string_to_anger(subject_code) % 13 * 36
	section_number = course_scheduling.course_label.convert_section_number(section) % 10 * 3
	modulated_number = (modulated_number + subject_code_auger + section_number) % 360

	return hls_to_hex(modulated_number, lightness, DEFAULT_SATURATION)
