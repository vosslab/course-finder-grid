"""
CSV cache persistence for the schedule change-detection workflow.

Owns the on-disk cache directory: where the per-subject snapshot CSVs and
the durable full-section memory file live, when the cache was last refreshed,
and copying freshly parsed CSVs into the cache after a successful run.
"""

# Standard Library
import os
import shutil
import logging
import datetime

# Directory layout: the package holds code only; runtime cache state lives at
# the repo root under cache/ so course_scheduling/ stays code-only.
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PACKAGE_DIR)
CACHE_DIR = os.path.join(REPO_ROOT, "cache")
# Durable per-term "now full" memory file (see full_course_memory).
FULL_MEMORY_PATH = os.path.join(CACHE_DIR, "full_course_memory.yaml")


#============================================

def ensure_cache_dir() -> None:
	"""
	Create the cache directory if it does not already exist.
	"""
	os.makedirs(CACHE_DIR, exist_ok=True)


#============================================

def cache_path(subject: str, term_code: str) -> str:
	"""
	Build the cached snapshot CSV path for one subject and term.

	Args:
		subject: Subject code like BIOL.
		term_code: Banner term code.

	Returns:
		Absolute path to the cached CSV for this subject and term.
	"""
	path = os.path.join(CACHE_DIR, f"{subject}_{term_code}.csv")
	return path


#============================================

def get_last_run_date(term_code: str, subjects: list) -> datetime.date | None:
	"""
	Determine the date of the last successful run from CSV cache mtimes.

	Args:
		term_code: Banner term code.
		subjects: Subject codes whose cache files mark a successful run.

	Returns:
		Date of the most recently modified cache file, or None if no cache exists.
	"""
	if not os.path.isdir(CACHE_DIR):
		return None
	# Find the newest mtime among cached CSVs for this term
	latest_mtime = None
	for subject in subjects:
		path = cache_path(subject, term_code)
		if os.path.isfile(path):
			mtime = os.path.getmtime(path)
			if latest_mtime is None or mtime > latest_mtime:
				latest_mtime = mtime
	if latest_mtime is None:
		return None
	last_date = datetime.date.fromtimestamp(latest_mtime)
	return last_date


#============================================

def update_csv_cache(term_code: str, tmp_dir: str, changed_subjects: list) -> None:
	"""
	Copy new CSVs into the cache directory for changed subjects.

	Args:
		term_code: Banner term code.
		tmp_dir: Temporary directory holding the freshly parsed CSV files.
		changed_subjects: Subject codes whose cache should be refreshed.
	"""
	ensure_cache_dir()
	for subject in changed_subjects:
		src = os.path.join(tmp_dir, f"{subject}_{term_code}.csv")
		dst = cache_path(subject, term_code)
		shutil.copy2(src, dst)
		logging.info("Updated cache: %s", os.path.basename(dst))
