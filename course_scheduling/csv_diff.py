"""CSV row loading and comparison helpers for schedule change detection."""

# Standard Library
import csv
import logging
import os


#============================================
def load_csv_rows(csv_path: str) -> list:
	"""
	Read a CSV file and return rows as a list of dicts.

	Args:
		csv_path: Path to the CSV file.

	Returns:
		List of row dicts, or empty list if file does not exist.
	"""
	if not os.path.isfile(csv_path):
		return []
	with open(csv_path, "r") as f:
		reader = csv.DictReader(f)
		rows = list(reader)
	return rows


#============================================
def compare_csv_files(new_csv: str, cached_csv: str) -> bool:
	"""
	Compare two CSV files by sorted line content.

	Args:
		new_csv: Path to newly generated CSV.
		cached_csv: Path to previously cached CSV.

	Returns:
		True if files differ (or cached file does not exist), False if identical.
	"""
	if not os.path.isfile(cached_csv):
		logging.info("No cached CSV found: %s", os.path.basename(cached_csv))
		return True
	with open(new_csv, "r") as f:
		new_lines = sorted(f.readlines())
	with open(cached_csv, "r") as f:
		old_lines = sorted(f.readlines())
	changed = new_lines != old_lines
	return changed


#============================================
def diff_rows(new_rows: list, old_rows: list) -> dict:
	"""
	Compare old and new row dicts by Label column, return summary of changes.

	This is the pure core of the diff: it takes already-loaded row lists and
	does no file or network I/O, so the report path stays unit-testable.

	Args:
		new_rows: Newly parsed row dicts (each carries a "Label" column).
		old_rows: Previously cached row dicts.

	Returns:
		Dict with keys: added, removed, modified (lists of label strings) and
		field_changes (detailed per-label field diffs). Full-section detection
		lives in full_course_memory.detect_full_events, not in this diff.
	"""
	# Index rows by Label for comparison
	old_by_label = {}
	for row in old_rows:
		label = row.get("Label", "")
		if label:
			old_by_label[label] = row
	new_by_label = {}
	for row in new_rows:
		label = row.get("Label", "")
		if label:
			new_by_label[label] = row
	old_labels = set(old_by_label.keys())
	new_labels = set(new_by_label.keys())
	added = sorted(new_labels - old_labels)
	removed = sorted(old_labels - new_labels)
	# Columns that change with every enrollment update (noise). A waitlist
	# forming or draining on an otherwise unchanged section stays quiet; full
	# events come from the memory path, not this byte-level diff.
	enrollment_noise_columns = {"Enrolled", "Enrollment_Ratio", "Waitlisted"}
	# Check for modified rows (same label but different content)
	modified = []
	field_changes = []
	for label in sorted(old_labels & new_labels):
		old_row = old_by_label[label]
		new_row = new_by_label[label]
		if old_row == new_row:
			continue
		# Find which columns actually changed
		all_keys = set(old_row.keys()) | set(new_row.keys())
		changed_cols = []
		for col in sorted(all_keys):
			if old_row.get(col, "") != new_row.get(col, ""):
				changed_cols.append(col)
		# Skip rows where only enrollment noise columns changed
		real_changes = [c for c in changed_cols if c not in enrollment_noise_columns]
		if not real_changes:
			continue
		modified.append(label)
		field_changes.append({
			"label": label,
			"fields": real_changes,
			"old_row": old_row,
			"new_row": new_row,
		})
	result = {
		"added": added,
		"removed": removed,
		"modified": modified,
		"field_changes": field_changes,
		"old_total": len(old_rows),
		"new_total": len(new_rows),
	}
	return result
