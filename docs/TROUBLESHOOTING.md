# Troubleshooting

Known issues, fixes, and debugging steps for the course-schedule tools.

## Email does not send

Symptom: `tools/email_schedule_report.py` runs without error but no email arrives.

Cause: The email path uses `py-applescript` to drive Mail.app on macOS. This requires:
- macOS with Mail.app installed and configured with at least one account.
- Accessibility permissions for the Python process (System Preferences >
  Privacy and Security > Automation).

Fix:
1. Verify Mail.app is open and the sending account is configured.
2. Run with `-n` (`--dry-run`) first to confirm change detection works without sending.
3. Check `logs/` for error output from the applescript transport layer.

Note: The email-send path is macOS-only. Linux and Windows are not supported for
this workflow.

## Grid is missing or empty

Symptom: `./build_grids_from_html.py` exits 0 but the workbook has no course cells.

Possible causes and fixes:

- **No matching sections after filtering.** Check the subject set
  (`--subject` flags) and the active term code (`-t TERM_CODE`).
- **HTML files not downloaded.** Check `cache/` for `.html` files. On a
  network error, `banner_http.py` writes `error_500.html` to the current
  directory. Re-run or fetch the HTML manually.
- **Term code wrong.** Banner term codes are six digits (for example `202710`
  for Spring 2027). A wrong term returns an empty results page.

## HTML parser produces no records

Symptom: `banner_parser.py` processes an HTML file but returns zero course dicts.

Cause: The Banner Course Finder page markup changed and the parser no longer
finds `courseResultsBox` div blocks or the expected `dataLabel`/`dataValue`
elements.

Fix: Compare the saved HTML against the pattern expected in
`course_scheduling/html_tokens.py` and update the selector logic.

## FileNotFoundError on start

Symptom: A script fails immediately with `FileNotFoundError`.

Cause: An input file path is wrong, or `cache/` / `output/` do not exist yet.

Fix: These directories are created on first run. If they are missing, run
`./build_grids_from_html.py -t <term>` once to initialize them, or create
the directories manually.

## Too many "section now full" emails on first run

Symptom: The email daemon fires notifications for every full section on its
first run for a new term.

Cause: The full-course memory file (`cache/full_course_memory.yaml`) is absent
for the new term, so all current full sections are treated as new events.

Fix: This is expected behavior on the very first run. The memory file is seeded
silently (no email sent) on first run; subsequent runs suppress already-known
full sections. Delete the yaml file or remove a term key to reset manually.

See [YAML_FILE_FORMAT.md](YAML_FILE_FORMAT.md) for reset instructions.

## pytest failures

For test-suite failures, see [PYTEST_STYLE.md](PYTEST_STYLE.md) for
triage guidance. Run the full suite with:

```bash
source source_me.sh && python3 -m pytest tests/
```

## source_me.sh not found

Symptom: `source source_me.sh` fails or `python3` uses the wrong interpreter.

Fix: Run all Python commands from the repo root where `source_me.sh` lives.
`source_me.sh` sets `PYTHONPATH` and selects the Homebrew Python 3.12
interpreter. See [INSTALL.md](INSTALL.md) for setup steps.
