# Usage

Build Excel course grids from live Banner HTML or a schedule CSV. The email command compares
current course data with its cache and can send only through the local macOS helper.

## Main workflows

### HTML workflow (build term workbook from Banner HTML)

Download course HTML for each subject, parse it, and write the merged
schedule-grid workbook for the term:

```bash
source source_me.sh && python3 build_grids_from_html.py -t 202710
```

Override the default subject set with repeatable `--subject` flags:

```bash
source source_me.sh && python3 build_grids_from_html.py \
    -t 202710 --subject MATH --subject PSYC
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

Build the helper, approve one foreground test message, and start the recurring daemon:

```bash
./build_course_finder_mailer.sh
source source_me.sh && python3 test_email_permission.py
./run_email_tmux.sh
```

Each new daemon launch also sends a plain startup test email to
`nvoss@roosevelt.edu` through `CourseFinderMailer.app`, the same stable native
helper used by scheduled reports. If macOS asks whether CourseFinderMailer may
control Mail, click **Allow**.
The scheduler starts only after the test message sends successfully; a denial
or Mail error leaves the daemon stopped so it cannot enter a failing restart
cycle.

The daemon runs as the short `cfmail` session on the normal tmux server, so it appears in
plain `tmux ls` output. Mail authorization belongs to the helper app, not Terminal, Python,
SSH, or tmux process ancestry. Keep the generated app at the repository root. Rebuilding it
changes its local ad-hoc signature and may require approving Automation again.

Run the same helper transport without starting the daemon:

```bash
source source_me.sh && python3 test_email_permission.py
```

The helper has a stable application identity, so this manual test and scheduled reports use
the same Automation grant. If the request is denied, open **System Settings > Privacy &
Security > Automation** and allow CourseFinderMailer to control Mail. No prompt plus a
delivered startup email means that grant is already active. When consent is undecided, the
helper shows a status window before it asks macOS to display the system prompt.

If the older default-socket daemon is still running, stop it once before using
the short session name:

```bash
tmux kill-session -t course_email
./run_email_tmux.sh
```

The launcher also refuses to start a duplicate if a previous isolated `cfmail` server or the
`course_email_daemon` server is still running. Follow the removal command it prints before
relaunching.

Attach to the running session:

```bash
tmux attach -t cfmail
```

The abbreviated equivalent is `tmux a -t cfmail`.

The daemon sends reports Mon-Thu at 8:03am and Fri at 8:03am and 6:07pm. Its term code is the
`TERM_CODE` value in `run_email_tmux.sh`. The tmux supervisor restarts an unexpectedly exited
scheduler; it repeats the real test email before starting each replacement scheduler process.
Report generation and the native Mail helper remain short-lived processes.

Runtime activity and errors go to `logs/email_schedule_report.log`, including retries,
failures, startup-test results, and supervisor restarts. The log rotates at 5 MB and keeps
three numbered backups.

### Refreshing the baseline

Refresh the cache and full-section memory before a loop starts without
composing or sending email:

```bash
source source_me.sh && python3 tools/email_schedule_report.py \
	-t 202710 --refresh-baseline
```

`./run_email_tmux.sh` refreshes the baseline by default before its scheduler loop, so the
first scheduled report is delta-only instead of a full initial dump. To preserve changes
accumulated during downtime for the next report, skip that refresh:

```bash
./run_email_tmux.sh --skip-baseline-refresh
```

Transient network failures and HTTP 408, 429, 500, 502, 503, and 504 responses retry with a
fresh session and bounded backoff. If baseline refresh fails, the supervisor preserves the
existing cache, logs a warning, and enters the scheduler loop. `--prime` and `--no-prime`
remain accepted aliases.

An unavailable subject does not suppress changes from successful subjects. A run with no
meaningful changes sends no email. If another subject changes, the email names the unavailable
subject, its attachment omits that subject, and its prior cache and full-course memory remain
untouched. Baseline refresh is all-or-nothing.

## Advanced tools

### tools/email_schedule_report.py

Run a single report pass without the daemon:

```bash
# Normal report (dry-run is the default: detect changes, log email text, do not send):
source source_me.sh && python3 tools/email_schedule_report.py -t 202710

# Explicit dry run (same behavior as the default):
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 -n

# Send a report immediately when there are meaningful changes:
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 -e

# Run in loop mode (same schedule as the tmux daemon):
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 --loop
```

Flags:
- `-t / --term TERM_CODE`: Banner term code (required).
- `--subject SUBJ` (repeatable): subject codes to include; default `BIOL PHYS CHEM BCHM`.
- `-n / --dry-run`: detect changes and log the report; do not build an attachment or send
  email. This is the default.
- `-e / --send-email`: send the email via Mail.app.
- `--loop`: run on the recurring schedule instead of once.
- `--refresh-baseline`: fetch and persist a no-email starting snapshot; cannot
  be combined with `--loop`. `--prime` is retained as an alias.

### Mail.app startup test

Send one plain email to `nvoss@roosevelt.edu` through the same
CourseFinderMailer and Mail.app transport used by scheduled reports:

```bash
source source_me.sh && python3 test_email_permission.py
```

Use this command to request or verify the helper's Automation permission
without downloading course data, changing caches, or starting the daemon. Run
`./build_course_finder_mailer.sh` first if the generated app is absent.

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

## Inputs and outputs

- The HTML command downloads one Banner page for each selected subject and writes dated merged
  workbooks in `output/`, with a semester-label copy. It also creates preset per-grid and audit
  workbooks.
- The CSV command reads a draft-schedule CSV. It requires `Meeting_Days`, `Begin_Time`, and
  `End_Time`; `SUBJ_CRSE_SEC`, `SUBJ`, `CRSE`, and `SEC` label rows. Inactive rows are skipped.
- A CSV grid writes to `-o OUTPUT` or a filter-derived `.xlsx` filename in the current directory.
- Email state is gitignored at the repo root: `cache/` holds snapshot CSVs and
  `full_course_memory.yaml`; generated attachments go to `output/`; logs go to `logs/`.

Each grid workbook uses this layout:

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
  a sentence stating the capacity at which it was previously reported full.
- Waitlist toggles: changes to the `Waitlisted` enrollment column are treated as
  noise and do not generate "modified" email lines.
- Reset: delete `full_course_memory.yaml` to reset memory for all terms, or delete
  a single term key to reset only that term.

## Notes

- The HTML parser is layout-dependent and may need updates if the course-listing site markup
  changes.
- Multi-line "When / Where" entries are split into multiple meetings for the same
  section.
- The download path uses a sessioned GET plus POST to select subjects without PST variables.
  A final HTTP error response is written to `error_500.html`; connection and timeout failures
  have no response body and are recorded only in the report log.
- The HTML workflow downloads one subject per request and merges the results.
- Filenames produced by `./build_grids_from_html.py` include the term code; tabs are
  merged in fixed order and the raw-data tab is appended last.
