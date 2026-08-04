"""
Tests that every per-class report line names its course.

These drive the real report seam (evaluate_subject_changes into
build_change_summary) with synthetic rows, so they cover the label_titles
hand-off from the diff as well as the rendering.
"""

# local repo modules
import course_scheduling.change_detect
import course_scheduling.change_summary

TERM = "202710"


#============================================
# helpers

def make_row(crn: str, label: str, title: str, enrolled: int, capacity: int,
		campus: str = "Chicago", attributes: str = "") -> dict:
	"""
	Build a minimal parsed row dict for the report seam.

	Args:
		crn: Course reference number string.
		label: Short course label (the diff key).
		title: Full course title as Banner supplies it.
		enrolled: Enrolled student count.
		capacity: Section capacity.
		campus: A non-noise column used to force genuine "modified" diffs.
		attributes: Banner course-format attributes.

	Returns:
		A dict with the columns diff_rows and detect_full_events expect.
	"""
	row = {
		"CRN": crn,
		"Label": label,
		"Title": title,
		"Enrolled": f"{enrolled} / {capacity}",
		"Waitlisted": "0",
		"Campus": campus,
		"Attributes": attributes,
	}
	return row


def summarize(new_rows: list, old_rows: list, memory: dict) -> str:
	"""
	Run the report seam end to end and return the summary text.

	Args:
		new_rows: Freshly parsed row dicts.
		old_rows: Previously cached row dicts.
		memory: Full-section memory mapping; mutated in place.

	Returns:
		The rendered multi-line change summary.
	"""
	details, _has = course_scheduling.change_detect.evaluate_subject_changes(
		new_rows, old_rows, term_code=TERM, memory=memory, first_run=False
	)
	summary = course_scheduling.change_summary.build_change_summary(
		["BCHM"], {"BCHM": details}
	)
	return summary


#============================================
# rendered lines name the course

def test_added_and_removed_lines_show_titles() -> None:
	"""Both the + and - lines name the course and describe the event."""
	memory: dict = {TERM: {}}
	old_rows = [make_row("11111", "BCHM 430-98", "BIOCHEMISTRY LAB", 10, 20)]
	new_rows = [make_row("22222", "BCHM 430-20", "BIOCHEMISTRY LAB", 10, 20)]
	summary = summarize(new_rows, old_rows, memory)
	assert "+ BCHM 430-20 Biochemistry Lab was added." in summary
	assert "- BCHM 430-98 Biochemistry Lab was removed." in summary


def test_modified_line_shows_the_current_title() -> None:
	"""The ~ line names the class and describes its title change in prose."""
	memory: dict = {TERM: {}}
	old_rows = [make_row("11111", "BCHM 430-20", "OLD NAME", 10, 20)]
	new_rows = [make_row("11111", "BCHM 430-20", "NEW NAME", 10, 20)]
	summary = summarize(new_rows, old_rows, memory)
	assert "~ BCHM 430-20 New Name" in summary
	assert 'The title changed from "Old Name" to "New Name".' in summary


def test_lab_title_assignment_is_summarized() -> None:
	"""Adding LAB to a title becomes one readable lab-assignment sentence."""
	memory: dict = {TERM: {}}
	old_rows = [make_row(
		"15574", "BCHM 123-04B", "ANATOMY & PHYSIOLOGY I", 29, 30,
		attributes="Face to Face and Lab Course and Natural Science",
	)]
	new_rows = [make_row(
		"15574", "BCHM 123-04B", "ANATOMY & PHYSIOLOGY I- LAB", 29, 30,
		attributes="Face to Face and Lab Course and Natural Science",
	)]
	summary = summarize(new_rows, old_rows, memory)
	assert "The section was assigned to be a lab." in summary


def test_lecture_attribute_correction_is_summarized() -> None:
	"""Removing a conflicting Lab Course attribute becomes readable prose."""
	memory: dict = {TERM: {}}
	old_rows = [make_row(
		"14987", "BCHM 123-98", "ANATOMY & PHYSIOLOGY I-LECT", 29, 30,
		attributes="Lab Course and Natural Science",
	)]
	new_rows = [make_row(
		"14987", "BCHM 123-98", "ANATOMY & PHYSIOLOGY I-LECT", 29, 30,
		attributes="Natural Science and Online",
	)]
	summary = summarize(new_rows, old_rows, memory)
	expected = (
		"The section was assigned to be a lecture. "
		'The format is now "Natural Science and Online".'
	)
	assert expected in summary


def test_full_line_title_is_title_cased() -> None:
	"""The * now-full line renders its title in readable case, not ALL CAPS."""
	memory: dict = {TERM: {}}
	old_rows = [make_row("11111", "BCHM 430-20", "ORGANIC CHEMISTRY II", 19, 20)]
	new_rows = [make_row("11111", "BCHM 430-20", "ORGANIC CHEMISTRY II", 20, 20)]
	summary = summarize(new_rows, old_rows, memory)
	assert "* BCHM 430-20 Organic Chemistry II" in summary


def test_blank_title_degrades_instead_of_failing() -> None:
	"""A class with no title still reports, marked blank."""
	memory: dict = {TERM: {}}
	new_rows = [make_row("22222", "BCHM 430-20", "", 10, 20)]
	summary = summarize(new_rows, old_rows=[], memory=memory)
	assert "+ BCHM 430-20 (blank) was added." in summary
