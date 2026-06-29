"""
Low-level HTML parsing primitives for saved Course Finder (Banner) pages.

Provides day/time token normalization, dataLabel/dataValue lookup helpers,
meeting-block parsing, and campus inference.
"""

# Standard Library
import re
import datetime

# PIP3 modules
import lxml.html


DAY_TOKEN_RE = re.compile(r'\b(M|TU|T|W|TH|R|F|SA|SU|S)\b')
MEETING_RE = re.compile(r'(?P<days>(?:\b(?:M|TU|T|W|TH|R|F|SA|SU|S)\b\s*)+)\s+'
					r'(?P<start>\d{1,2}:\d{2}\s*[AP]M)\s*-\s*'
					r'(?P<end>\d{1,2}:\d{2}\s*[AP]M)'
					r'(?:\s*/\s*(?P<room>[A-Z]{2,4}\s*\d*))?')


#============================================

def normalize_day_token(token: str) -> str:
	"""
	Normalize a raw day abbreviation token to a canonical single character.

	Args:
		token: Raw day abbreviation, e.g. "TU", "TH", "SA".

	Returns:
		Canonical day code: M, T, W, R, F, or S.
	"""
	token = token.upper()
	if token in ("TU", "T"):
		return "T"
	if token in ("TH", "R"):
		return "R"
	if token in ("SA", "SU", "S"):
		return "S"
	return token


#============================================

def parse_html_time(time_text: str) -> datetime.time:
	"""
	Parse a 12-hour time string into a datetime.time object.

	Args:
		time_text: Time string like "10:30 AM".

	Returns:
		Parsed time object.
	"""
	cleaned = " ".join(time_text.split())
	return datetime.datetime.strptime(cleaned, "%I:%M %p").time()


#============================================

def normalize_label_text(text: str) -> str:
	"""
	Collapse internal whitespace and strip a label string.

	Args:
		text: Raw label text, possibly with multiple spaces or newlines.

	Returns:
		Cleaned single-line label text.
	"""
	return " ".join(text.split()).strip()


#============================================

def extract_text(value_element: lxml.html.HtmlElement | None) -> str:
	"""
	Extract and normalize the text content from an lxml element.

	Args:
		value_element: An lxml element, or None.

	Returns:
		Normalized text string, or empty string if element is None.
	"""
	if value_element is None:
		return ""
	return normalize_label_text(" ".join(value_element.itertext()))


#============================================

def find_data_value_element(course_box: lxml.html.HtmlElement, label_text: str) -> lxml.html.HtmlElement | None:
	"""
	Find the dataValue element paired with a given dataLabel in a course box.

	Args:
		course_box: The lxml element for one course result box.
		label_text: Exact text of the dataLabel to find.

	Returns:
		The first matching dataValue element, or None if not found.
	"""
	labels = course_box.xpath(".//div[contains(@class,'dataLabel')]")
	for label in labels:
		if normalize_label_text(label.text_content()) == label_text:
			parent = label.getparent()
			values = parent.xpath(".//div[contains(@class,'dataValue')]")
			if values:
				return values[0]
	return None


#============================================

def find_first_data_value_element(course_box: lxml.html.HtmlElement, label_text_options: list) -> lxml.html.HtmlElement | None:
	"""
	Return the first matching data value element for any label in label_text_options.

	Args:
		course_box: The lxml element for one course result box.
		label_text_options: List of dataLabel text strings to try in order.

	Returns:
		The first matching dataValue element, or None if none found.
	"""
	for label_text in label_text_options:
		value_element = find_data_value_element(course_box, label_text)
		if value_element is not None:
			return value_element
	return None


#============================================

def parse_meeting_blocks(when_text: str) -> list:
	"""
	Parse a When/Where text string into a list of meeting block dicts.

	Args:
		when_text: Raw When/Where text from a course box.

	Returns:
		List of dicts with keys Days, Start, End, Room.
	"""
	clean_text = " ".join(when_text.replace("\xa0", " ").split())
	meetings = []
	for match in MEETING_RE.finditer(clean_text):
		days_tokens = DAY_TOKEN_RE.findall(match.group("days"))
		days = []
		for token in days_tokens:
			day = normalize_day_token(token)
			if day not in days:
				days.append(day)
		start_time = parse_html_time(match.group("start"))
		end_time = parse_html_time(match.group("end"))
		if start_time and end_time and days:
			# Capture optional room/building after the time range
			room_text = match.group("room")
			if room_text:
				room_text = room_text.strip()
			meetings.append({
				"Days": days,
				"Start": start_time,
				"End": end_time,
				"Room": room_text or "",
			})
	return meetings


#============================================

def infer_campus_from_text(when_text: str) -> str | None:
	"""
	Infer campus from When/Where text based on known location keywords.

	Args:
		when_text: Raw When/Where text from a course box.

	Returns:
		Campus string, or None if the course is online or text is empty.
	"""
	if not when_text:
		return None
	upper_text = when_text.upper()
	if "ONLINE" in upper_text:
		return None
	if "SCH" in upper_text or "SCHAUMBURG" in upper_text:
		return "SCHAUMBURG CAMPUS"
	if "CHICAGO" in upper_text:
		return "CHICAGO CAMPUS"
	return "CHICAGO CAMPUS"
