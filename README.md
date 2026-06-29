# Course Schedule Email Reporter

Generates color-coded weekly schedule grids as Excel workbooks from course-listing HTML pages or CSV enrollment exports; lays sections on 15-minute time slots with subject and level colors; and emails enrollment-change reports on a tmux schedule.

## Quick start

Build the merged term schedule-grid workbook from live course HTML:

```bash
./build_grids_from_html.py -t 202710
```

Run the scheduled email daemon in a tmux session:

```bash
./run_email_tmux.sh
```

Attach to the running session:

```bash
tmux attach -t course_email
```

The daemon sends schedule reports Mon-Thu at 8:03am and Fri at 8:03am and 6:07pm.

Subjects default to `BIOL`, `PHYS`, `CHEM`, `BCHM`. Pass `--subject MATH` (repeatable) to
run a different department's subjects instead. This command always builds the standard
preset grid matrix (lower undergrad, full undergrad, 300-level, graduate, Schaumburg,
lab-only, raw table, all-courses); use `tools/build_grid_from_csv.py` for custom
campus, level, or course-number filtering.

## Tools / Advanced

Run a single change-detection report once (dry run, no email sent):

```bash
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 -n
```

Send the report email immediately (one-shot, not in loop mode):

```bash
source source_me.sh && python3 tools/email_schedule_report.py -t 202710 -e
```

Build a schedule grid from a CSV enrollment export:

```bash
source source_me.sh && python3 tools/build_grid_from_csv.py \
    -i path/to/your_courses.csv \
    --biol --chem --phys --bchm --chicago \
    -n 100 -n 200 -n 300 \
    -o biol_undergrad_chicago.xlsx
```

## Common filter flags

`./build_grids_from_html.py` accepts `--subject SUBJ` (repeatable) to control which
subject codes are downloaded; default is `BIOL PHYS CHEM BCHM`. The HTML command always
runs the full preset grid matrix regardless of other flags.

`tools/build_grid_from_csv.py` accepts the full filter set:

- `--biol`, `--chem`, `--phys`, `--bchm`, `--math`: subject toggles.
- `-n 100`, `-n 200`, `-n 300`, `-n 400`: keep only the given course-number series (repeatable).
- `--undergrad`, `--grad`: filter by level.
- `--chicago`, `--schaumburg`: filter by campus.
- `--lab-only`: keep likely lab sections only.
- `-o OUTPUT`: explicit output path for the `.xlsx` file.

## Documentation

- [docs/USAGE.md](docs/USAGE.md): CLI flags, workflows, output locations, and color scheme.
- [docs/AUTHORS.md](docs/AUTHORS.md): project maintainers and contributors.
- [docs/CHANGELOG.md](docs/CHANGELOG.md): chronological record of changes.
