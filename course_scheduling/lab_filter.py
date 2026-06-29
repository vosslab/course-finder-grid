"""
Lab-section detection heuristic for course filtering.

Classifies whether a course section is a probable lab using label section
letters, LAB/LEC tokens in the class text, the HTML Attributes field, and a
small whitelist of lab-only courses.
"""

# Standard Library
import re

# local repo modules
import course_scheduling.course_label


#============================================

# Token regexes and whitelist used by the lab-detection heuristic
LAB_TOKEN_RE = re.compile(r'(^|[ -])LAB', re.IGNORECASE)
LEC_TOKEN_RE = re.compile(r'(^|[ -])LEC', re.IGNORECASE)
LAB_ONLY_COURSE_WHITELIST = {
	"BIOL 468",
}


#============================================

def get_lab_filter_details(label: str | None, course_text: str | None = None, attributes_text: str | None = None) -> dict:
	"""
	Return lab-filter decision details for debugging and reporting.

	Args:
		label: Course label string (e.g. "CHEM 201-20B").
		course_text: Combined class and title text for token matching.
		attributes_text: HTML "Attributes" field text (e.g. "Lab Course and Natural Science").

	Returns:
		Dict of lab-detection details, including is_probable_lab (bool), reason
		(str), section tokens, attribute flags, and the whitelist key.
	"""
	section = None
	whitelist_key = None
	normalized_label = course_scheduling.course_label.normalize_label_key(label)
	parsed_subject, parsed_course_number, parsed_section, parsed_label = course_scheduling.course_label.normalize_course_label(normalized_label)
	if parsed_label is not None:
		normalized_label = parsed_label
	if parsed_section is not None:
		section = parsed_section
	if parsed_subject is not None and parsed_course_number is not None:
		whitelist_key = f"{parsed_subject} {parsed_course_number}"

	section_is_lab = False
	if section:
		section_is_lab = section.upper().endswith("B")

	text_parts = [normalized_label]
	if course_text:
		text_parts.append(" ".join(str(course_text).split()))
	filter_text = " ".join(text_parts).upper()

	has_lab_token = bool(LAB_TOKEN_RE.search(filter_text))
	has_lec_token = bool(LEC_TOKEN_RE.search(filter_text))
	whitelist_lab_course = whitelist_key in LAB_ONLY_COURSE_WHITELIST

	# Check for "Lab Course" in the HTML Attributes field
	has_lab_attribute = False
	if attributes_text:
		has_lab_attribute = "lab course" in attributes_text.lower()

	is_probable_lab = False
	reason = "no_lab_indicator"
	if has_lec_token:
		is_probable_lab = False
		reason = "lec_token"
	elif whitelist_lab_course:
		is_probable_lab = True
		reason = "whitelist_course"
	elif has_lab_token:
		is_probable_lab = True
		reason = "lab_token"
	elif has_lab_attribute:
		is_probable_lab = True
		reason = "lab_attribute"
	elif section_is_lab:
		is_probable_lab = False
		reason = "section_b_only"

	potential_false_negative = section_is_lab and not has_lab_token and not has_lec_token

	lab_filter_details = {
		"whitelist_key": whitelist_key,
		"whitelist_lab_course": whitelist_lab_course,
		"section": section,
		"section_is_lab": section_is_lab,
		"has_lab_token": has_lab_token,
		"has_lec_token": has_lec_token,
		"has_lab_attribute": has_lab_attribute,
		"potential_false_negative": potential_false_negative,
		"is_probable_lab": is_probable_lab,
		"reason": reason,
	}
	return lab_filter_details
