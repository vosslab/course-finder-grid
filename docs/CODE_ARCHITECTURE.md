# Code architecture

Overview of the system design, major components, data flow, and extension points
for the `course_scheduling` package and its entry-point scripts.

## Overview

The repo generates color-coded weekly schedule grids as Excel workbooks from two
source types: live Banner Course Finder HTML pages and draft-schedule CSV exports.
A separate email path detects enrollment changes between runs and sends reports via
Mail.app.

The `course_scheduling/` directory is a pure-code Python package. All runtime
state (cache snapshots, logs, generated workbooks) lives at the repo root in
`cache/`, `logs/`, and `output/`, which are gitignored.

## Major components

### Entry-point scripts

| Script | Purpose |
| --- | --- |
| [build_grids_from_html.py](../build_grids_from_html.py) | Root launcher: download HTML, build preset grid matrix, write merged workbook to `output/` |
| [tools/build_grid_from_csv.py](../tools/build_grid_from_csv.py) | One-off grid from a CSV export; accepts full filter set |
| [tools/email_schedule_report.py](../tools/email_schedule_report.py) | One-shot or looping change-detection report; sends email via Mail.app |
| [run_email_tmux.sh](../run_email_tmux.sh) | Starts the email daemon in a named tmux session |

### Command and argument layer

- [course_scheduling/cs_cli.py](../course_scheduling/cs_cli.py): shared `argparse` flag definitions
  (`add_common_filters`, `add_subject_flags`, `build_filter_spec`); the only module in the package
  that imports `argparse`.
- [course_scheduling/course_filter.py](../course_scheduling/course_filter.py): `FilterSpec` dataclass
  (subjects, campus, levels, number series, lab_only) and `evaluate_class_inclusion` predicate.

### Download and parse (HTML path)

- [course_scheduling/banner_http.py](../course_scheduling/banner_http.py): opens a requests session,
  fetches the Banner Course Finder search page for a term, POSTs the FIND COURSES form per subject,
  and saves the result HTML to `cache/`.
- [course_scheduling/banner_parser.py](../course_scheduling/banner_parser.py): reads a saved HTML file
  with `lxml`, iterates `courseResultsBox` divs, and produces filtered course dicts plus raw and
  lab-debug audit rows.
- [course_scheduling/html_tokens.py](../course_scheduling/html_tokens.py): low-level primitives for
  day/time token normalization, `dataLabel`/`dataValue` lookup, meeting-block parsing, and campus
  inference.
- [course_scheduling/html_courses.py](../course_scheduling/html_courses.py): applies `FilterSpec` and
  expands parsed course dicts into per-meeting grid rows; delegates parsing to `banner_parser`.
- [course_scheduling/crosslist_resolver.py](../course_scheduling/crosslist_resolver.py): union-find
  merging of cross-listed sections into slash-delimited labels.
- [course_scheduling/enrollment_parse.py](../course_scheduling/enrollment_parse.py): parses Banner
  "Enrolled / capacity" text into a fill ratio.

### CSV path

- [course_scheduling/csv_courses.py](../course_scheduling/csv_courses.py): reads a draft-schedule CSV
  with `csv.DictReader`, applies `FilterSpec`, and produces per-meeting grid rows.

### Grid model and rendering

- [course_scheduling/grid_model.py](../course_scheduling/grid_model.py): pure in-memory grid; builds a
  day/time-slot structure from 07:00 to 23:45 in 15-minute steps (68 slots); holds no openpyxl logic.
- [course_scheduling/xlsx_writer.py](../course_scheduling/xlsx_writer.py): consumes the grid model and
  writes the spreadsheet with openpyxl; merges duration cells, writes day/time labels, colors by
  course identity, and shades the common hour.
- [course_scheduling/schedule_colors.py](../course_scheduling/schedule_colors.py): deterministic pastel
  fill colors keyed on subject hue, course level (lightness), and enrollment/waitlist state.
- [course_scheduling/schedule_time.py](../course_scheduling/schedule_time.py): time-slot arithmetic
  helpers.

### Workbook coordinator

- [course_scheduling/workbook_builder.py](../course_scheduling/workbook_builder.py): thin coordinator;
  owns the preset matrix of `GridConfig` objects (lower undergrad, full undergrad, 300-level, graduate,
  Schaumburg, lab-only, raw table, all-courses); sequences download -> parse -> filter -> grid ->
  write -> merge for one term.
- [course_scheduling/xlsx_merge.py](../course_scheduling/xlsx_merge.py): copies multiple single-sheet
  xlsx files into one multi-tab workbook, preserving formatting and merged cells.

### Analysis and audit tables

- [course_scheduling/parser_audit_tables.py](../course_scheduling/parser_audit_tables.py): CSV and xlsx
  writers for the raw parsed table and lab-filter debug rows; supports auditing of the parse/filter stage.
- [course_scheduling/schedule_analysis_tables.py](../course_scheduling/schedule_analysis_tables.py): xlsx
  writers for two policy-audit tables (common-hour overlaps and off-block starts).

### Change detection and email path

- [course_scheduling/change_detect.py](../course_scheduling/change_detect.py): pure
  `evaluate_subject_changes` seam (used by both production and unit tests); also owns
  `check_for_changes`, which downloads and parses each subject then diffs against the cache.
- [course_scheduling/csv_diff.py](../course_scheduling/csv_diff.py): CSV row loading and row-level
  comparison helpers.
- [course_scheduling/csv_cache.py](../course_scheduling/csv_cache.py): on-disk cache under `cache/`;
  per-subject CSV snapshots and the durable full-section memory file.
- [course_scheduling/full_course_memory.py](../course_scheduling/full_course_memory.py): YAML-backed
  per-term memory of which CRNs have been reported full; prevents duplicate "now full" emails when
  capacity stays the same.
- [course_scheduling/change_summary.py](../course_scheduling/change_summary.py): human-readable text
  builders for schedule diffs (when/where changes, enrollment changes).
- [course_scheduling/email_report.py](../course_scheduling/email_report.py): composes subject line and
  body for the change report; no transport logic.
- [course_scheduling/email_sender.py](../course_scheduling/email_sender.py): AppleScript transport via
  `Mail.app`; sends a report email with xlsx attachment to hardcoded recipients.
- [course_scheduling/report_pipeline.py](../course_scheduling/report_pipeline.py): end-to-end
  orchestration for one report run (load memory, detect changes, compose email, generate workbook, send,
  persist cache).
- [course_scheduling/report_scheduler.py](../course_scheduling/report_scheduler.py): sleep-loop
  scheduler; computes next run slot (Mon-Thu 8:03am, Fri 8:03am + 6:07pm), sleeps, then invokes
  a caller-supplied callback.

### Shared utilities

- [course_scheduling/course_label.py](../course_scheduling/course_label.py): label normalization and
  course-number extraction.
- [course_scheduling/lab_filter.py](../course_scheduling/lab_filter.py): heuristic lab-section
  detection (section letter, LAB/LEC tokens, Attributes field, whitelist).
- [course_scheduling/term_code.py](../course_scheduling/term_code.py): Banner term code -> human label
  (e.g. `202710` -> `Fall_2026`).
- [course_scheduling/output_naming.py](../course_scheduling/output_naming.py): builds descriptive xlsx
  filenames from active filter selections.

## Data flow

### HTML grid path (primary)

```text
build_grids_from_html.py
  |
  +--> workbook_builder.default_grid_configs()   # define preset tab matrix
  |
  +--> workbook_builder.build_term_workbook()
         |
         +--> banner_http                        # POST Banner form, save HTML to cache/
         |
         +--> for each GridConfig:
                |
                +--> banner_parser               # parse saved HTML -> course dicts
                |      |
                |      +--> html_tokens          # day/time normalization, meeting blocks
                |      +--> course_label         # normalize label, extract course number
                |      +--> lab_filter           # lab-section heuristic
                |      +--> course_filter        # FilterSpec predicate
                |      +--> enrollment_parse     # enrolled/capacity ratio
                |
                +--> crosslist_resolver          # merge cross-listed sections
                +--> html_courses               # expand to per-meeting grid rows
                +--> grid_model                 # build in-memory time-slot grid
                +--> xlsx_writer                # render grid to xlsx
                +--> parser_audit_tables        # write raw/debug tables
                +--> schedule_analysis_tables   # write policy-audit tables
         |
         +--> xlsx_merge                        # combine tabs into one workbook
  |
  output/<term>-merged-grid.xlsx
```

### CSV grid path

```text
tools/build_grid_from_csv.py
  |
  +--> cs_cli.build_filter_spec()   # parse argparse -> FilterSpec
  +--> csv_courses                  # read CSV, apply FilterSpec, expand rows
  +--> grid_model                   # build in-memory grid
  +--> xlsx_writer                  # render to xlsx
  |
  <output>.xlsx
```

### Email change-detection path

```text
tools/email_schedule_report.py  (--loop or one-shot)
  |
  +--> report_scheduler           # (--loop only) sleep until next slot
  +--> report_pipeline.run_report()
         |
         +--> csv_cache           # load cached CSVs from cache/
         +--> full_course_memory  # load durable YAML memory
         +--> change_detect       # download -> parse -> diff per subject
         |      |
         |      +--> banner_http + banner_parser
         |      +--> csv_diff
         |
         +--> change_summary      # build human-readable diff text
         +--> email_report        # compose subject + body
         +--> workbook_builder    # generate merged workbook in temp dir
         +--> email_sender        # AppleScript -> Mail.app -> send
         +--> csv_cache           # persist new snapshots
         +--> full_course_memory  # persist updated YAML memory
```

## Testing and verification

- `pytest tests/` runs the full fast suite (unit + integration); E2E tests are excluded.
- [tests/test_full_report_integration.py](../tests/test_full_report_integration.py): integration test
  covering the change-detect / email-report pipeline with fixture HTML.
- [tests/test_cli_filters.py](../tests/test_cli_filters.py): filter predicate unit tests.
- [tests/test_full_course_memory.py](../tests/test_full_course_memory.py): full-section memory logic.
- `tests/e2e/` holds non-browser E2E scripts run directly (not via pytest):
  - [tests/e2e/e2e_build_grids.py](../tests/e2e/e2e_build_grids.py): full HTML -> xlsx pipeline smoke.
- Repo-wide gates: `test_pyflakes_code_lint.py`, `test_function_typing.py`,
  `test_shebangs.py`, `test_ascii_compliance.py`, `test_markdown_links.py`,
  `test_import_requirements.py`, `test_indentation.py`.

## Extension points

- **New grid tab**: add a `GridConfig` to `workbook_builder.default_grid_configs()` with the desired
  `FilterSpec`.
- **New subject filter**: add a flag in `course_scheduling/cs_cli.py` using `add_subject_flags`.
- **New campus or level**: extend `FilterSpec` fields and `evaluate_class_inclusion` in
  `course_scheduling/course_filter.py`.
- **New color scheme**: adjust hue/lightness constants in
  `course_scheduling/schedule_colors.py`.
- **New analysis table**: add a writer module alongside
  `course_scheduling/schedule_analysis_tables.py` and call it from `workbook_builder`.
- **Non-Banner HTML source**: implement a new parser alongside `banner_parser.py` that produces the
  same course-dict schema; plug into `workbook_builder`.
- **Non-Mail.app transport**: replace `email_sender.py` with a SMTP or API module; the pipeline
  calls `email_sender.send_email()` as a single call site.

## Known gaps

- `course_scheduling/course_label.py` and `course_scheduling/schedule_time.py` were not fully
  read; their public API can be confirmed by reading each file.
- Email recipients are hardcoded in `email_sender.py`; no config file or argparse flag exposes them.
