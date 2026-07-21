"""
End-to-end orchestration for one schedule report run.

Loads the durable full-section memory, detects per-subject changes, builds the
email text, generates the merged workbook in-process, sends the email (unless
dry-run), and persists the cache and memory. A single-shot command runs this
pipeline in-process; recurring loop fires start that command in a short-lived
subprocess before it runs the pipeline.
"""

# Standard Library
import os
import shutil
import logging
import datetime
import tempfile

# local repo modules
import course_scheduling.csv_cache
import course_scheduling.email_report
import course_scheduling.email_sender
import course_scheduling.change_detect
import course_scheduling.change_summary
import course_scheduling.workbook_builder
import course_scheduling.full_course_memory

# The package holds code only; runtime state (logs, generated grids) lives at
# the repo root so course_scheduling/ stays code-only.
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PACKAGE_DIR)


#============================================

def setup_logging() -> None:
	"""
	Configure logging to both stdout and a log file under the repo-root logs dir.
	"""
	log_dir = os.path.join(REPO_ROOT, "logs")
	os.makedirs(log_dir, exist_ok=True)
	log_file = os.path.join(log_dir, "email_schedule_report.log")
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s %(levelname)s %(message)s",
		handlers=[
			logging.StreamHandler(),
			logging.FileHandler(log_file, mode="a"),
		],
	)


#============================================

def prime_baseline(term_code: str, subjects: list) -> None:
	"""
	Fetch and persist a baseline without composing or sending an email.

	Args:
		term_code: Banner term code.
		subjects: Subject codes to fetch and cache.
	"""
	setup_logging()
	logging.info("=== Course Schedule Baseline Prime ===")
	memory = course_scheduling.full_course_memory.load_memory(
		course_scheduling.csv_cache.FULL_MEMORY_PATH
	)
	tmp_dir = tempfile.mkdtemp(prefix="course_schedule_")
	try:
		course_scheduling.change_detect.check_for_changes(term_code, subjects, tmp_dir, memory)
		course_scheduling.csv_cache.update_csv_cache(term_code, tmp_dir, subjects)
		course_scheduling.full_course_memory.save_memory(
			course_scheduling.csv_cache.FULL_MEMORY_PATH, memory
		)
		logging.info("baseline primed: %d subjects cached", len(subjects))
	finally:
		shutil.rmtree(tmp_dir, ignore_errors=True)


#============================================

def run_report(term_code: str, subjects: list, dry_run: bool) -> None:
	"""
	Run one schedule report end-to-end for a term and subject set.

	Args:
		term_code: Banner term code.
		subjects: Subject codes to check and grid across.
		dry_run: When True, detect changes and compose the email but neither
			generate the workbook nor send the email; memory stays untouched.
	"""
	setup_logging()
	logging.info("=== Course Schedule Report ===")
	logging.info("Term code: %s, Dry run: %s", term_code, dry_run)

	# Load durable full-section memory before parsing so first-run seeding and
	# snapshot-vs-memory detection both see the prior state.
	memory = course_scheduling.full_course_memory.load_memory(course_scheduling.csv_cache.FULL_MEMORY_PATH)

	# Create a temporary directory for downloads and parsed CSVs.
	tmp_dir = tempfile.mkdtemp(prefix="course_schedule_")

	changed_subjects, change_details, all_changed_subjects = course_scheduling.change_detect.check_for_changes(
		term_code, subjects, tmp_dir, memory
	)

	if not changed_subjects:
		if all_changed_subjects:
			course_scheduling.csv_cache.update_csv_cache(term_code, tmp_dir, all_changed_subjects)
		# Persist first-run seeding and the term key even with no email to send.
		# A dry run leaves the memory file untouched.
		if not dry_run:
			course_scheduling.full_course_memory.save_memory(course_scheduling.csv_cache.FULL_MEMORY_PATH, memory)
		logging.info("No meaningful changes detected.")
		shutil.rmtree(tmp_dir, ignore_errors=True)
		return

	logging.info("Changed subjects: %s", ", ".join(changed_subjects))
	change_summary_text = course_scheduling.change_summary.build_change_summary(changed_subjects, change_details)

	# Build email subject and body from today's date and the last run.
	today = datetime.date.today()
	email_subject = course_scheduling.email_report.build_email_subject(today)
	last_run = course_scheduling.csv_cache.get_last_run_date(term_code, subjects)
	email_body = course_scheduling.email_report.build_email_body(
		today, last_run, changed_subjects, len(subjects), change_summary_text
	)

	if dry_run:
		logging.info("Email subject: %s", email_subject)
		logging.info("Email body:\n%s", email_body)
		logging.info("Dry run: skipping report generation and email.")
		shutil.rmtree(tmp_dir, ignore_errors=True)
		return

	# Generate the xlsx report in-process via the workbook coordinator.
	# Generated grids land in the repo-root output/ dir, not in the package.
	output_dir = os.path.join(REPO_ROOT, "output")
	os.makedirs(output_dir, exist_ok=True)
	grid_configs = course_scheduling.workbook_builder.default_grid_configs(term_code, subjects, output_dir)
	xlsx_path = course_scheduling.workbook_builder.build_term_workbook(term_code, subjects, grid_configs, output_dir)
	email_body += f"\nAttached: {os.path.basename(xlsx_path)}\n"

	# Send email first; if this raises (for example no user session), cache stays untouched.
	course_scheduling.email_sender.send_email(
		course_scheduling.email_sender.RECIPIENTS, email_subject, email_body, xlsx_path
	)

	# Update cache ONLY after email sends successfully.
	course_scheduling.csv_cache.update_csv_cache(term_code, tmp_dir, all_changed_subjects)

	# Record fired full events and persist memory beside the cache update so the
	# same sections stay silent next run unless their capacity increases.
	fired_events = []
	for subject in changed_subjects:
		fired_events.extend(change_details[subject]["full_events"])
	course_scheduling.full_course_memory.record_full_events(memory, term_code, fired_events)
	course_scheduling.full_course_memory.save_memory(course_scheduling.csv_cache.FULL_MEMORY_PATH, memory)

	# Clean up temp directory.
	shutil.rmtree(tmp_dir, ignore_errors=True)
	logging.info("Done.")
