# Release history

Organized log of released versions and their release dates.

## v26.09 - Unreleased

### Highlights

- Added the native `CourseFinderMailer` helper for Mail delivery. It accepts
  private, bounded requests, sends only to the established recipients, and
  accepts generated xlsx attachments only from `output/`.
- The email daemon now runs a startup delivery and Mail-authorization test
  before scheduling. Its normal tmux session is `cfmail`, which is visible in
  `tmux ls` and can be attached with `tmux a -t cfmail`.
- Mail authorization now belongs to the locally signed helper instead of the
  Python process. It uses LaunchServices and typed AppleScript handler
  arguments, avoiding dynamic script-source interpolation.

### Notable fixes

- Failed startup authorization stops the daemon rather than leaving a scheduler
  running that cannot deliver email.
- Replaced the launcher's fixed-delay readiness check with an explicit
  supervisor result, and give every launch a private status directory to prevent
  stale status files from passing the gate.
- Removed the unused `py-applescript` dependency and stopped logging complete
  AppleScript source that could contain message bodies.

### Compatibility notes

- On the first launch, macOS may ask for `CourseFinderMailer` permission to
  automate Mail. Approve that prompt before scheduled reports can send email.
- The launcher recognizes prior isolated `cfmail` and `course_email_daemon`
  sessions during migration, preventing a second scheduler from starting.

### Validation

- Added an offline request-boundary test for rejected arbitrary recipients;
  actual Mail delivery and TCC consent remain manual macOS acceptance checks.
- Verified the fast suite, native build, shell syntax, plist, signature, lint,
  and whitespace checks after the final audit fixes.

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
