"""
Term workbook coordinator: download -> parse -> grid -> write -> merge.

A thin coordinator for one term across one set of subjects. It downloads each
subject's HTML once, then for each grid configuration filters and expands the
parsed records into a schedule grid, writes the grid plus its analysis tables,
and merges every grid into a single tabbed workbook. The grid and rendering
logic itself lives in grid_model and xlsx_writer; this module only sequences
the calls. The default preset matrix of grid configurations lives here so the
command layer supplies only the term and subject list.
"""

# Standard Library
import os
import glob
import shutil
import datetime
import dataclasses

# local repo modules
import course_scheduling.term_code
import course_scheduling.xlsx_merge
import course_scheduling.grid_model
import course_scheduling.xlsx_writer
import course_scheduling.banner_http
import course_scheduling.html_courses
import course_scheduling.course_filter
import course_scheduling.parser_audit_tables
import course_scheduling.schedule_analysis_tables


#============================================

@dataclasses.dataclass
class GridConfig:
	"""
	One grid tab in the term workbook.

	Fields:
		output_file: Path for the grid xlsx, or None for a raw-table-only run.
		filter_spec: Filter state selecting which courses land on this grid.
		raw_table_output: Optional path for the raw parsed table.
		raw_table_only: When True, write only the raw table and skip the grid.
		lab_debug_csv: Optional path for the lab-filter debug rows.
		merge_analysis_tables: When True, this grid's common-hour and timeblock
			tables are merged into the final workbook.
	"""
	output_file: str | None
	filter_spec: course_scheduling.course_filter.FilterSpec
	raw_table_output: str | None = None
	raw_table_only: bool = False
	lab_debug_csv: str | None = None
	merge_analysis_tables: bool = False


#============================================

def analysis_paths(output_file: str) -> tuple[str, str]:
	"""
	Derive the common-hour and timeblock table paths from a grid output path.

	Args:
		output_file: Path to the grid xlsx (for example "foo-grid.xlsx").

	Returns:
		Tuple of (common_hour_path, timeblock_path).
	"""
	output_dir = os.path.dirname(output_file)
	base_name = os.path.basename(output_file)
	stem = base_name.replace("-grid.xlsx", "").replace(".xlsx", "")
	common_hour_path = os.path.join(output_dir, f"{stem}-common_hour.xlsx")
	timeblock_path = os.path.join(output_dir, f"{stem}-timeblock.xlsx")
	return common_hour_path, timeblock_path


#============================================

def default_grid_configs(term_code: str, subjects: list, output_dir: str) -> list:
	"""
	Build the preset matrix of grid configurations for a term.

	Reproduces the standard set of department grids: lower undergrad, full
	undergrad, 300-level, graduate, Schaumburg, the two lab grids, the raw
	parsed table, and an all-courses grid whose analysis tables are merged.

	Args:
		term_code: Banner term code.
		subjects: Subject codes to include on every grid.
		output_dir: Directory for the grid and table outputs.

	Returns:
		List of GridConfig entries in merge order.
	"""
	subject_list = list(subjects)
	lab_debug_path = os.path.join(output_dir, f"lab_courses_{term_code}_debug.csv")
	raw_table_path = os.path.join(output_dir, f"raw_table_{term_code}-grid.xlsx")

	def spec(campus: list | None = None, levels: list | None = None,
			number: list | None = None, lab_only: bool = False) -> course_scheduling.course_filter.FilterSpec:
		# Build a FilterSpec with this run's subjects and the given filters.
		return course_scheduling.course_filter.FilterSpec(
			subjects=subject_list, campus=campus, levels=levels,
			number=number, lab_only=lab_only,
		)

	def grid_path(basename: str) -> str:
		return os.path.join(output_dir, basename)

	configs = [
		GridConfig(grid_path(f"lower_undergrad_{term_code}-grid.xlsx"),
			spec(campus=["CHICAGO CAMPUS"], number=[100, 200])),
		GridConfig(grid_path(f"undergrad_level_{term_code}-grid.xlsx"),
			spec(campus=["CHICAGO CAMPUS"], levels=["U"], number=[100, 200, 300])),
		GridConfig(grid_path(f"300_level_undergrad_{term_code}-grid.xlsx"),
			spec(levels=["U"], number=[300])),
		GridConfig(grid_path(f"graduate_level_{term_code}-grid.xlsx"),
			spec(levels=["G"])),
		GridConfig(grid_path(f"schaumburg_{term_code}-grid.xlsx"),
			spec(campus=["SCHAUMBURG CAMPUS"])),
		GridConfig(grid_path(f"lab_chicago_{term_code}-grid.xlsx"),
			spec(campus=["CHICAGO CAMPUS"], lab_only=True), lab_debug_csv=lab_debug_path),
		GridConfig(grid_path(f"lab_schaumburg_{term_code}-grid.xlsx"),
			spec(campus=["SCHAUMBURG CAMPUS"], lab_only=True)),
		GridConfig(None, spec(), raw_table_output=raw_table_path, raw_table_only=True),
		GridConfig(grid_path(f"all_courses_in_dept_{term_code}-grid.xlsx"),
			spec(), merge_analysis_tables=True),
	]
	return configs


#============================================

def clean_old_files(output_dir: str, term_code: str, merged_path: str,
		label_path: str, lab_debug_path: str) -> None:
	"""
	Remove old grid xlsx files and other intermediates before a fresh build.

	Args:
		output_dir: Directory containing the files.
		term_code: Banner term code.
		merged_path: Path to the merged output file.
		label_path: Path to the label-named copy.
		lab_debug_path: Path to the lab debug CSV.
	"""
	# Remove old grid files and stale analysis tables from a prior crashed run
	old_intermediates = []
	for pattern in ("*-grid.xlsx", "*-common_hour.xlsx", "*-timeblock.xlsx"):
		old_intermediates.extend(glob.glob(os.path.join(output_dir, pattern)))
	for path in old_intermediates:
		os.remove(path)
	# Remove specific old outputs
	for path in [
		os.path.join(output_dir, "all_class_schedule_grid_tabs.xlsx"),
		os.path.join(output_dir, f"all_class_schedule_{term_code}_grid_tabs.xlsx"),
		merged_path,
		label_path,
		lab_debug_path,
	]:
		if os.path.isfile(path):
			os.remove(path)


#============================================

def download_html_files(output_dir: str, term_code: str, subjects: list) -> list:
	"""
	Download course HTML for each subject into output_dir.

	Args:
		output_dir: Directory to write the downloaded HTML files.
		term_code: Banner term code.
		subjects: Subject codes to download.

	Returns:
		List of downloaded HTML file paths.
	"""
	html_files = []
	for subject in subjects:
		output_html = os.path.join(output_dir, f"course_finder_{term_code}_{subject}.html")
		course_scheduling.banner_http.download_subject(term_code, subject, output_html)
		html_files.append(output_html)
	return html_files


#============================================

def build_single_grid(html_files: list, config: GridConfig) -> None:
	"""
	Build one grid (and its tables) from the parsed HTML for one configuration.

	Mirrors the per-grid sequence: filter and expand into grid rows, optionally
	write the raw and lab-debug audit tables, and (unless raw-table-only) build
	the schedule grid, render the spreadsheet, and write the analysis tables.

	Args:
		html_files: Saved HTML file paths to parse.
		config: The grid configuration to build.
	"""
	classes, raw_rows, lab_debug_rows, merged_courses = course_scheduling.html_courses.load_grid_rows(
		html_files, config.filter_spec
	)

	if config.raw_table_output:
		course_scheduling.parser_audit_tables.write_raw_table(raw_rows, config.raw_table_output)

	if config.lab_debug_csv:
		course_scheduling.parser_audit_tables.write_lab_debug_rows(lab_debug_rows, config.lab_debug_csv)

	if config.raw_table_only:
		return

	sorted_classes = sorted(classes, key=lambda row: row["Label"])
	schedule_grid = course_scheduling.grid_model.populate_schedule_grid(sorted_classes)
	course_scheduling.xlsx_writer.create_spreadsheet(schedule_grid, sorted_classes, config.output_file)

	# Write the analysis tables only for the merged (unfiltered) config, so the
	# single common-hour/timeblock pair is computed once from the full course set
	# instead of once per preset filter.
	if config.merge_analysis_tables:
		common_hour_path, timeblock_path = analysis_paths(config.output_file)
		course_scheduling.schedule_analysis_tables.write_common_hour_table(merged_courses, common_hour_path)
		course_scheduling.schedule_analysis_tables.write_timeblock_table(merged_courses, timeblock_path)


#============================================

def merge_and_finalize(output_dir: str, grid_files: list, merged_path: str,
		label_path: str, term_code: str) -> None:
	"""
	Merge grid files, create the label copy, and clean up intermediates.

	Args:
		output_dir: Directory containing the merge inputs and side-effect files.
		grid_files: Grid xlsx paths in merge order.
		merged_path: Path for the merged output.
		label_path: Path for the label-named copy.
		term_code: Banner term code.
	"""
	if not grid_files:
		raise RuntimeError("No grid files to merge")

	# Merge every grid file into one tabbed workbook (in-process, no subprocess).
	course_scheduling.xlsx_merge.merge_workbooks(grid_files, merged_path)

	# Create label-named copy if different
	term_label = course_scheduling.term_code.term_code_to_label(term_code)
	if term_label != term_code:
		shutil.copy2(merged_path, label_path)
		print(f"Merged workbook: {merged_path}")
		print(f"Semester-label copy: {label_path}")
	else:
		print(f"Merged workbook: {merged_path}")

	# Clean up intermediate grid files (the two merged analysis tables are part
	# of grid_files, so they are removed here too).
	for grid_file in grid_files:
		if os.path.isfile(grid_file):
			os.remove(grid_file)

	# Clean up downloaded HTML files
	html_pattern = os.path.join(output_dir, f"course_finder_{term_code}_*.html")
	for html_file in glob.glob(html_pattern):
		os.remove(html_file)


#============================================

def build_term_workbook(term_code: str, subjects: list, grid_configs: list, output_dir: str) -> str:
	"""
	Build the merged schedule-grid workbook for one term and subject set.

	Downloads each subject's HTML once, builds every grid in grid_configs,
	merges them into a single tabbed workbook, writes a semester-label copy,
	and cleans up the intermediate files.

	Args:
		term_code: Banner term code.
		subjects: Subject codes to download once and grid across.
		grid_configs: List of GridConfig entries (the grid matrix) in merge order.
		output_dir: Directory for the downloads and generated workbook.

	Returns:
		Path to the finished workbook (the label copy when one was written,
		otherwise the term-code merged path).
	"""
	# Ensure the output directory exists before writing any grids.
	os.makedirs(output_dir, exist_ok=True)
	run_date = datetime.date.today().strftime("%Y_%m_%d")
	term_label = course_scheduling.term_code.term_code_to_label(term_code)
	merged_path = os.path.join(output_dir, f"{term_code}_schedule_grid-{run_date}.xlsx")
	label_path = os.path.join(output_dir, f"{term_label}_schedule_grid-{run_date}.xlsx")
	lab_debug_path = os.path.join(output_dir, f"lab_courses_{term_code}_debug.csv")

	# Clean old outputs before generating a fresh set.
	clean_old_files(output_dir, term_code, merged_path, label_path, lab_debug_path)

	# Download HTML once per subject; every grid reuses the same files.
	html_files = download_html_files(output_dir, term_code, subjects)

	# Build each grid and assemble the merge list in configuration order.
	# The common-hour and timeblock analysis tables are written by
	# build_single_grid as standalone deliverables; they are intentionally
	# left out of grid_files so they stay separate files and do not become
	# workbook tabs (and so merge_and_finalize cleanup does not delete them).
	grid_files = []
	for config in grid_configs:
		build_single_grid(html_files, config)
		if config.raw_table_only:
			grid_files.append(config.raw_table_output)
		else:
			grid_files.append(config.output_file)

	# Emit the lab-debug note before the workbook summary so the final stdout
	# line stays the merged workbook path (printed by the caller).
	print(f"Lab debug CSV: {lab_debug_path}")
	merge_and_finalize(output_dir, grid_files, merged_path, label_path, term_code)

	# Prefer the semester-label copy when one was written.
	xlsx_path = label_path if os.path.isfile(label_path) else merged_path
	return xlsx_path
