# USAGE.md

How to run the course-schedule tools, CLI flags, and practical examples.

## Main workflows

### HTML workflow (build term workbook from Banner HTML)

Download course HTML for each subject, parse it, and write the merged
schedule-grid workbook for the term:

```bash
./build_grids_from_html.py -t 202710
```

Override the default subject set with repeatable `--subject` flags:

```bash
./build_grids_from_html.py -t 202710 --subject MATH --subject PSYC
```

The default subject set is `BIOL`, `PHYS`, `CHEM`, `BCHM`. The library is
subject-agnostic; the default lives only in the root entry point. This command always
builds the standard preset grid matrix (lower undergrad, full undergrad, 300-level,
graduate, Schaumburg, lab-only, raw table, all-courses); for custom campus, level, or
course-number filtering use `tools/build_grid_from_csv.py` instead.

### CSV workflow (build grid from a draft-schedule CSV)

Build a schedule grid from a CSV enrollment export without downloading
live HTML:

```bash
source source_me.sh && python3 tools/build_grid_from_csv.py \
    -i path/to/your_courses.csv \
    --biol --chem --phys --bchm --chicago \
    -n 100 -n 200 -n 300 \
    -o biol_undergrad_chicago.xlsx
```

Required input columns: `Meeting_Days`, `Begin_Time`, `End_Time`.
Label columns: `SUBJ_CRSE_SEC`, `SUBJ`, `CRSE`, `SEC`.
Rows whose `Course_Status` is not `Active` are skipped.

### Email report daemon (tmux)

Start the recurring schedule-change email daemon in a tmux session:

```bash
./run_email_tmux.sh
```

Attach to the running session:

```bash
tmux attach -t course_email
```

The daemon sends reports Mon-Thu at 8:03am and Fri at 8:03am and 6:07pm.
The term code is set in `run_email_tmux.sh` (`TERM_CODE` variable).

### Baseline priming

Prime the cache and full-section memory before a loop starts without composing
or sending email:

```bash
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 --prime
```

`./run_email_tmux.sh` runs that prime step by default before it starts the
daemon, so the first scheduled report is delta-only instead of a full initial
dump. To skip priming after downtime and retain accumulated changes for the
next report, start the launcher with `--no-prime`:

```bash
./run_email_tmux.sh --no-prime
```

## Advanced tools

### tools/email_schedule_report.py

Run a single report pass without the daemon:

```bash
# Dry run (detect changes, print output, do not send email):
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 -n

# Send the email immediately:
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 -e

# Run in loop mode (same schedule as the tmux daemon):
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 --loop
```

Flags:
- `-t / --term TERM_CODE`: Banner term code (required).
- `--subject SUBJ` (repeatable): subject codes to include; default `BIOL PHYS CHEM BCHM`.
- `-n / --dry-run`: detect changes and print; do not send email (default).
- `-e / --send-email`: send the email via Mail.app.
- `--loop`: run on the recurring schedule instead of once.
- `--prime`: fetch and persist a no-email baseline; cannot be combined with
  `--loop`.

### tools/build_grid_from_csv.py

Build a schedule grid from a CSV file:

```bash
source source_me.sh && python3 tools/build_grid_from_csv.py \
    -i <csv_file> [filter flags] [-o output.xlsx]
```

Flags:
- `-i / -f / --file INPUT`: path to the CSV file (required).
- `-o / --output OUTPUT`: explicit output path for the `.xlsx` file.
- Common filter flags (see below).

## Common filter flags

`./build_grids_from_html.py` accepts only `--subject SUBJ` (repeatable) to select which
subject codes are downloaded. The HTML command always runs the full preset grid matrix
(lower undergrad, full undergrad, 300-level, graduate, Schaumburg, lab-only, raw table,
all-courses) regardless of other flags; per-grid campus or level filters do not apply here.

`tools/build_grid_from_csv.py` accepts the full filter set:

- `--biol`, `--chem`, `--phys`, `--bchm`, `--math`: subject toggles.
- `-n 100`, `-n 200`, `-n 300`, `-n 400`: keep only the given course-number series (repeatable).
- `--undergrad`: keep only undergraduate-level sections (course number below 400).
- `--grad`: keep only graduate-level sections (course number 400 and above).
- `--chicago`: keep only Chicago campus sections.
- `--schaumburg`: keep only Schaumburg campus sections.
- `--lab-only`: keep likely lab sections using section suffix `B`, `LAB` token detection, and `LEC` exclusion.

## Output

Each build command writes one `.xlsx` schedule grid. When `-o` is omitted the
filename is derived from the active filters (subjects, levels, numbers, campus).

Grid layout:
- 15-minute time slots from 07:00 to 23:45 on each row.
- One column per day (`M`, `T`, `W`, `R`, `F`).
- Courses are placed in the column for their meeting day and merged vertically
  across their meeting time.
- Sections that run concurrently on the same day use additional side-by-side columns.

The workbook from `./build_grids_from_html.py` produces multiple tabs: lower
undergrad, full undergrad, 300-level, graduate, Schaumburg, lab-only, raw
parser table, and an all-courses sheet.

## Color scheme

- `BIOL` sections use shades of green.
- `PHYS` sections use shades of yellow.
- `CHEM` sections use shades of blue.
- `BCHM` sections use shades of violet.
- Colors darken with higher course level (100, 200, 300, 400).
- Sections over 80 percent enrolled are shaded orange.
- Waitlisted or closed sections (HTML source only) are shaded red.
- Tuesday and Thursday 12:15-13:15 common-hour slots are shaded light tan when empty.

## Full-course memory

Runtime state lives at the repo root and is gitignored: `cache/` (per-subject
snapshot CSVs and `full_course_memory.yaml`), `logs/`, and `output/` (generated
grids). `tools/email_schedule_report.py`
maintains a YAML snapshot at `cache/full_course_memory.yaml` to distinguish a
genuine capacity increase from a section that simply filled, lost a seat, and
refilled.

- YAML shape: `term -> {crn -> capacity}`.
- First run (new term): seeds silently with all currently full sections; no flood
  of "full" emails on the first run for a new term.
- Capacity-bump rule: if a section refills at the same capacity it is treated as
  noise. If capacity increased since last seen full, the email reports it again with
  a `(was full at PREV)` note.
- Waitlist toggles: changes to the `Waitlisted` enrollment column are treated as
  noise and do not generate "modified" email lines.
- Reset: delete `full_course_memory.yaml` to reset memory for all terms, or delete
  a single term key to reset only that term.

## Notes

- The HTML parser is layout-dependent and may need updates if the course-listing
  site markup changes.
- Multi-line "When / Where" entries are split into multiple meetings for the same
  section.
- The download path uses a sessioned GET plus POST to select subjects without
  PST variables; `error_500.html` is written in the current directory on server error.
- The HTML workflow downloads one subject per request and merges the results.
- Filenames produced by `./build_grids_from_html.py` include the term code; tabs are
  merged in fixed order and the raw-data tab is appended last.
