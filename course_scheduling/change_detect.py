"""
Per-subject change detection for the schedule report.

Holds the pure report-path seam (evaluate_subject_changes), shared by the
production path and the unit tests, plus check_for_changes, which downloads and
parses each subject in-process and compares it against the cached snapshot. The
download/parse/diff steps call the library directly; no sibling script is
shelled out to.
"""

# Standard Library
import os
import logging

# local repo modules
import course_scheduling.csv_diff
import course_scheduling.csv_cache
import course_scheduling.banner_http
import course_scheduling.banner_parser
import course_scheduling.course_filter
import course_scheduling.parser_audit_tables
import course_scheduling.full_course_memory


#============================================

def evaluate_subject_changes(new_rows: list, old_rows: list, term_code: str,
		memory: dict, first_run: bool) -> tuple:
	"""
	Pure report-path seam: diff rows, detect full events, gate on meaning.

	This shares one code path between production and tests. It does no
	download, parse, or file I/O. On the first run for a term it seeds the
	full-section memory from the current snapshot and fires no full events, so
	the existing backlog of full sections does not flood recipients. On later
	runs it asks course_scheduling.full_course_memory.detect_full_events which
	CRNs newly became full or jumped capacity.

	Args:
		new_rows: Freshly parsed row dicts for one subject.
		old_rows: Previously cached row dicts for the same subject.
		term_code: Banner term code, for example 202710.
		memory: Full-section memory mapping; mutated in place when seeding.
		first_run: True when this term has never been seen (seed, do not fire).

	Returns:
		Tuple of (details dict, has_real_changes bool). The details dict carries
		added/removed/modified/field_changes plus a "full_events" list.
	"""
	# Byte-level enrollment noise is already dropped inside diff_rows; here we
	# layer the snapshot-vs-memory full detection on top of that diff.
	details = course_scheduling.csv_diff.diff_rows(new_rows, old_rows)
	if first_run:
		# Seed the term baseline silently so the backlog does not fire events.
		course_scheduling.full_course_memory.seed_full_sections(new_rows, term_code, memory)
		full_events = []
	else:
		full_events = course_scheduling.full_course_memory.detect_full_events(new_rows, term_code, memory)
	details["full_events"] = full_events
	# A subject is meaningful when sections were added, removed, genuinely
	# modified, or newly went full; pure enrollment churn stays quiet.
	has_real_changes = any([
		details["added"],
		details["removed"],
		details["modified"],
		full_events,
	])
	return details, has_real_changes


#============================================

def download_and_parse_subject(term_code: str, subject: str, tmp_dir: str) -> str:
	"""
	Download one subject's HTML and write its raw parsed table to a CSV.

	Replaces the old download-then-parse subprocess chain with in-process calls:
	banner_http.download_subject writes the results HTML, banner_parser produces
	the raw audit rows with an unfiltered FilterSpec, and parser_audit_tables
	writes them to the per-subject snapshot CSV used for diffing.

	Args:
		term_code: Banner term code.
		subject: Subject code like BIOL.
		tmp_dir: Temporary directory for the HTML and CSV working files.

	Returns:
		Path to the freshly written snapshot CSV.
	"""
	html_path = os.path.join(tmp_dir, f"course_finder_{term_code}_{subject}.html")
	logging.info("Downloading %s HTML", subject)
	course_scheduling.banner_http.download_subject(term_code, subject, html_path)

	# The snapshot CSV is the unfiltered raw parse table, matching the prior
	# grid script run with no filter flags.
	unfiltered_spec = course_scheduling.course_filter.FilterSpec()
	logging.info("Parsing %s HTML to CSV", subject)
	_courses, raw_rows, _lab_debug_rows = course_scheduling.banner_parser.load_and_parse_class_data_from_file(
		html_path, unfiltered_spec
	)
	new_csv = os.path.join(tmp_dir, f"{subject}_{term_code}.csv")
	course_scheduling.parser_audit_tables.write_raw_table(raw_rows, new_csv)
	return new_csv


#============================================

def check_for_changes(term_code: str, subjects: list, tmp_dir: str, memory: dict) -> tuple:
	"""
	Download and parse each subject, compare against cache, detect full sections.

	Full-section "now full" events come from comparing the freshly parsed
	snapshot against the durable per-term memory (keyed by CRN), not from the
	byte-level CSV diff. On the first run for a term the memory is seeded from
	the current snapshot so the existing backlog of full sections does not fire.

	Args:
		term_code: Banner term code.
		subjects: Subject codes to download and compare.
		tmp_dir: Temporary directory for working files.
		memory: Full-section memory mapping, mutated in place when seeding.

	Returns:
		Tuple of (changed_subjects list, change_details dict keyed by subject,
		all_changed_subjects list).
	"""
	course_scheduling.csv_cache.ensure_cache_dir()
	changed_subjects = []
	all_changed_subjects = []
	change_details = {}
	# A missing term key means this term has never been seen: seed instead of
	# firing events. Captured before the loop so seeding mutating memory does
	# not flip the flag partway through the subjects.
	first_run = term_code not in memory
	if first_run:
		logging.info("First run for term %s: seeding full-section memory", term_code)
	# Track whether the feed exposed real CRNs distinct from the Label fallback.
	saw_any_rows = False
	saw_real_crn = False
	for subject in subjects:
		new_csv = download_and_parse_subject(term_code, subject, tmp_dir)
		cached_csv = course_scheduling.csv_cache.cache_path(subject, term_code)
		# Freshly parsed snapshot rows carry the "CRN" column.
		new_rows = course_scheduling.csv_diff.load_csv_rows(new_csv)
		for row in new_rows:
			saw_any_rows = True
			# The parser falls back to Label when the feed lacks a CRN dataLabel.
			if row["CRN"] != row["Label"]:
				saw_real_crn = True
		old_rows = course_scheduling.csv_diff.load_csv_rows(cached_csv)
		# Single seam shared with the unit tests: diff, seed-or-detect full
		# sections, and decide whether the change is meaningful. Called for
		# every subject so first-run seeding persists the term baseline even
		# when a subject shows no byte-level change.
		details, has_real_changes = evaluate_subject_changes(
			new_rows, old_rows, term_code, memory, first_run
		)
		if course_scheduling.csv_diff.compare_csv_files(new_csv, cached_csv):
			logging.info("CHANGED: %s", subject)
			all_changed_subjects.append(subject)
			if has_real_changes:
				changed_subjects.append(subject)
				change_details[subject] = details
				logging.info(
					"  meaningful added=%d removed=%d modified=%d full=%d",
					len(details["added"]),
					len(details["removed"]),
					len(details["modified"]),
					len(details["full_events"]),
				)
			else:
				logging.info("  byte-level change only; suppressing enrollment noise in email")
		else:
			logging.info("No change: %s", subject)
	# Surface the degraded-key state once when no real CRN was found at all.
	if saw_any_rows and not saw_real_crn:
		logging.info(
			"CRN dataLabel absent from feed; Label fallback active for term %s", term_code
		)
	return changed_subjects, change_details, all_changed_subjects
