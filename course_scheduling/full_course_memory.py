"""
Durable memory of which course sections have been reported full.

This module prevents false-positive "now full" emails. Each full section is
remembered by CRN per term, storing only the capacity at which it was last
reported full. A same-capacity refill stays silent, while a capacity increase
(for example 24 -> 36) re-fires a "now full" event.

The YAML memory is one combined file with a minimal mapping:

	term_code -> {crn -> capacity}

This module is standalone and owns enrollment parsing. It does not import
email_schedule_report to avoid a circular dependency.
"""

# Standard Library
import os
import re

# PIP3 modules
import yaml


#============================================
def parse_enrolled(enrolled_text: str) -> tuple:
	"""
	Parse the combined enrollment string into integer counts.

	This is the single home for the enrollment parse regex.

	Args:
		enrolled_text: String like "19 / 18" or "29 / 48".

	Returns:
		A (enrolled, capacity) tuple of ints, or (None, None) when the text
		does not contain a parseable "enrolled / capacity" pair.
	"""
	# match two integers separated by a slash, with optional surrounding space
	match = re.search(r'(\d+)\s*/\s*(\d+)', enrolled_text)
	if not match:
		return (None, None)
	enrolled = int(match.group(1))
	capacity = int(match.group(2))
	return (enrolled, capacity)


#============================================
def load_memory(memory_path: str) -> dict:
	"""
	Load the full-section memory from a YAML file.

	Args:
		memory_path: Path to the YAML memory file.

	Returns:
		The parsed memory mapping, or an empty dict when the file is absent.
	"""
	# a missing file means no sections have been reported full yet
	if not os.path.isfile(memory_path):
		return {}
	with open(memory_path, 'r') as file_handle:
		memory = yaml.safe_load(file_handle)
	# an empty YAML file parses to None; normalize to an empty dict
	if memory is None:
		return {}
	return memory


#============================================
def save_memory(memory_path: str, memory: dict) -> None:
	"""
	Write the full-section memory to a YAML file.

	Args:
		memory_path: Path to the YAML memory file.
		memory: The memory mapping to serialize.
	"""
	with open(memory_path, 'w') as file_handle:
		yaml.safe_dump(memory, file_handle, default_flow_style=False, sort_keys=True)


#============================================
def detect_full_events(rows: list, term_code: str, memory: dict) -> list:
	"""
	Find sections that should fire a "now full" event.

	A section fires when it is full now AND its CRN is new to the term, or its
	current capacity exceeds the remembered capacity. Each event carries fields
	for rendering only; the memory itself stores capacity alone.

	Args:
		rows: List of csv.DictReader-style row dicts. Each row must carry the
			keys "CRN", "Label", "Title", and "Enrolled".
		term_code: The term identifier, for example "202710".
		memory: The full-section memory mapping.

	Returns:
		A list of event dicts. Each event has the keys "crn", "label",
		"title", "enrolled", "capacity", and "prev_capacity" (None when the
		section is seen full for the first time).
	"""
	# remembered capacities for this term; absent term means nothing seen yet
	term_memory = memory.get(term_code, {})
	events = []
	for row in rows:
		enrolled_text = row["Enrolled"]
		enrolled, capacity = parse_enrolled(enrolled_text)
		# skip sections with unparseable enrollment or that are not full
		if enrolled is None:
			continue
		if enrolled < capacity:
			continue
		crn = row["CRN"]
		# a previously remembered capacity decides whether this re-fires
		prev_capacity = term_memory.get(crn, None)
		# new CRN fires; otherwise only a capacity increase fires
		if prev_capacity is not None and capacity <= prev_capacity:
			continue
		event = {
			"crn": crn,
			"label": row["Label"],
			"title": row["Title"],
			"enrolled": enrolled,
			"capacity": capacity,
			"prev_capacity": prev_capacity,
		}
		events.append(event)
	return events


#============================================
def record_full_events(memory: dict, term_code: str, events: list) -> None:
	"""
	Record fired events into the memory mapping.

	Only the capacity is stored, keyed by CRN under the term.

	Args:
		memory: The full-section memory mapping, modified in place.
		term_code: The term identifier, for example "202710".
		events: The events returned by detect_full_events.
	"""
	# create the term sub-mapping on first use
	if term_code not in memory:
		memory[term_code] = {}
	for event in events:
		crn = event["crn"]
		capacity = event["capacity"]
		memory[term_code][crn] = capacity


#============================================
def seed_full_sections(rows: list, term_code: str, memory: dict) -> None:
	"""
	Seed the memory with every currently-full section for first-run setup.

	This records capacities without firing any events, so that an initial run
	does not flood recipients with "now full" emails for the existing backlog.

	Args:
		rows: List of csv.DictReader-style row dicts. Each row must carry the
			keys "CRN" and "Enrolled".
		term_code: The term identifier, for example "202710".
		memory: The full-section memory mapping, modified in place.
	"""
	# create the term sub-mapping on first use
	if term_code not in memory:
		memory[term_code] = {}
	for row in rows:
		enrolled_text = row["Enrolled"]
		enrolled, capacity = parse_enrolled(enrolled_text)
		# skip sections with unparseable enrollment or that are not full
		if enrolled is None:
			continue
		if enrolled < capacity:
			continue
		crn = row["CRN"]
		memory[term_code][crn] = capacity
