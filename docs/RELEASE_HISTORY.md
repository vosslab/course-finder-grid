# Release history

Organized log of released versions and their release dates.

## 26.06 (2026-06-29)

Initial structured release under CalVer (`YY.MM`).

### Summary

- Complete package restructure: `course_scheduling/` is now a pure-code Python
  package; runtime state (`cache/`, `logs/`, `output/`) lives at repo root and is
  gitignored.
- Two root entry points: `build_grids_from_html.py` (HTML preset matrix) and
  `run_email_tmux.sh` (tmux email daemon).
- Dropped pandas from the runtime path; grid and analysis output now use `csv`,
  `datetime`, and `openpyxl` only.
- Merged workbook is 9 tabs; common-hour and timeblock analysis tables are written
  as standalone xlsx files.
- Preset grid matrix: lower undergrad, full undergrad, 300-level, graduate,
  Schaumburg, lab_chicago, lab_schaumburg, raw table, all-courses.
- Full-course memory persisted as `cache/full_course_memory.yaml`; prevents
  false-positive "now full" emails.
- 834 pytest tests pass; pyflakes clean.

### Known gaps

- Release notes for versions prior to 26.06 were not recorded.
- Add future entries under a new `## YY.MM` heading when a new version ships.
