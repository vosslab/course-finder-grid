"""
Unit tests for course_scheduling/course_scheduling.full_course_memory.py.

Covers the term -> {crn -> capacity} memory model:
 - YAML round-trip and missing-file behavior
 - New CRN full detection and memory recording
 - Refill suppression at the remembered capacity (core bug fix)
 - Capacity-bump re-firing
 - Below-capacity silence
 - Not-full section silence
 - Regression sequence: fill, same-cap refill (silent), capacity bump (fires)
"""

# Standard Library
import os

# local repo modules
import course_scheduling.full_course_memory


#============================================
# helpers

def make_row(crn: str, enrolled: int, capacity: int, label: str = "BIO 101", title: str = "Intro Bio") -> dict:
	"""
	Build a minimal csv.DictReader-style row for testing.

	Args:
		crn: The course reference number string.
		enrolled: Number of enrolled students.
		capacity: Section capacity.
		label: Short course label.
		title: Full course title.

	Returns:
		A dict with the keys detect_full_events expects.
	"""
	enrolled_text = f"{enrolled} / {capacity}"
	row = {
		"CRN": crn,
		"Label": label,
		"Title": title,
		"Enrolled": enrolled_text,
	}
	return row


TERM = "202710"
CRN_A = "11111"


#============================================
# YAML round-trip and missing file

def test_load_memory_missing_file_returns_empty(tmp_path: str) -> None:
	"""load_memory on a non-existent path returns an empty dict."""
	missing = os.path.join(tmp_path, "no_such_file.yaml")
	result = course_scheduling.full_course_memory.load_memory(missing)
	assert result == {}


def test_yaml_round_trip(tmp_path: str) -> None:
	"""save_memory then load_memory returns the same mapping."""
	memory_path = os.path.join(tmp_path, "memory.yaml")
	# build a mapping with two terms and two CRNs
	original = {
		TERM: {"22222": 30, "33333": 48},
		"202720": {"44444": 24},
	}
	course_scheduling.full_course_memory.save_memory(memory_path, original)
	loaded = course_scheduling.full_course_memory.load_memory(memory_path)
	assert loaded == original


#============================================
# new CRN that is full

def test_new_full_crn_fires_one_event_with_none_prev() -> None:
	"""A new full CRN produces exactly one event with prev_capacity None."""
	row = make_row(CRN_A, enrolled=30, capacity=30)
	events = course_scheduling.full_course_memory.detect_full_events([row], TERM, memory={})
	assert events[0]["prev_capacity"] is None


def test_record_full_events_stores_capacity() -> None:
	"""After record_full_events, memory[term][crn] equals the section capacity."""
	row = make_row(CRN_A, enrolled=30, capacity=30)
	memory: dict = {}
	events = course_scheduling.full_course_memory.detect_full_events([row], TERM, memory)
	course_scheduling.full_course_memory.record_full_events(memory, TERM, events)
	assert memory[TERM][CRN_A] == 30


#============================================
# refill suppression (core bug fix)

def test_same_capacity_refill_fires_no_event() -> None:
	"""A full CRN refilled to its remembered capacity produces zero events."""
	# pre-load memory with the known capacity
	memory = {TERM: {CRN_A: 30}}
	row = make_row(CRN_A, enrolled=30, capacity=30)
	events = course_scheduling.full_course_memory.detect_full_events([row], TERM, memory)
	assert events == []


#============================================
# capacity bump

def test_capacity_bump_fires_event_with_old_prev() -> None:
	"""A full CRN whose capacity exceeds the remembered value fires with the old capacity as prev."""
	memory = {TERM: {CRN_A: 30}}
	# capacity raised to 36 and section is now full again
	row = make_row(CRN_A, enrolled=36, capacity=36)
	events = course_scheduling.full_course_memory.detect_full_events([row], TERM, memory)
	assert events[0]["prev_capacity"] == 30


#============================================
# below remembered capacity

def test_below_remembered_capacity_fires_no_event() -> None:
	"""A full CRN at a capacity strictly below the remembered value produces zero events."""
	# remembered at 36; section now reports 30 capacity (drop in capacity)
	memory = {TERM: {CRN_A: 36}}
	row = make_row(CRN_A, enrolled=30, capacity=30)
	events = course_scheduling.full_course_memory.detect_full_events([row], TERM, memory)
	assert events == []


#============================================
# not-full section

def test_not_full_section_fires_no_event() -> None:
	"""A section with empty seats produces zero events regardless of memory."""
	row = make_row(CRN_A, enrolled=19, capacity=30)
	events = course_scheduling.full_course_memory.detect_full_events([row], TERM, memory={})
	assert events == []


#============================================
# regression sequence

def test_regression_sequence_fill_refill_bump() -> None:
	"""
	Guards the exact false-positive bug: fill fires, same-cap refill is silent,
	capacity-bump fires.

	Sequence on one CRN:
	 1. Section full at cap 30 -> event fires; memory records 30.
	 2. Seat opens then refills to same cap 30 -> no event.
	 3. Capacity raised to 36, section full again -> event fires with prev_capacity 30.
	"""
	memory: dict = {}

	# step 1: initial fill
	row_full = make_row(CRN_A, enrolled=30, capacity=30)
	events_1 = course_scheduling.full_course_memory.detect_full_events([row_full], TERM, memory)
	course_scheduling.full_course_memory.record_full_events(memory, TERM, events_1)

	# step 2: drop a seat then refill at the same cap -- must stay silent
	row_refill = make_row(CRN_A, enrolled=30, capacity=30)
	events_2 = course_scheduling.full_course_memory.detect_full_events([row_refill], TERM, memory)
	assert events_2 == []

	# step 3: capacity raised to 36, section full again -- must fire
	row_bump = make_row(CRN_A, enrolled=36, capacity=36)
	events_3 = course_scheduling.full_course_memory.detect_full_events([row_bump], TERM, memory)
	assert events_3[0]["prev_capacity"] == 30
