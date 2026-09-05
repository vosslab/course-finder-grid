# File formats

Input, runtime-state, and output formats for the course-schedule tools.

## CSV input

`tools/build_grid_from_csv.py` reads a draft-schedule CSV with Python's
`csv.DictReader`. The file is opened as UTF-8 with CSV newline handling.

The header must contain these columns. An empty file is accepted as zero rows;
a non-empty file missing one of these headers raises `ValueError`.

| Column | Accepted value | Use |
| --- | --- | --- |
| `Meeting_Days` | Non-empty day-token string, such as `MWF` or `TR` | Split into one grid column per character |
| `Begin_Time` | Numeric military time, such as `0800` or `1315.0` | Start time; rows before 06:00 are excluded |
| `End_Time` | Numeric military time, such as `0850` or `1415.0` | End time |

Each retained row must also meet these row-level rules:

- `Course_Status` must equal `Active`. A missing or other value excludes the row.
- Supply `SUBJ`, `CRSE`, and `SEC`, or a parseable `SUBJ_CRSE_SEC` label such
  as `BIOL 201-01`. Rows without a complete course identity are excluded.
- `Level` and `Campus_Desc` are optional source columns used only when the
  selected filters need them.
- Other columns, including `Title`, `Enrolled`, and `CRN`, are not required by
  this grid-input path.

Place a user-supplied source file wherever convenient; `data/` is the customary
location. No sample CSV ships with the repository. See [USAGE.md](USAGE.md) for
the CSV command and filter flags.

## Banner HTML

The HTML workflow fetches the Roosevelt Banner Course Finder search page and
posts the `FIND COURSES` form for one subject at a time. The request includes a
term code and one repeated `SUBJ` value; the remaining form fields select the
unrestricted Banner search values.

- A successful response is UTF-8 HTML. The batch workflow temporarily writes
  it as `output/course_finder_<term_code>_<subject>.html`; these files are
  removed after the workbook is finalized.
- The email workflow instead writes its HTML and intermediate CSV in a private
  temporary directory. Neither workflow uses `cache/` for HTML pages.
- `banner_parser.py` uses `lxml` and expects Banner `courseResultsBox` blocks
  with labeled values such as `Class`, `When / Where`, and `Enrolled`.
- A final HTTP response with status 400 or higher is written as
  `error_500.html` in the process working directory before the request fails.
  Connection and timeout failures have no saved response body.

The parser is intentionally coupled to the Banner result markup. A Banner
layout change requires parser and token-normalization work, not a CSV fallback.

## Cache CSVs

The change-report workflow persists one raw-parser snapshot per subject:

```text
cache/<subject>_<term_code>.csv
```

For example, `cache/BIOL_202710.csv` is the prior BIOL snapshot for term
`202710`. A missing snapshot makes the next successful download a changed
baseline. Cache files are gitignored.

These are not draft-schedule CSVs and do not mirror the CSV input schema. They
are CSV audit rows in this first-seen column order:

```text
Source_File, Class_Raw, Label, CRN, Subject, Course_Number, Section, Title,
Instructor, When_Where, Enrolled, Enrollment_Ratio, Attributes,
Cross_Listed_With, Campus, Level, Meetings_Count, Waitlisted, Whitelist_Key,
Whitelist_Lab_Course, Section_Is_B_Lab, Has_LAB_Token, Has_LEC_Token,
Has_Lab_Attribute, Potential_False_Negative, Lab_Probable, Lab_Reason,
Included_By_Current_Filters, Exclusion_Reason
```

The parser writes values as CSV cells; absent values become empty cells and
boolean audit values use their Python text form. Change reporting compares the
whole snapshot, while only selected source fields become human-facing email
changes.

## Excel workbooks

All `.xlsx` outputs are Excel Open XML workbooks written with `openpyxl`.

### Merged HTML workbook

The HTML command produces these retained files:

```text
output/<term_code>_schedule_grid-<YYYY_MM_DD>.xlsx
output/<term_label>_schedule_grid-<YYYY_MM_DD>.xlsx
```

When the term label differs from the term code, the second file is a byte copy
of the first and is the path printed by the command. The merged workbook has
one tab for each generated intermediate below; tab names are derived from the
intermediate basename and truncated to Excel's 31-character limit.

| Intermediate basename | Selection |
| --- | --- |
| `lower_undergrad_<term>-grid.xlsx` | Chicago 100/200-level courses |
| `undergrad_level_<term>-grid.xlsx` | Chicago undergraduate 100/200/300 courses |
| `300_level_undergrad_<term>-grid.xlsx` | All-campus undergraduate 300-level courses |
| `graduate_level_<term>-grid.xlsx` | Graduate courses |
| `schaumburg_<term>-grid.xlsx` | Schaumburg courses |
| `lab_chicago_<term>-grid.xlsx` | Chicago lab courses |
| `lab_schaumburg_<term>-grid.xlsx` | Schaumburg lab courses |
| `raw_table_<term>-grid.xlsx` | Unfiltered raw parser audit table |
| `all_courses_in_dept_<term>-grid.xlsx` | Unfiltered schedule grid |

The intermediate workbooks are deleted after merging. Schedule tabs use
15-minute slots from 07:00 through 23:45 and weekday columns `M`, `T`, `W`,
`R`, and `F`; overlapping meetings add side-by-side columns. Course cells are
merged over their duration. The raw audit tab uses the cache-snapshot columns
above with worksheet name `raw_data` before merge-time renaming.

The CSV command writes one schedule workbook to `-o`, or to a filter-derived
filename in the current directory when `-o` is omitted.

### Retained audit outputs

The HTML workflow retains these files in `output/`:

| Path | Worksheet | Contents |
| --- | --- | --- |
| `all_courses_in_dept_<term>-common_hour.xlsx` | `common_hour_conflicts` | Meetings that partially overlap the T/R common hour |
| `all_courses_in_dept_<term>-timeblock.xlsx` | `nonstandard_timeblocks` | Meetings whose start is not an official time block |
| `lab_courses_<term>_debug.csv` | N/A | Lab-filter audit rows |

Both analysis workbooks have columns `Label`, `Days`, `Start`, `End`, and
`Room`; if there are no rows, their sheets are empty. The debug CSV column
order follows the parser's first-seen lab-audit fields.

## Mail-helper JSON

`email_sender.py` writes a private, versioned JSON request in a temporary
directory and launches `CourseFinderMailer.app`. The helper writes the sibling
result at `request.json.result.json`. These files are short-lived and are not
user input or durable application state.

```json
{
  "version": 1,
  "recipients": ["nvoss@roosevelt.edu"],
  "subject": "text without line breaks",
  "body": "message text",
  "attachment_path": null
}
```

- `version` is the integer `1`.
- `recipients` is a non-empty, duplicate-free list limited to the two
  application-approved report addresses.
- `subject` is non-empty, contains neither line breaks nor NUL, and is at most
  512 UTF-8 bytes.
- `body` contains no NUL and is at most 1,000,000 UTF-8 bytes.
- `attachment_path` is a string or `null`. A string must resolve to a regular
  `.xlsx` file directly inside repo-root `output/` and be no larger than
  50,000,000 bytes.

The helper result is a JSON object with `status` (`sent` or `failed`). A
successful Swift response may omit `error` or set it to null; a failed response
includes error text. Python accepts only `status: "sent"` with no error value
and rejects results larger than 16,384 bytes.

## YAML state

`cache/full_course_memory.yaml` is a separate durable full-section-memory
contract. Its schema and reset semantics are owned by
[YAML_FILE_FORMAT.md](YAML_FILE_FORMAT.md).

## Related docs

- [USAGE.md](USAGE.md): commands and workflow examples.
- [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md): component ownership and data flow.
- [YAML_FILE_FORMAT.md](YAML_FILE_FORMAT.md): full-course memory YAML schema.
