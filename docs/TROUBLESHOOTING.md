# Troubleshooting

Known symptoms, causes, and fixes for the course-schedule tools.

## Mail helper is missing

Symptom: A mail command reports `CourseFinderMailer.app is missing` or the
tmux launcher says that the app is missing or not executable.

Cause: The native `CourseFinderMailer.app` is a local build output at the
repository root. It is not present until it is built.

Fix: Build the helper, then run its permission test:

```bash
./build_course_finder_mailer.sh
source source_me.sh && python3 test_email_permission.py
```

See [INSTALL.md](INSTALL.md) for the macOS, Swift, and Mail.app requirements.

## Mail Automation is denied

Symptom: `test_email_permission.py` or `run_email_tmux.sh` reports that the
startup test failed. The log can contain `Not authorized to send Apple events
to Mail. (-1743)` or a CourseFinderMailer Automation-permission error.

Cause: macOS TCC has not allowed `CourseFinderMailer` to control Mail.app.
Permission belongs to the helper app, rather than to Terminal, Python, SSH, or
tmux. The launcher stops before scheduling when this test fails.

Fix:

1. Confirm that Mail.app has a configured sending account.
2. Run `source source_me.sh && python3 test_email_permission.py` in a logged-in
   macOS desktop session.
3. When macOS asks, allow CourseFinderMailer to control Mail.
4. If no prompt appears, open **System Settings > Privacy & Security >
   Automation** and allow CourseFinderMailer to control Mail.
5. Run `./run_email_tmux.sh` again. It sends its own startup test before the
   scheduler begins.

When consent is undecided, the helper shows a small status window before the
system prompt. Already-approved sends keep that helper window hidden. Check
`logs/email_schedule_report.log` for the recorded helper error and startup
result.

## Mail helper times out

Symptom: The log says `CourseFinderMailer timed out.` and the daemon does not
start.

Cause: The helper did not return its explicit Mail result within its bounded
wait. A daemon startup test fails closed, so it does not leave a scheduler
running that cannot send reports.

Fix: Run the direct test from the repo root and complete any visible macOS or
Mail.app action:

```bash
source source_me.sh && python3 test_email_permission.py
```

Confirm the Mail.app account and Automation setting described above, then
rerun `./run_email_tmux.sh`. Use the log entry as the diagnostic record; the
test does not download courses, change caches, or start the scheduler.

## Helper was rebuilt

Symptom: A previously working mail test now prompts again or is denied after
running `./build_course_finder_mailer.sh`.

Cause: Rebuilding changes the helper's local ad-hoc signature, so macOS can
require a new Automation approval.

Fix: Run `source source_me.sh && python3 test_email_permission.py`, approve
CourseFinderMailer again, and then relaunch the daemon. Do not grant the
permission to a different process as a substitute; scheduled reports use the
helper app identity.

## Daemon is not visible

Symptom: The email daemon is expected to run, but it does not appear in plain
`tmux ls` output.

Cause: The current launcher uses the normal tmux server and the session name
`cfmail`. Older launchers also used a default-server `course_email` session or
an isolated tmux server.

Fix: Start and inspect the current daemon with:

```bash
./run_email_tmux.sh
tmux ls
tmux attach -t cfmail
```

`tmux a -t cfmail` is the equivalent abbreviated attach command. The launcher
reports success only after the helper's startup test completes.

## A legacy daemon exists

Symptom: `run_email_tmux.sh` refuses to start and reports a legacy session or
an isolated tmux server.

Cause: Starting another scheduler could send duplicate reports. The launcher
detects the old default-server `course_email` session and the briefly used
isolated-server names `cfmail` and `course_email_daemon`.

Fix: Use the removal command printed by the launcher, then rerun it. For the
old default-server session, the command is:

```bash
tmux kill-session -t course_email
```

For an isolated server, verify the named daemon is the one to remove and use
the command printed by the launcher, such as `tmux -L cfmail kill-server` or
`tmux -L course_email_daemon kill-session -t course_email`.

## Course server error

Symptom: A download reports an HTTP status or writes `error_500.html`.

Cause: Banner returned an upstream HTTP response instead of course-result
HTML. An Oracle-branded page is an upstream Banner or database response.

Fix: The downloader retries connection failures, timeouts, and HTTP 408, 429,
500, 502, 503, and 504 with a fresh session and bounded backoff. A final HTTP
response of 400 or greater is written to `error_500.html`; connection and
timeout failures have no response body to save. Re-run after the upstream
service recovers and inspect `logs/email_schedule_report.log` for attempts.

During a report, an unavailable subject does not suppress meaningful changes
from successful subjects. If no subject changed, no email is sent and the
outage remains in the log. If another subject changed, the email identifies the
unavailable subject and its attachment omits it; its cache and full-section
memory remain untouched.

A baseline refresh is all-or-nothing. An exhausted response preserves the
existing baseline, but the supervisor logs the failure and continues into its
scheduler loop. A failed scheduled child likewise does not permanently stop
the supervised loop.

## Grid is missing or empty

Symptom: `./build_grids_from_html.py` exits zero but the workbook has no course
cells.

Possible causes and fixes:

- **No matching sections:** Check the `--subject` flags and active `-t TERM_CODE`.
- **HTML was not downloaded:** Check `cache/` for HTML input, inspect the log,
  and resolve any Banner error before rerunning.
- **Wrong term code:** Banner term codes use six digits, for example `202710`
  for Spring 2027. A wrong term can return an empty results page.

## HTML parser has no records

Symptom: `banner_parser.py` processes an HTML file but returns zero course
records.

Cause: Banner markup changed and no longer contains the expected
`courseResultsBox`, `dataLabel`, or `dataValue` elements.

Fix: Compare the saved response with the tokens in
`course_scheduling/html_tokens.py`, then update the parser selectors.

## File path is missing

Symptom: A script fails immediately with `FileNotFoundError`.

Cause: An input path is wrong, or runtime directories have not been created.

Fix: Run `./build_grids_from_html.py -t <term>` once to create `cache/` and
`output/`, or create those directories before invoking a command that needs
them. For a missing saved HTML input, correct the path or download it again.

## Full-section notices repeat

Symptom: The first report for a new term appears to notify about every already
full section.

Cause: `cache/full_course_memory.yaml` has no memory for that term.

Fix: The first normal run seeds full-section memory silently, so it does not
send that initial flood. Later runs suppress a section that refills at the same
capacity. To deliberately reset memory, remove the YAML file or only the term
key; see [YAML_FILE_FORMAT.md](YAML_FILE_FORMAT.md).

## pytest failures

Run the fast suite from the repository root:

```bash
source source_me.sh && python3 -m pytest tests/
```

See [PYTEST_STYLE.md](PYTEST_STYLE.md) for failure triage guidance.

## source_me.sh is unavailable

Symptom: `source source_me.sh` fails, or the active `python3` is not Python
3.12.

Cause: The command is not being run from the repository root, or the required
Homebrew Python installation is absent.

Fix: Change to the repository root before sourcing the file. `source_me.sh`
requires bash, loads local shell setup, and sets the Python runtime flags; it
does not select an interpreter or set `PYTHONPATH`. Install Python 3.12 as
described in [INSTALL.md](INSTALL.md), then verify with `python3 --version`.
