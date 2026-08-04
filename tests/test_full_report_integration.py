"""
Report-path integration tests for the change_detect and change_summary seams.

These exercise the pure seam evaluate_subject_changes, which check_for_changes
also calls, so production and tests share one code path. They feed synthetic
rows (no Banner download, no file I/O) and cover:
 - first-run seeding: zero full events fire and the term key enters memory
 - same-cap refill: pure enrollment churn stays quiet
 - waitlist-only toggle on a tracked full section: quiet, no modified line,
    while a genuinely new full section still reports
 - the has_real_changes gate flipping for a new full event
"""

# local repo modules
import course_scheduling.change_detect
import course_scheduling.change_summary


#============================================
# helpers

def make_row(crn: str, enrolled: int, capacity: int, label: str = "BIOL 101",
		title: str = "Intro Bio", waitlisted: str = "0", campus: str = "Chicago") -> dict:
	"""
	Build a minimal parsed row dict for the report-path seam.

	Args:
		crn: Course reference number string.
		enrolled: Enrolled student count.
		capacity: Section capacity.
		label: Short course label (the diff key).
		title: Full course title.
		waitlisted: Waitlist count string (an enrollment-noise column).
		campus: A non-noise column used to force genuine "modified" diffs.

	Returns:
		A dict with the columns diff_rows and detect_full_events expect.
	"""
	enrolled_text = f"{enrolled} / {capacity}"
	row = {
		"CRN": crn,
		"Label": label,
		"Title": title,
		"Enrolled": enrolled_text,
		"Waitlisted": waitlisted,
		"Campus": campus,
	}
	return row


TERM = "202710"
CRN_A = "11111"
CRN_B = "22222"


#============================================
# first-run seeding

def test_first_run_seeds_memory_and_fires_no_full_events() -> None:
	"""First run seeds the term baseline silently: zero full events, term key added."""
	new_rows = [make_row(CRN_A, enrolled=30, capacity=30)]
	memory: dict = {}
	details, _has = course_scheduling.change_detect.evaluate_subject_changes(
		new_rows, old_rows=[], term_code=TERM, memory=memory, first_run=True
	)
	# the existing full backlog must not fire on the seeding run
	assert details["full_events"] == []
	# the term baseline now persists so later runs compare against it
	assert memory[TERM][CRN_A] == 30


#============================================
# same-cap refill stays quiet

def test_same_cap_refill_is_quiet() -> None:
	"""A seat opening then refilling at the remembered cap produces no meaningful change."""
	# remembered full at cap 30; cache showed a seat open, snapshot is full again
	memory = {TERM: {CRN_A: 30}}
	old_rows = [make_row(CRN_A, enrolled=29, capacity=30)]
	new_rows = [make_row(CRN_A, enrolled=30, capacity=30)]
	_details, has_real_changes = course_scheduling.change_detect.evaluate_subject_changes(
		new_rows, old_rows, term_code=TERM, memory=memory, first_run=False
	)
	assert has_real_changes is False


def test_parser_audit_field_change_is_quiet() -> None:
	"""A parser-reason change alone does not become an email course update."""
	memory: dict = {TERM: {}}
	old_row = make_row(CRN_A, enrolled=20, capacity=30)
	old_row["Lab_Reason"] = "lab_attribute"
	new_row = make_row(CRN_A, enrolled=20, capacity=30)
	new_row["Lab_Reason"] = "lab_token"
	_details, has_real_changes = course_scheduling.change_detect.evaluate_subject_changes(
		[new_row], [old_row], term_code=TERM, memory=memory, first_run=False
	)
	assert has_real_changes is False


#============================================
# waitlist-only toggle is quiet, genuine new full still reports

def test_waitlist_toggle_quiet_while_new_full_reports() -> None:
	"""A waitlist-only change on a tracked full section stays quiet; a new full section fires."""
	# CRN_A is already remembered full; CRN_B was open last cache
	memory = {TERM: {CRN_A: 30}}
	old_rows = [
		make_row(CRN_A, enrolled=30, capacity=30, label="BIOL 101", waitlisted="0"),
		make_row(CRN_B, enrolled=19, capacity=30, label="BIOL 201", waitlisted="0"),
	]
	new_rows = [
		# CRN_A: only the waitlist moved; still full at the same cap
		make_row(CRN_A, enrolled=30, capacity=30, label="BIOL 101", waitlisted="5"),
		# CRN_B: genuinely went full for the first time
		make_row(CRN_B, enrolled=30, capacity=30, label="BIOL 201", waitlisted="0"),
	]
	details, _has_real_changes = course_scheduling.change_detect.evaluate_subject_changes(
		new_rows, old_rows, term_code=TERM, memory=memory, first_run=False
	)
	summary = course_scheduling.change_summary.build_change_summary(
		["BIOL"], {"BIOL": details}
	)
	assert "BIOL 101" not in summary
	assert "BIOL 201" in summary


def test_gate_true_with_only_full_event() -> None:
	"""A new full event flips the gate True even with no added/removed/modified."""
	memory: dict = {TERM: {}}
	old_rows = [make_row(CRN_A, enrolled=29, capacity=30)]
	# the only meaningful movement is the section becoming full
	new_rows = [make_row(CRN_A, enrolled=30, capacity=30)]
	_details, has_real_changes = course_scheduling.change_detect.evaluate_subject_changes(
		new_rows, old_rows, term_code=TERM, memory=memory, first_run=False
	)
	assert has_real_changes is True
