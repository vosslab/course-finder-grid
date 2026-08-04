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

## Course server error

Symptom: A download reports HTTP 500 or writes `error_500.html`.

Cause: The external course server returned a transient error or is unavailable.
An Oracle-branded error page is an upstream Banner/database response rather
than course-result HTML.

Fix: The downloader retries transient network failures and HTTP 408, 429, 500,
502, 503, and 504 responses with a fresh session and bounded backoff. After an
HTTP 5xx response, and after bounded retries when the status is retryable, the
report continues with the subjects that succeeded. A run with zero meaningful
course changes sends no email; the failure remains in the report log. When a
successful subject has a meaningful change, the email and attachment use those
successful downloads and state that the failed subject's data is unavailable.
Its prior cache and full-section memory remain untouched.

A baseline refresh remains all-or-nothing: an exhausted response stops the
refresh without replacing the existing baseline, but the failure does not stop
the daemon. A scheduled report child or scheduler failure also does not
permanently stop the supervised loop. The terminal failure and traceback are
retained in `logs/email_schedule_report.log`. A final HTTP error response is
also saved to `error_500.html`; connection and timeout failures have no
response body to save. While BCHM continues to return the reported server
error, creation or replacement of `error_500.html` is expected program output,
not a hand-authored input file.

## Grid is missing or empty

Symptom: `./build_grids_from_html.py` exits 0 but the workbook has no course cells.

Possible causes and fixes:

- **No matching sections after filtering.** Check the subject set
  (`--subject` flags) and the active term code (`-t TERM_CODE`).
- **HTML files not downloaded.** Check `cache/` for `.html` files. A final HTTP
  error response is saved to `error_500.html`; connection and timeout failures
  are recorded in `logs/email_schedule_report.log`. Re-run or fetch the HTML
  manually.
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
