# Changelog

## 2026-07-20

### Behavior or Interface Changes

- Patch 2: add baseline priming for the email-report daemon. `--prime` fetches
  every subject, persists the cache and full-section memory, and sends no email;
  `run_email_tmux.sh` now primes before starting the loop by default. Pass
  `--no-prime` when a restart should preserve changes accumulated while the loop
  was down for the next report.

### Fixes and Maintenance

- Patch 1: restore process isolation for recurring report fires. The import trace
  showed that the long-lived daemon loaded PyObjC through the in-process report
  pipeline, which kept a Python Dock icon present while the daemon slept. Each
  scheduled fire now runs the report in a short-lived subprocess, and the daemon
  imports `report_pipeline` lazily only in that child path. The scheduler and
  pipeline module docstrings now describe that boundary accurately.

### Decisions and Failures

- Rejected the AppKit activation-policy approach because it would mask the Dock
  symptom instead of removing the long-lived PyObjC load. macOS denied `/bin/ps`,
  so the exact Dock-registration timing was not confirmed; the import trace and
  the background-only daemon status check support the isolation fix.

## 2026-06-29

### Additions and New Features

- Docset refresh (docset-updater chain): created `docs/CODE_ARCHITECTURE.md`,
  `docs/FILE_STRUCTURE.md`, `docs/INSTALL.md`, `docs/USAGE.md`,
  `docs/FILE_FORMATS.md`, `docs/YAML_FILE_FORMAT.md`,
  `docs/TROUBLESHOOTING.md`, `docs/RELEASE_HISTORY.md`; updated `AGENTS.md`;
  rewrote `README.md` quick-start and documentation links; screenshot-docs
  rendered the real color-coded schedule grid (full-width landscape, all five
  weekday columns) from `output/Fall_2026_schedule_grid-2026_06_29.xlsx` via
  LibreOffice headless export and embedded `docs/screenshots/grid_example.png`
  into `README.md`.

- Patch 13: move runtime state (cache, logs, generated grids) out of
  `course_scheduling/` to repo-root `cache/` `logs/` `output/`; gitignored;
  `course_scheduling/` is now code-only.

- Patch 11c: rename the one curated CSV to `data/spring_2026_sample_courses.csv`;
  remove historical per-department split artifacts and the malformed
  `all_spring_2026.csv` during data cleanup. Updated `docs/USAGE.md` and
  `README.md` examples to `data/spring_2026_sample_courses.csv`.
  CSV smoke passes; 831 tests pass; old name absent from docs.
  Final desired `data/` contents: only `data/spring_2026_sample_courses.csv`.
  All other files in `data/` are for user to delete:
  `spring_2026_all_subjects_main_list.csv`, `spring_2026_biol.csv`,
  `spring_2026_chem.csv`, `spring_2026_all_except_biol_chem.csv`,
  `all_spring_2026.csv`, `Spring_2026_schedule_draft_All_Subjects-main_list.csv`,
  `Spring_2026_schedule_draft_All_but_BIOL_CHEM-copy.csv`,
  `Spring_2026_schedule_draft_BIOL-copy.csv`,
  `Spring_2026_schedule_draft_CHEM-copy.csv`,
  `filtered_input.csv`, `lab_courses_202710_debug.csv`.
  Also the 5 stale `course_scheduling/` CSV originals (absent from disk).

- Patch 11c (prior): scope reduction -- curate only one sample input CSV in `data/`.
  `data/spring_2026_all_subjects_main_list.csv` is the sole kept input;
  per-department splits were leftover manual artifacts, not a documented workflow.
  Doc examples (`docs/USAGE.md`, `README.md`) already reference the correct path.
  CSV smoke passes. Files for user to delete from `data/`:
  `spring_2026_biol.csv`, `spring_2026_chem.csv`, `spring_2026_all_except_biol_chem.csv`,
  `all_spring_2026.csv`, `Spring_2026_schedule_draft_All_Subjects-main_list.csv`,
  `Spring_2026_schedule_draft_All_but_BIOL_CHEM-copy.csv`,
  `Spring_2026_schedule_draft_BIOL-copy.csv`, `Spring_2026_schedule_draft_CHEM-copy.csv`.
  Also the 5 stale `course_scheduling/` originals (already absent from disk).

- Patch 12: keep plural `build_grids_from_html.py` as the root HTML command;
  trimmed to `-t/--term` + repeatable `--subject` only (removed `cs_cli` /
  `add_common_filters` -- per-grid campus/level/number flags are consumed by the
  preset matrix, not this entry point). Default science subjects (`_DEFAULT_SUBJECTS`)
  applied in `main()` when no `--subject` given. Updated `README.md` and `docs/USAGE.md`:
  plural name throughout; "Common filter flags" sections scope the full filter set to
  `tools/build_grid_from_csv.py` only; added inline note near each HTML-command example
  that it always builds the standard preset matrix and to use the CSV tool for custom
  campus/level/number filtering. `--help` shows only two flags; pyflakes clean; 834
  tests pass. Singular `build_grid_from_html.py` listed for user to delete.

- Patch 11b: rename curated input CSVs in `data/` to lowercase snake_case;
  exclude malformed `all_spring_2026.csv` from `data/` (listed for deletion).
  Rename map: `Spring_2026_schedule_draft_All_Subjects-main_list.csv` ->
  `spring_2026_all_subjects_main_list.csv`,
  `Spring_2026_schedule_draft_All_but_BIOL_CHEM-copy.csv` ->
  `spring_2026_all_except_biol_chem.csv`,
  `Spring_2026_schedule_draft_BIOL-copy.csv` -> `spring_2026_biol.csv`,
  `Spring_2026_schedule_draft_CHEM-copy.csv` -> `spring_2026_chem.csv`.
  Updated `docs/USAGE.md` and `README.md` examples to
  `data/spring_2026_all_subjects_main_list.csv`. CSV smoke passes; 831 tests pass.
  Files for user to delete: `data/Spring_2026_schedule_draft_All_Subjects-main_list.csv`,
  `data/Spring_2026_schedule_draft_All_but_BIOL_CHEM-copy.csv`,
  `data/Spring_2026_schedule_draft_BIOL-copy.csv`,
  `data/Spring_2026_schedule_draft_CHEM-copy.csv`, `data/all_spring_2026.csv`;
  also the stale `course_scheduling/` originals (5 files, already gone from disk).

- Patch 11: move input CSV drafts to `data/`; update doc example paths in
  `docs/USAGE.md` and `README.md` (both now reference `data/` instead of
  `course_scheduling/`). `.gitignore` rules are all `course_scheduling/`-scoped;
  `data/*.csv` inputs remain trackable. CSV smoke test passes from new path;
  831 pytest tests pass. Files for user to delete from `course_scheduling/`:
  `Spring_2026_schedule_draft_All_Subjects-main_list.csv`,
  `Spring_2026_schedule_draft_All_but_BIOL_CHEM-copy.csv`,
  `Spring_2026_schedule_draft_BIOL-copy.csv`,
  `Spring_2026_schedule_draft_CHEM-copy.csv`,
  `all_spring_2026.csv` (note: this file has known malformed rows).

- Patch 10: collapse `cli/filters.py` into `course_scheduling/cs_cli.py`
  (single command-arg adapter; the one module under `course_scheduling/` that
  may import argparse); repoint all importer stubs:
  `build_grid_from_html.py`, `tools/build_grid_from_csv.py`,
  `course_scheduling/grid_courses_from_html.py`,
  `course_scheduling/grid_courses_from_csv.py`,
  `tests/test_cli_filters.py` (`import cli.filters` ->
  `import course_scheduling.cs_cli`, call sites updated accordingly).
  733 tests pass (1 pre-existing README.md/USAGE.md link failure unchanged);
  `pyflakes` clean; all three CLI `--help` exits 0; no remaining
  `cli.filters` references in the repo. Files for user to delete:
  `cli/filters.py`, `cli/__init__.py` (and the now-empty `cli/` folder).

- Patch 8: strip CLI from `course_scheduling/xlsx_merge.py` (now import-only:
  removed `parse_args`, `if __name__ == '__main__'`, `import argparse`,
  `import sys`; replaced `sys.exit(1)` with `raise ValueError`); repoint
  `tests/test_full_report_integration.py` to import
  `course_scheduling.change_detect` and `course_scheduling.change_summary`
  directly (call sites updated: `report.evaluate_subject_changes` ->
  `course_scheduling.change_detect.evaluate_subject_changes`,
  `report.build_change_summary` ->
  `course_scheduling.change_summary.build_change_summary`); repoint
  `tests/test_full_course_memory.py` to `import
  course_scheduling.full_course_memory` (all call sites updated). 734 tests
  pass; `pyflakes` clean. Absorbed scripts confirmed orphaned and listed for
  user removal: `course_scheduling/grid_courses_from_html.py`,
  `course_scheduling/grid_courses_from_csv.py`,
  `course_scheduling/download_course_finder_html.py`,
  `course_scheduling/email_schedule_report.py`,
  `course_scheduling/email_schedule_loop.py`,
  `build_grids_from_html.py` (root, plural),
  `course_scheduling/csv_main_filter.sh`.

- Patch 7: add root `build_grid_from_html.py` stub (thin CLI over
  `course_scheduling.workbook_builder.build_term_workbook` + `default_grid_configs`),
  `tools/email_schedule_report.py` (one-shot or `--loop` over
  `course_scheduling.report_pipeline.run_report` /
  `course_scheduling.report_scheduler.run_loop`), and
  `tools/build_grid_from_csv.py` (CSV -> grid via
  `csv_courses.load_grid_rows` -> `grid_model.populate_schedule_grid` ->
  `xlsx_writer.create_spreadsheet`). Updated `run_email_tmux.sh` to launch
  `tools/email_schedule_report.py --loop --term $TERM_CODE` instead of
  `course_scheduling/email_schedule_loop.py`. All three stubs carry the
  `#!/usr/bin/env python3` shebang as the first line and the executable bit;
  subject default (`BIOL`/`PHYS`/`CHEM`/`BCHM`) lives only in the stubs
  (argparse defaults), not in the library. 734 tests pass; `pyflakes` clean;
  CSV stub output is content-equivalent (same dimensions, merges, cells, fills)
  to the prior `grid_courses_from_csv.py` reference.

- Patch 6: absorb orchestration into `change_detect`, `csv_cache`,
  `email_report`, `report_pipeline`, `report_scheduler`, and
  `workbook_builder`; replace all project subprocess chains with in-process
  package-qualified calls (the download/parse/diff path, the grid-build
  matrix, and the loop now call the library directly). Subjects are passed in
  and the library is subject-agnostic; the science default set
  (`BIOL`/`PHYS`/`CHEM`/`BCHM`) lives only at the command layer
  (`email_schedule_report.py`, `email_schedule_loop.py`,
  `build_grids_from_html.py`). Only the legitimate `open -a Mail` shell-out
  remains under `course_scheduling/`.

- Patch 3: split `banner_html_parse.py` into `html_tokens.py` (eight
  low-level primitives: `normalize_day_token`, `parse_html_time`,
  `normalize_label_text`, `extract_text`, `find_data_value_element`,
  `find_first_data_value_element`, `parse_meeting_blocks`,
  `infer_campus_from_text`) and `banner_parser.py`
  (`load_and_parse_class_data_from_file`, the course-record builder).
  Renamed four modules to responsibility names:
  `crosslist_merge` -> `crosslist_resolver`,
  `change_report` -> `change_summary`,
  `email_send` -> `email_sender`,
  `merge_xlsx_files` -> `xlsx_merge` (internal function renamed to
  `merge_workbooks` to avoid substring collision in grep).
  Added `term_code.py` with a single `term_code_to_label` function,
  replacing the duplicate copies in `email_schedule_report.py` and
  `build_grids_from_html.py`; both callers repointed to
  `course_scheduling.term_code.term_code_to_label`. Updated every
  importer to package-qualified names; updated `COURSE_SCHEDULING_README.md`
  and `csv_main_filter.sh` for the renamed module. 551 tests pass;
  `pyflakes` clean; all hygiene gates green.

- Patch 4: split `schedule_grid_xlsx.py` into `grid_model.py` (pure
  in-memory grid and column/placement math: `validate_and_extract_course`,
  `populate_schedule_grid`, `time_slot_to_row_number`, `compute_columns_info`,
  `find_available_column` with its unused `ws` parameter dropped,
  `fill_the_status_grid`, plus a new `generate_time_slots` helper) and
  `xlsx_writer.py` (openpyxl rendering: `format_merged_cells`,
  `format_schedule_sheet`, `write_time_slots_to_column`,
  `write_spreadsheet_labels`, `create_spreadsheet`, plus `shade_common_hour`
  moved in from `schedule_time.py`). Split `grid_analysis_output.py` into
  `parser_audit_tables.py` (`log_filter_exclusion`, `write_raw_table`,
  `write_lab_debug_rows`) and `schedule_analysis_tables.py`
  (`write_common_hour_table`, `write_timeblock_table`). Renamed
  `course_colors` -> `schedule_colors`. Purified `schedule_time.py` so it
  imports no openpyxl and no color module. Repointed every importer
  (`grid_courses_from_html.py`, `grid_courses_from_csv.py`, `banner_parser.py`)
  to the new package-qualified module names. The CSV grid build is
  content-equivalent (cell values, fill colors, merged ranges) before and
  after; the raw/lab/analysis table outputs match the prior pandas output.

- Patch 5: add `banner_http.py` (network discovery/fetch: `get_search_page`,
  `parse_subject_options`, `build_post_payload`, `post_results`,
  `write_error_html`, plus new `download_subject(term, subject, output_file)`
  for one subject per call and `list_subjects(term)`), `html_courses.py`
  (`load_grid_rows(html_files, filter_spec)` plus the relocated
  `expand_courses_to_grid_rows`; filter + expand only, no HTML parsing), and
  `csv_courses.py` (`load_grid_rows(input_file, filter_spec)` reading with
  `csv.DictReader`). Replaced the last pandas read path with `csv.DictReader`
  and dropped pandas from `pip_requirements.txt`. Re-typed
  `banner_parser.load_and_parse_class_data_from_file` to take `FilterSpec`
  directly (removed the temporary args->FilterSpec bridge). Repointed
  `grid_courses_from_html.py` and `grid_courses_from_csv.py` to the new
  loaders. CSV and HTML grid builds (plus common-hour and timeblock tables)
  are content-equivalent (cell values, fill colors, merged ranges) before and
  after; CSV edge cases (empty file, blank `Begin_Time`, blank `Meeting_Days`,
  non-active status, `Begin_Time` < 600) skip identically to the prior read
  path. 634 tests pass; `pyflakes` clean; `test_import_requirements` green.

- WP-4.2: add `cli/__init__.py` (docstring-only package marker) and
  `cli/filters.py` with three functions: `add_common_filters(parser)` registers
  the shared campus/level/number/subject/lab-only filter flags on any argparse
  parser; `filter_spec_from_args(args)` converts a parsed Namespace to a
  `course_scheduling.course_filter.FilterSpec` (the single argparse->FilterSpec
  boundary); `output_filename_from_args(args)` delegates to
  `course_scheduling.output_naming.generate_output_filename`. Repointed
  `course_scheduling/grid_courses_from_html.py` and
  `course_scheduling/grid_courses_from_csv.py` to call
  `cli.filters.add_common_filters`, `cli.filters.filter_spec_from_args`, and
  `cli.filters.output_filename_from_args`, removing the inline bridge
  duplication from both scripts. Added `tests/test_cli_filters.py` with three
  focused deterministic tests for `filter_spec_from_args`. All 551 tests pass;
  `pyflakes` clean; hygiene gates green.

- Patch 1: populate `pip_requirements.txt` with the six runtime deps
  (`lxml`, `openpyxl`, `pandas`, `py-applescript`, `pyyaml`, `requests`)
  used by `course_scheduling/` scripts; enforced by
  `tests/test_import_requirements.py`.
- Patch 2: add `course_scheduling/__init__.py` package marker (docstring only)
  and add `course_scheduling/` to `sys.path` in `tests/conftest.py`; repair the
  two project tests (`tests/test_full_course_memory.py`,
  `tests/test_full_report_integration.py`) to flat imports (`import file_utils`,
  `import full_course_memory`, `import email_schedule_report`) matching the
  runtime SCRIPT_DIR bootstrap.
- WP-4.1: split `course_scheduling/course_filters.py` (461 lines) into five
  argparse-free library modules -- `course_label.py` (label parsing and
  normalization), `lab_filter.py` (lab-detection heuristic and token
  constants), `course_filter.py` (a `FilterSpec` dataclass plus
  `evaluate_class_inclusion`/`should_include_class` re-typed to take
  `FilterSpec` instead of an argparse `Namespace`), `enrollment_parse.py`
  (enrollment-ratio parsing), and `output_naming.py` (a pure
  `generate_output_filename(subjects, levels, numbers, campus)` builder).
  New modules import siblings package-qualified
  (`import course_scheduling.<module>`). Dropped dead code
  (`is_probable_lab_course`, `infer_waitlisted_from_row`,
  `parse_waitlist_value`), which removed the only pandas use, so the new
  modules import no pandas. Repointed importers
  (`crosslist_merge.py`, `course_colors.py`, `banner_html_parse.py`,
  `schedule_grid_xlsx.py`, `grid_courses_from_html.py`,
  `grid_courses_from_csv.py`) to the new modules; the grid loaders and the
  banner parser build a `FilterSpec` from `args` at the call site as a
  temporary bridge. The argparse filter flags (`add_common_filters`) were
  inlined into the two grid CLI scripts as a bridge pending the WP-4.2
  `cli/filters.py` helper. Deleted `course_filters.py` and updated
  `course_scheduling/COURSE_SCHEDULING_README.md`.

### Behavior or Interface Changes

- The merged term workbook no longer includes the common-hour (`-comm`) and
  timeblock (`-time`) tabs; those analysis tables are now written as standalone
  xlsx files in the output dir, matching the original workflow. The merged
  workbook is now 9 tabs: the preset grids, lab_chicago, lab_schaumburg,
  raw_table, and all_courses_in_dept-grid.

- Per-preset common-hour/timeblock files are no longer generated then deleted;
  the single analysis pair is computed once from the full course set.

- `build_grids_from_html.py` output is much quieter: removed per-subject
  "Loaded N", per-sheet "Added", per-course filter-remove, tab-merge-order
  list, and per-file "removed" prints. The final stdout line is now the merged
  workbook path.

- Patch 16: quiet the `build_grids_from_html.py` run and make the final stdout
  line the merged workbook path. Removed the high-volume loop prints: per-file
  "Loaded N courses" (`course_scheduling/banner_parser.py`), per-sheet "Added
  '<sheet>'" (`course_scheduling/xlsx_merge.py`), per-course "<filter> remove:
  <label>" (deleted dead `log_filter_exclusion` in
  `course_scheduling/parser_audit_tables.py` and the duplicate prints in
  `course_scheduling/course_filter.py` `should_include_class`), and the "Tab
  merge order" list plus per-file "removed '<path>'" lines in
  `merge_and_finalize`. The root stub now prints the returned workbook path as
  its last statement, and the "Lab debug CSV" note is emitted before the
  workbook summary so it is no longer the final line.

- Patch 4: removed pandas from `grid_model.py`, `xlsx_writer.py`,
  `parser_audit_tables.py`, `schedule_analysis_tables.py`, and
  `schedule_time.py` (dependency reduction, output identical). The 15-minute
  grid slots (07:00..23:45) are now generated with `datetime`/`timedelta`
  instead of `pandas.date_range`; `time_to_slot` parses with
  `datetime.strptime('%H%M')` instead of `pandas.to_datetime`; the audit and
  analysis tables write via the `csv` module and openpyxl instead of
  `DataFrame.to_csv`/`.to_excel` (sheet names `raw_data`,
  `common_hour_conflicts`, `nonstandard_timeblocks` and column order
  preserved). `validate_and_extract_course` now takes a `Mapping` row so it
  works with both dict and Series-like rows. Equivalence was confirmed: the
  stdlib slot list matches the former `date_range` output exactly and `%H%M`
  parsing matches `to_datetime` across edge cases and the real CSV values.

- Prior pass: moved the two most-common entry points to the repo root and
  renamed the batch HTML pipeline. `course_scheduling/html_main_filter.py`
  became root `build_grids_from_html.py` (plural grids) and
  `course_scheduling/html_main_filter.sh` became root
  `build_grids_from_html.sh`; both now resolve their sibling worker scripts
  (`download_course_finder_html.py`, `grid_courses_from_html.py`,
  `merge_xlsx_files.py`) and write all generated outputs under the
  `course_scheduling/` subfolder, so behavior is unchanged. Moved
  `course_scheduling/run_email_tmux.sh` to the repo root (its git-derived
  `REPO_ROOT`/`SCRIPT_DIR` paths already targeted `course_scheduling/`, so
  only the usage comment changed). Repointed the subprocess caller in
  `course_scheduling/email_schedule_report.py` (`run_report_generation`) from
  `html_main_filter.py` to the root `build_grids_from_html.py`. Staged
  `course_scheduling/full_course_memory.py` so `tests/test_import_requirements.py`
  detects it as a local module. `README.md` quick start now leads with the
  two root commands (`./build_grids_from_html.py -t <term>` and
  `./run_email_tmux.sh`), then a single dry-run change-detection report, with
  an Advanced section pointing at the CSV path
  (`course_scheduling/grid_courses_from_csv.py`). The single-subject worker
  `grid_courses_from_html.py` and all library modules stay in
  `course_scheduling/`.

### Fixes and Maintenance

- Guarded `course_label.extract_course_number` against the `None` return of
  `split_course_label` (was a latent TypeError on any non-matching label).

- `banner_parser` raises `FileNotFoundError` instead of calling `sys.exit(1)`.

- `change_summary` and `xlsx_writer` use direct `dict[key]` access for keys
  that are always present (was `.get(...)`/`value or fallback` hiding bugs).

- Converted `from openpyxl import ...` to module-qualified imports in
  `xlsx_writer` and `xlsx_merge`; `.format()` to f-string in `schedule_colors`.

- Extracted the Mail-retry logic in `email_sender` into a helper so the
  try/except body is two lines.

- Removed a duplicate (no-op) time-slot write in
  `xlsx_writer.format_schedule_sheet` and corrected its docstring.

- Renamed `build_term_workbook`'s `filter_specs` parameter to `grid_configs`
  (it takes GridConfig objects).

- Added missing module/function docstrings across the library modules.

- Fixed the `run_email_tmux.sh` log path note (already at repo-root `logs/`).

- Corrected `README.md` and `docs/USAGE.md`: removed the nonexistent
  `data/spring_2026_sample_courses.csv` sample references and the nonexistent
  `--subject` flag for the CSV tool; added a `docs/USAGE.md` link to the
  README Documentation section.

- Patch 16: write the common-hour and timeblock analysis tables once from the
  full parsed course set instead of once per preset filter.
  `build_single_grid` now writes them only under the `merge_analysis_tables`
  config (the unfiltered all-courses grid), removed the generate-then-delete
  glob cleanup in `merge_and_finalize`, and added `*-common_hour.xlsx` /
  `*-timeblock.xlsx` to the startup `clean_old_files` sweep so stale tables from
  a crashed run are cleared. The merge list now holds the preset grid tabs plus
  exactly one common-hour and one timeblock tab.

- Patch 15: fix undergrade->undergrad typo in grid filename preset
  `lower_undergrade_` -> `lower_undergrad_` in `course_scheduling/workbook_builder.py:110`.

- Patch 14: `build_grids_from_html.py` keeps `--term` required (avoids stale
  hardcoded term); `--subject` defaults to BIOL/PHYS/CHEM/BCHM.

- Patch 9: rewrite `README.md` by workflow (not internal files): quick start
  leads with `./build_grid_from_html.py -t <term>` and `./run_email_tmux.sh`;
  add a Tools / Advanced section for `tools/email_schedule_report.py` and
  `tools/build_grid_from_csv.py`; document `--subject` configurability;
  name no internal library module as a user command. Create `docs/USAGE.md`
  from the content of `course_scheduling/COURSE_SCHEDULING_README.md`,
  rewritten for the new commands with full flag reference, HTML and CSV
  workflow examples, tmux daemon usage, output and color notes, and
  full-course memory semantics; remove all references to deleted scripts.
  Remove stray debug `print(schedule_grid.keys())` from
  `course_scheduling/xlsx_writer.py` `format_schedule_sheet` (leftover
  debug output; no behavior change). Reconcile `docs/CHANGELOG.md`: relabel
  pre-plan entries that collided with the current plan's Patch N numbering;
  add this Patch 9 bullet. 734 tests pass; `pytest tests/test_readme_first_paragraph.py
  tests/test_markdown_links.py tests/test_ascii_compliance.py` green;
  deleted-script grep in `README.md` and `docs/USAGE.md` is empty;
  `pyflakes course_scheduling/xlsx_writer.py` clean.
- Prior pass: rewrite `README.md` first paragraph and body prose to describe
  methods and output (color-coded Excel workbooks from course-listing HTML or
  CSV exports, 15-minute time slots, subject/level colors, tmux-scheduled
  email reports) with no institution, vendor product, or discipline names;
  all three verification tests pass (74/74) and banned-term grep is empty.
- Prior pass: write `README.md` first paragraph (pure prose, under 250 chars,
  documents tmux runner as the supported scheduler); fix `run_email_tmux.sh`
  to invoke Python via `source source_me.sh && python3` instead of the
  hardcoded `/opt/homebrew/` interpreter path; drop stale `local_llm_wrapper`
  entry from `LOCAL_IMPORT_WHITELIST` in `tests/test_import_requirements.py`.
- Prior pass: gitignore `course_scheduling/` generated artifacts (dated grids,
  `csv_cache/`, `logs/`, debug/intermediate CSVs); inputs (`all_spring_2026.csv`,
  `Spring_2026_*.csv`) remain tracked.
- Prior pass: verified generated artifacts (`*_schedule_grid-2026_*.xlsx`,
  `csv_cache/`, `logs/`, `*_debug.csv`, `filtered_input.csv`) are gitignored
  and remain untracked; `git add --dry-run course_scheduling/` confirms they
  are excluded while source modules, shell scripts, input CSVs, and
  `tests/fixtures/` are stage-ready; no unstaging was needed because the
  entire `course_scheduling/` tree was already untracked.
- Prior pass: split `course_scheduling/course_finder_lib.py` (1161 lines) into
  four focused library modules -- `course_filters.py` (460 lines: argparse
  filter flags, course-label parsing/normalization, lab classification,
  waitlist/section parsing), `course_colors.py` (133 lines: HLS color math
  and subject/level color constants), `schedule_time.py` (176 lines:
  common-hour, slot, and official-time-block logic), and
  `schedule_grid_xlsx.py` (414 lines: grid data model and openpyxl
  rendering) -- using flat absolute imports between the new modules;
  repointed the 15 public call sites in `grid_courses_from_csv.py` and
  `grid_courses_from_html.py` to their new owning modules; updated
  `course_scheduling/COURSE_SCHEDULING_README.md` to list the new modules;
  added behavior-preserving signature type hints to
  `grid_courses_from_csv.py`. Pre-split and post-split grids built from
  `Spring_2026_schedule_draft_All_Subjects-main_list.csv --biol -n 100` are
  content-equivalent (identical populated cell values, fill colors, and
  merged cell ranges).
- Prior pass: split `course_scheduling/grid_courses_from_html.py` (765 lines)
  into three focused library modules -- `banner_html_parse.py` (323 lines:
  HTML day/time token normalization, dataLabel/dataValue lookup helpers,
  `parse_meeting_blocks`, campus inference, and the lxml per-file parser),
  `crosslist_merge.py` (204 lines: union-find cross-list discovery,
  symmetry validation, and same-subject merging), and
  `grid_analysis_output.py` (118 lines: filter-exclusion logging plus
  raw-table, lab-debug, common-hour, and non-standard-timeblock writers) --
  using flat absolute imports; left `grid_courses_from_html.py` as the
  170-line CLI keeping `parse_args`, `expand_courses_to_grid_rows`,
  `load_and_parse_class_data`, and a new `def main()` built from the former
  inline `__main__` body; repointed the `parse_meeting_blocks` consumer in
  `change_report.py` from `import grid_courses_from_html` to
  `import banner_html_parse`; added full type hints to every moved and kept
  function so `tests/test_function_typing.py` is green. Pre-split and
  post-split grids built from `course_finder_sample_crn.html --biol` are
  content-equivalent (identical populated cell values, fill colors, and
  merged cell ranges).

### Removals and Deprecations

- Removed dead functions `banner_http.list_subjects` and
  `banner_http.parse_subject_options` (zero callers after the reorg).

- Patch 4: deleted `schedule_grid_xlsx.py`, `grid_analysis_output.py`, and
  `course_colors.py` after their functions moved into `grid_model.py` /
  `xlsx_writer.py`, `parser_audit_tables.py` / `schedule_analysis_tables.py`,
  and `schedule_colors.py`; no facade or re-export shim was left behind.
  Dropped dead code in the same pass: `is_cell_merged` (zero callers) and
  `number_to_pastel_hex` (zero callers). Removed `shade_common_hour` from
  `schedule_time.py` (moved to `xlsx_writer.py`), so `schedule_time.py` no
  longer imports openpyxl or a color module.
- Prior pass: removed the `html_main_filter.py` / `html_main_filter.sh` names;
  the batch HTML pipeline is now `build_grids_from_html.py` /
  `build_grids_from_html.sh` at the repo root with no compatibility shim.
- Prior pass: deleted dead launchd scheduler files
  `course_scheduling/edu.roosevelt.course_schedule_report.plist` and
  `course_scheduling/install_plist.sh`; replaced by `run_email_tmux.sh`
  and `email_schedule_loop.py`.
- Prior pass: removed `course_scheduling/course_finder_lib.py` after its
  functions moved into `course_filters.py`, `course_colors.py`,
  `schedule_time.py`, and `schedule_grid_xlsx.py`; no facade/re-export shim
  was left behind (there is no external consumer). Dropped the four
  import-time `assert` statements that documented `time_slot_to_row_number`
  examples, since `docs/PYTHON_STYLE.md` disallows asserts in library
  modules.

### Developer Tests and Notes

- Added `tests/e2e/e2e_build_grids.py`: live-network e2e for `build_grids_from_html.py`;
  asserts exit 0, final stdout line is an existing `.xlsx`, exactly 9 correct workbook tabs,
  and two standalone analysis files in `output/`. Also added `tests/e2e/run_all.sh`.

- Pruned fragile pytests per PYTEST_STYLE: removed a stale `sys.path` insert
  in conftest, unused `tmp_path` params, collection-size (`len(...) == 1`)
  assertions, exact email-format-string assertions, and over-exhaustive
  CLI-filter assertions. Suite is 741 passed.

- Prior pass: add type hints to `download_course_finder_html.py`,
  `email_schedule_loop.py`, `html_main_filter.py`, and `merge_xlsx_files.py`
  to satisfy `tests/test_function_typing.py`; changes are annotation-only
  (no behavior, logic, or CLI flag changes); all 138 hygiene-gate tests pass.

- Prior pass: split `course_scheduling/email_schedule_report.py` (783 lines)
  into three focused library modules -- `csv_diff.py` (120 lines: row
  loading and byte-level diff), `change_report.py` (157 lines: summary
  text and field-change formatting, imports `grid_courses_from_html` for
  `parse_meeting_blocks`; later repointed to `banner_html_parse`),
  `email_send.py` (81 lines: AppleScript transport and `RECIPIENTS` constant)
  -- and kept `email_schedule_report.py` as the thin 448-line orchestrator
  CLI with its shebang and `__main__` intact; `full_course_memory.py` is
  byte-unchanged; all hygiene gates pass (161/161).

- Verified the `course_scheduling` package rewrite reproduces the old flat
  script behavior using a throwaway end-to-end parity harness with three
  lanes: pure-function parity, grid data and color parity, and email and
  change-detection parity. The harness scripts and their HTML fixtures have
  since been removed per the plan; the durable evidence is retained under
  `docs/active_plans/reports/`: the trust report
  (`course_scheduling_rewrite_trust_report.md`) plus three lane records
  (`wp2a_pure_function_parity_lane.md`, `wp2b_grid_data_color_parity.md`,
  `wp2c_email_change_detection_parity.md`). All disclosed differences were
  accepted-intentional except one inconclusive-fixture item. Verdict: SAFE to
  retire the old flat scripts, pending a separate human retirement action.
