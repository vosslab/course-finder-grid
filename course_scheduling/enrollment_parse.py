"""
Enrollment text parsing for the Course Finder workflow.

Extracts the enrolled/capacity ratio from Banner "Enrolled" field text so the
grid renderer can flag near-full sections.
"""

# Standard Library
import re


#============================================

def parse_enrollment_ratio(enrolled_text: object) -> float | None:
	"""
	Parse an 'enrolled / capacity' string into a fill ratio.

	Args:
		enrolled_text: Raw enrollment text such as "18 / 24", or None.

	Returns:
		The enrolled/capacity ratio as a float, or None when the text is empty,
		unparseable, or has a non-positive capacity.
	"""
	if enrolled_text is None:
		return None
	text = str(enrolled_text).strip()
	if not text:
		return None
	match = re.search(r'(\d+)\s*/\s*(\d+)', text)
	if not match:
		return None
	enrolled = int(match.group(1))
	capacity = int(match.group(2))
	if capacity <= 0:
		return None
	return enrolled / capacity
