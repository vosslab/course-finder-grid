# File formats

Input and output file formats for the course-schedule tools.

## Inputs

### Banner HTML (HTML workflow)

Source: Banner Course Finder search results, one file per subject code per term.

- Produced by `course_scheduling/banner_http.py` (`download_subject`), saved to `cache/`.
- Parsed by `course_scheduling/banner_parser.py` using `lxml`; extracts
  `courseResultsBox` div blocks.
- One HTML file covers all sections for one subject in one term.
- The parser is layout-dependent; markup changes on the Banner site may require
  updates to `course_scheduling/html_tokens.py`.

### CSV enrollment export (CSV workflow)

Source: draft-schedule spreadsheets exported from Banner or a compatible system.

Required columns (rows missing any of these are skipped):

| Column | Description |
| --- | --- |
| `Meeting_Days` | Day tokens, for example `MWF`, `TR`, `M` |
| `Begin_Time` | Four-digit 24-hour time, for example `0800`, `1315` |
| `End_Time` | Four-digit 24-hour time, for example `0850`, `1415` |
| `Course_Status` | Only rows with value `Active` are included |

Label columns (used for grid cell text and filtering):

| Column | Description |
| --- | --- |
| `SUBJ_CRSE_SEC` | Full label, for example `BIOL 201-01` |
| `SUBJ` | Subject code, for example `BIOL` |
| `CRSE` | Course number, for example `201` |
| `SEC` | Section code, for example `01` |
| `Title` | Course title |
| `Enrolled` | Enrollment string, for example `19 / 24` (enrolled / capacity) |
| `CRN` | Course reference number |

Expected input location: place a user-supplied CSV with these columns under
`data/` (for example `data/spring_2026_sample_courses.csv`); no sample CSV ships
with the repository.

---

## Outputs

### Merged term workbook (HTML workflow primary output)

Path: `output/<term_code>_schedule_grid-<run_date>.xlsx`, with a semester-label
copy at `output/<term_label>_schedule_grid-<run_date>.xlsx` (`run_date` is the
build date formatted `YYYY_MM_DD`).

A single Excel workbook with 9 tabs, one per preset grid configuration:

| Tab source file | Filter description |
| --- | --- |
| `lower_undergrad_<term>-grid.xlsx` | Chicago campus, undergrad, 100/200-level |
| `undergrad_level_<term>-grid.xlsx` | Chicago campus, all undergrad levels |
| `300_level_undergrad_<term>-grid.xlsx` | All campuses, undergrad 300-level |
| `graduate_level_<term>-grid.xlsx` | Graduate level |
| `schaumburg_<term>-grid.xlsx` | Schaumburg campus, all levels |
| `lab_chicago_<term>-grid.xlsx` | Lab sections, Chicago campus |
| `lab_schaumburg_<term>-grid.xlsx` | Lab sections, Schaumburg campus |
| `all_courses_in_dept_<term>-grid.xlsx` | All courses, no filter |
| `raw_table_<term>-grid.xlsx` | Raw parser output table |

Grid layout in each tab:

- Rows: 15-minute time slots from 07:00 to 23:45.
- Columns: one per weekday (`M`, `T`, `W`, `R`, `F`); concurrent sections add side-by-side columns.
- Cells are vertically merged across the course meeting duration.
- Colors indicate subject (green = BIOL, yellow = PHYS, blue = CHEM, violet = BCHM),
  darken with course level, and switch to orange (>80 % enrolled) or red (waitlisted/closed).
- Tuesday and Thursday 12:15-13:15 common-hour blocks are shaded light tan when empty.

### Standalone analysis tables (HTML workflow)

Written alongside the merged workbook:

| File | Contents |
| --- | --- |
| `all_courses_in_dept_<term>-common_hour.xlsx` | Common-hour conflict summary |
| `all_courses_in_dept_<term>-timeblock.xlsx` | Non-standard timeblock summary |

### Single grid (CSV workflow)

Path: specified by `-o`; derived from active filters when omitted.

Same layout as a single tab from the merged workbook.

### Raw and debug tables

| File | When produced | Contents |
| --- | --- | --- |
| `raw_table_<term>-grid.xlsx` | HTML workflow | All parsed rows before filtering |
| `<subject>_lab_debug_<term>.csv` | HTML workflow | Lab-section filter debug rows |

### Cache snapshots (email path)

Path: `cache/<term>/<subject>_<term>.csv`

Per-subject CSV snapshots written after each download; used as the "before" state for
change detection on the next run. Format mirrors the CSV enrollment export columns above.

### Full-course memory (email path)

Path: `cache/full_course_memory.yaml`

See [YAML_FILE_FORMAT.md](YAML_FILE_FORMAT.md) for the schema and semantics.

---

## Notes

- `cache/`, `logs/`, and `output/` are gitignored; they are created on first run.
- The merged workbook filename pattern is `<term_code>_schedule_grid-<run_date>.xlsx`,
  with a `<term_label>_schedule_grid-<run_date>.xlsx` copy alongside it.
- For flag details and workflow examples, see [USAGE.md](USAGE.md).
