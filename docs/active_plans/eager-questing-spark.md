# Fix the daemon Dock icon and add a baseline flush on loop start

## Context

Two related problems with the `--loop` email schedule daemon (started via
`run_email_tmux.sh` in a detached tmux session):

Problem 1 - persistent Dock icon. The daemon shows a Python icon in the macOS Dock
the entire time it runs, even while it is only sleeping between scheduled slots. The
old, retired loop (`~/nsh/junk-drawer/course_scheduling/email_schedule_loop.py`)
never did this.

Problem 2 - giant first email. Starting the loop from a clean state makes the very
first scheduled run report everything as a change, producing a huge email. Root
cause is the byte-level diff, not the full-section memory: full-section memory
already seeds silently on a first run (`course_scheduling/change_detect.py:53-56`),
but with no cached snapshot CSV the row diff (`diff_rows`) reports every section as
"added" (`change_detect.py:158-163`), which flags the subject as meaningfully
changed and floods the email. The user wants to flush/prime the baseline on loop
start so the first real email is delta-only.

Root cause is an architecture regression, not a missing flag:

- The old loop process imported only stdlib (`os, sys, time, datetime, subprocess`)
  and ran the report+email as a short-lived **subprocess**. The PyObjC-backed
  `applescript` package only loaded inside that transient child, which sent the
  mail and exited within seconds, so nothing persistent ever registered with the
  window server.
- The new loop runs the report **in-process**. `tools/email_schedule_report.py:16`
  imports `course_scheduling.report_pipeline` at module top, which at
  `course_scheduling/report_pipeline.py:20` imports `course_scheduling.email_sender`,
  which at `course_scheduling/email_sender.py:9` does `import applescript`
  (py-applescript, PyObjC/Foundation). In `--loop` mode this pulls PyObjC into the
  long-lived daemon at startup, and running the AppleScript (`activate`,
  `scpt.run()`) in that same persistent process flips it into a GUI app with a
  Dock icon that never goes away.

Intended outcome: the recurring daemon becomes a true background process with no
Dock icon, matching the old proven behavior, while still sending mail correctly at
each scheduled slot.

## Objectives

- The `--loop` daemon process never imports `applescript` / PyObjC and never runs
  AppleScript in-process.
- Each scheduled fire performs the full report+send in a short-lived child process
  that exits after sending, so any GUI/window-server registration dies with it.
- No persistent Python Dock icon while the daemon sleeps or runs; scheduled emails
  still send.
- Single-shot mode (`email_schedule_report.py -t ... -e`, no `--loop`) keeps working
  unchanged.
- A baseline flush (prime) populates the cache snapshot CSVs and full-section memory
  for all subjects without sending email, so the first scheduled email after start
  is delta-only, not a full dump.
- The launcher primes by default; an opt-out flag (`--no-prime`) skips priming so a
  restart can still report changes that accumulated while the loop was down.

## Design philosophy

Fix the design, not the symptom (per `docs/REPO_STYLE.md` core philosophies). The
durable fix restores the old subprocess-isolation boundary: the long-lived
scheduler carries no GUI-framework code, and every AppleScript execution lives in a
transient child. The rejected alternative is hiding the icon in-process by importing
AppKit and calling `setActivationPolicy_` (LSUIElement-style) at daemon startup:
that keeps PyObjC resident in the long-lived process, papers over the real coupling,
and adds an AppKit dependency purely to suppress a symptom. Subprocess isolation is
also the behavior the user explicitly wants back, so it wins on long-term-over-
short-term as well.

For the baseline flush, the plan reuses the existing `check_for_changes` seed seam
rather than adding a parallel snapshot path: prime is just "run the normal fetch,
persist the baseline for every subject, skip email." The rejected alternative was a
separate scraper/writer for priming, which would duplicate the download/parse/seed
logic and risk drifting from the real detection path.

## Scope

- Make `--loop` mode in `tools/email_schedule_report.py` run each report pass by
  shelling out to a fresh single-shot child (`sys.executable` running this same
  script with `-t <term>`, the resolved `--subject` flags, and `-e`).
- Ensure the daemon's own import chain stays free of `applescript`: import
  `course_scheduling.report_pipeline` lazily (inside the single-shot branch only),
  not at module top, so the loop-mode process only imports the stdlib-only
  `course_scheduling.report_scheduler`.
- Update the now-inaccurate module docstrings in
  `course_scheduling/report_scheduler.py` and `course_scheduling/report_pipeline.py`
  that claim nothing is shelled out.
- Prove the Dock-registration mechanism with a runtime import trace before editing.
- Add a pytest regression test that the loop entry import path stays free of
  `applescript`/PyObjC, and a unit test of the child-command builder.
- Log child-process nonzero exit so a failed scheduled send stays visible.
- Add a `prime_baseline(term_code, subjects)` path in `report_pipeline` and a
  `--prime` flag on `tools/email_schedule_report.py` that fetches, caches every
  subject, seeds+saves memory, and sends no email.
- Wire `run_email_tmux.sh` to prime by default before starting the loop, with a
  `--no-prime` opt-out.
- Verify end-to-end: daemon runs with no Dock icon; a forced fire still sends; a
  primed start yields a delta-only first email.
- Update `docs/CHANGELOG.md`.

## Non-goals

- No change to `course_scheduling/email_sender.py` AppleScript content, Mail.app
  behavior, recipients, or the `activate`/`visible:true` script (Mail's own window
  coming forward during send is expected).
- No change to the schedule slots or `run_loop` timing logic.
- No AppKit/`setActivationPolicy_`/LSUIElement/`Info.plist` approach.
- No conversion to launchd; tmux launch via `run_email_tmux.sh` stays the entry
  point.
- No change to single-shot `run_report` internals.
- Prime does not send email, does not change the change-detection algorithm, and
  does not alter the meaning of a real scheduled run; it only establishes the
  baseline (cache CSVs + memory) that later runs diff against.
- No auto-prime on every restart without an opt-out; priming is the default but
  `--no-prime` must exist so accumulated changes can be preserved on demand.

## Milestone plan

| M | Title | Summary | Goal |
| --- | --- | --- | --- |
| M1 | Restore subprocess isolation for scheduled sends | Loop mode shells out to a short-lived child per fire; daemon import chain drops applescript | Daemon runs with no persistent Dock icon; emails still send |
| M2 | Add baseline flush (prime) on loop start | New `--prime` mode caches all subjects + seeds memory without sending; launcher primes by default with a `--no-prime` opt-out | First scheduled email after start is delta-only, not a full dump |

### M1 - Restore subprocess isolation for scheduled sends

Depends on: none.

Parallel-plan ready: no. Single small, serial change centered on one file
(`tools/email_schedule_report.py`); M1-A0 gates M1-A, and verification (M1-B)
must run after implementation. Splitting into parallel lanes would add
coordination cost with no wall-time gain.

Work package M1-A0 (owner: coder): confirm the root cause before changing code.
Depends on: none. Lightweight confirmation, not a research task - the architectural
fix (keep both the import and the AppleScript run out of the long-lived process) is
correct regardless of the exact registration point.
- Capture the current loop-entry import graph once:
  `source source_me.sh && python3 -X importtime tools/email_schedule_report.py
  --help 2>trace.txt` and confirm `applescript`/`Foundation` appear (proves PyObjC
  loads into the daemon today).
- Note in the changelog entry whether the Dock icon appears at import or only after
  the first `scpt.run()`; a single quick observation is enough. Do not expand into a
  multi-case study.
- Acceptance: trace shows the daemon entry imports `applescript`; the registration
  point is noted in one line.

Work package M1-A (owner: coder): decouple loop mode from the applescript chain.
Depends on: M1-A0.
- In `tools/email_schedule_report.py`, move `import course_scheduling.report_pipeline`
  out of module top (line 16) and into the single-shot `else` branch of `main()`
  (currently line 84), so it loads only when actually running a report in-process.
  Keep `import course_scheduling.report_scheduler` at module top (stdlib-only chain).
- Add a small pure helper `build_child_command(term_code, subjects)` that returns
  the child argv list: `[sys.executable, os.path.abspath(__file__), '-t',
  term_code]` plus `'--subject', s` for each subject, plus `'-e'`. Keeping it a
  named, side-effect-free function makes the callback unit-testable (M1-A2).
- Replace the in-process loop callback (currently `report_callback` at lines 79-81
  calling `report_pipeline.run_report(...)`) with one that shells out via
  `build_child_command(...)`: `result = subprocess.run(cmd, check=False)` and, on
  `result.returncode != 0`, log a warning so a failed scheduled send stays visible
  (matches the old loop's non-fatal, keep-looping behavior). Add `import subprocess`
  to the standard-library import block.
- CLI/config parity: `report_pipeline.run_report(term_code, subjects, dry_run)`
  takes exactly these inputs; loop mode always sends (`dry_run=False`). Confirm no
  other loop-state value (env, cwd-derived config, extra flag) affects report
  generation or delivery, so the child (`-t`, repeated `--subject`, `-e`) is a
  complete match for the in-process call it replaces. Record the confirmation.
- Update the module docstrings that now misstate behavior:
  `course_scheduling/report_scheduler.py` docstring (lines 1-13, "shells out to
  nothing") and `course_scheduling/report_pipeline.py` docstring (lines 1-8, "no
  sibling script is shelled out to") to describe the subprocess-per-fire flow.
- Follow-on (do not stop before these): add the `docs/CHANGELOG.md` entry (root
  cause from M1-A0 + the subprocess-isolation fix + rejected AppKit option); run
  `pyflakes` on edited files and `pytest tests/`.
- Acceptance: `pyflakes tools/email_schedule_report.py
  course_scheduling/report_scheduler.py` clean; `pytest tests/` passes.

Work package M1-A2 (owner: coder): regression tests for the design boundary.
Depends on: M1-A. Independent file from M1-A edits, so it can start as soon as the
M1-A interface (`build_child_command`, module-top imports) is in place.
- Add `tests/test_email_loop_no_pyobjc.py`: import the loop entry module
  (`import tools.email_schedule_report` via the repo-root path shim, or import the
  stdlib-only `course_scheduling.report_scheduler`) in a subprocess-clean
  interpreter and assert `'applescript' not in sys.modules` and no PyObjC module
  (`Foundation`, `AppKit`) is present. This is a behavioral boundary test in the
  style of the sanctioned "core code must not import PySide6" example in
  `docs/PYTEST_STYLE.md`; runtime `sys.modules` is the source of truth, grep is a
  supporting check only.
- Add a unit test of `build_child_command(term_code, subjects)`: assert the argv
  contains `-t <term>`, a `--subject <s>` pair per subject in order, and ends with
  `-e`; assert it does NOT contain `--loop` (no recursive daemon). Deterministic,
  no subprocess spawn.
- Add a callback test: monkeypatch `subprocess.run`, invoke the loop callback once,
  and assert it was called with the argv from `build_child_command` and that a
  nonzero return code triggers the warning log. This exercises the actual loop-fire
  path without waiting for a schedule slot.
- Acceptance: all three tests pass under `pytest tests/`; each finishes well under
  one second and spawns no real Mail.app/AppleScript.

Work package M1-B (owner: coder): end-to-end verification. Depends on: M1-A, M1-A2.
One primary proof per invariant; keep it short.
- Clean daemon imports: covered by the M1-A2 `sys.modules` regression test (no extra
  work here).
- No persistent Dock registration: start the daemon detached via
  `run_email_tmux.sh`; confirm the sleeping daemon PID is not a foreground app with
  one check - `lsappinfo info -only StatusLabel <pid>` (or System Events
  `background only` query). Capture the output.
- Child exits after sending: force one fire by running the child command from
  `build_child_command` and confirm with `pgrep` that the child appears then is gone
  after the send.
- Timing contract (one line): the callback is synchronous, so `run_loop` blocks
  until the child finishes before the next slot - same as the old loop's blocking
  `subprocess.run`; a slow send delays, never overlaps, the next fire.
- Acceptance: the foreground-app check shows the sleeping daemon is background-only;
  the forced-fire child spawns and exits.

Exit criteria:
- M1-A0 trace artifact recorded; Dock-registration trigger identified.
- Loop daemon import chain contains no `applescript`/PyObjC (proven by the
  `sys.modules` regression test, grep supporting).
- Loop callback, child-command builder, and nonzero-exit logging covered by tests.
- Foreground-app check confirms the sleeping daemon is background-only.
- A forced fire sends email through a short-lived child that spawns and exits.
- `pyflakes` clean on edited files; `pytest tests/` green.
- `docs/CHANGELOG.md` updated.

### M2 - Add baseline flush (prime) on loop start

Depends on: M1-A (shares `tools/email_schedule_report.py` main()/parse_args; land
the import/callback change first to avoid a merge collision on the same file).

Parallel-plan ready: yes (after M1-A). M2-A (pipeline+CLI), M2-B (launcher shell),
and M2-C (tests) are independent lanes once M2-A's `prime_baseline` signature is
fixed; up to 2 doers can run M2-B and M2-C concurrently against M2-A's interface.

Work package M2-A (owner: coder): prime mode in the pipeline and CLI.
Depends on: M1-A.
- Add `prime_baseline(term_code, subjects)` to `course_scheduling/report_pipeline.py`:
  `setup_logging`; load memory via
  `full_course_memory.load_memory(csv_cache.FULL_MEMORY_PATH)`; make a temp dir;
  call `change_detect.check_for_changes(term_code, subjects, tmp_dir, memory)` (this
  fetches/parses every subject and seeds full-section memory on a first run);
  then unconditionally persist the baseline for ALL subjects with
  `csv_cache.update_csv_cache(term_code, tmp_dir, subjects)` and
  `full_course_memory.save_memory(csv_cache.FULL_MEMORY_PATH, memory)`; clean up the
  temp dir. Compose and send NO email (never call `email_sender.send_email`). Log
  "baseline primed: N subjects cached".
- Reuse existing helpers; do not fork the download/parse/seed logic. The only new
  behavior is "persist the baseline for every subject and skip email".
- Add a `--prime` flag to `tools/email_schedule_report.py parse_args`, made mutually
  exclusive with `--loop` via `parser.add_mutually_exclusive_group()` (passing both
  is an argparse error). In `main()`, a `--prime` run calls
  `report_pipeline.prime_baseline(term_code, subjects)` once and returns
  (single-shot, short-lived process). Keep the lazy `report_pipeline` import (M1-A)
  covering this branch too.
- Follow-on: `docs/CHANGELOG.md` entry; `docs/USAGE.md` note documenting `--prime`;
  `pyflakes` + `pytest tests/`.
- Acceptance: `email_schedule_report.py -t <term> --prime` writes a cache CSV per
  subject under `cache/` and updates `cache/full_course_memory.yaml` without sending
  email; a subsequent `-t <term> -n` (dry-run) reports no "added" flood for
  unchanged subjects.

Work package M2-B (owner: coder): launcher prime-by-default with opt-out.
Depends on: M2-A.
- Edit `run_email_tmux.sh`: add a `--no-prime` argument parse (default prime=on).
  When priming is on, run a short-lived prime step before the loop, for example the
  tmux command becomes
  `cd $REPO_ROOT && source source_me.sh && python3 tools/email_schedule_report.py
  -t $TERM_CODE --prime && python3 tools/email_schedule_report.py --loop --term
  $TERM_CODE`; when `--no-prime` is passed, drop the prime segment. The prime and
  the loop are separate processes, so the prime child (which imports applescript)
  exits before the pure-stdlib daemon starts - consistent with M1.
- Update the `Usage:` comment block to document `--no-prime`.
- Acceptance: `./run_email_tmux.sh` primes then loops (log shows "baseline primed"
  before "loop started"); `./run_email_tmux.sh --no-prime` starts the loop with no
  prime step; existing "session already running" guard still works.

Work package M2-C (owner: coder): tests for prime behavior. Depends on: M2-A. This
package owns the primary delta-only proof; it is not optional.
- Primary delta-only test (the key protected behavior): monkeypatch
  `download_and_parse_subject` to write fixed inline snapshot rows (no network),
  point cache/memory at `tmp_path`, then: (1) start from an empty cache, (2) call
  `prime_baseline` with known data, (3) assert BOTH state stores were written - a
  cache CSV exists per subject AND `full_course_memory.yaml` was saved, (4) run the
  normal detection path (`check_for_changes`) again on the SAME unchanged data and
  assert no subject is flagged meaningfully changed (no "added" flood). This proves
  priming prevents the initial dump. Deterministic, offline, sub-second.
- Send-suppression test: monkeypatch `check_for_changes` and
  `email_sender.send_email`, call `prime_baseline`, assert `send_email` is never
  called and `update_csv_cache` receives the full subject list.
- `parse_args` test: `--prime` sets the flag; passing `--prime` with `--loop` raises
  `SystemExit` (argparse mutual-exclusion error).
- Acceptance: tests pass under `pytest tests/`, offline, no Mail.app; the delta-only
  test asserts on both cache CSV presence and memory persistence.

Exit criteria:
- `--prime` caches every subject and seeds memory with no email sent (test-proven).
- Delta-only behavior protected by the automated M2-C primary test (empty cache ->
  prime -> unchanged run -> no "added" flood), checking both cache CSVs and memory.
- `--prime` and `--loop` are mutually exclusive (argparse-enforced, test-proven).
- Launcher primes by default and honors `--no-prime` (verified by log/dry-run).
- A primed clean start produces a delta-only first scheduled email instead of a full
  dump (verified against a freshly cleared `cache/`).
- `docs/USAGE.md` documents `--prime`/`--no-prime`; `docs/CHANGELOG.md` updated.
- `pyflakes` clean; `pytest tests/` green.

## Architecture boundaries

Mapping (milestone/workstream -> component -> patch):

| Workstream | Component / module | Change kind | Patch |
| --- | --- | --- | --- |
| M1-A | `tools/email_schedule_report.py` (loop entry / main) | lazy import + subprocess callback | Patch 1 |
| M1-A | `course_scheduling/report_scheduler.py`, `course_scheduling/report_pipeline.py` (docstrings) | doc correction | Patch 1 |
| M1-A2 | `tests/test_email_loop_no_pyobjc.py` (+ callback/builder tests) | new tests | Patch 1 |
| M1-B | E2E verification (no code) | verification only | Patch 1 (notes) |
| M2-A | `course_scheduling/report_pipeline.py` (`prime_baseline`), `tools/email_schedule_report.py` (`--prime`) | new prime mode + CLI flag | Patch 2 |
| M2-B | `run_email_tmux.sh` (prime-by-default, `--no-prime`) | launcher wiring | Patch 2 |
| M2-C | `tests/` (prime pipeline + parse_args tests) | new tests | Patch 2 |

Durable boundary: `course_scheduling.report_scheduler` stays the stdlib-only "when
to run" component; `course_scheduling.report_pipeline` + `email_sender` stay the
GUI-touching "do the run" component; the loop entry point keeps them in separate
processes.

## Acceptance criteria and verification

- Import isolation: from the loop entry (`email_schedule_report` module top +
  `report_scheduler`), no path reaches `import applescript`. Verify with
  `grep -rn "import applescript" course_scheduling/` (only `email_sender.py`) plus
  an import trace showing `report_scheduler` pulls only stdlib.
- No Dock icon: start the daemon detached; observe the Dock while it sleeps - no
  Python icon.
- Send still works: `source source_me.sh && python3 tools/email_schedule_report.py
  -t 202710 -e` composes and sends via Mail.app; the child exits afterward.
- Prime works: against a cleared `cache/`, `python3 tools/email_schedule_report.py
  -t 202710 --prime` writes one cache CSV per subject and updates
  `cache/full_course_memory.yaml`, sends no email, and a following `-n` dry-run shows
  no full "added" dump for unchanged subjects.
- Launcher default: `./run_email_tmux.sh` logs "baseline primed" before the loop
  starts; `./run_email_tmux.sh --no-prime` skips priming.
- Lint/tests: `pyflakes` clean on edited files; `pytest tests/` passes.

## Risk register

| Risk | Impact | Trigger | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| Subject list not expanded correctly into child argv | Child runs wrong/empty subject set | subjects passed as one arg instead of repeated `--subject` | Build argv by appending `'--subject', s` per subject; verify child `--help`/dry-run argv in M1-B | coder |
| Child inherits a different Python/env than the daemon | Import failures in child | `sys.executable` or cwd differs from tmux launch env | Use `sys.executable` + `os.path.abspath(__file__)`; daemon already runs after `source source_me.sh` so child inherits env | coder |
| AppleScript still briefly shows an icon during the child's send | Momentary Dock flash | child runs AppleScript | Acceptable and matches old behavior; icon dies when child exits (documented, not a regression) | reviewer |
| Prime-by-default swallows real changes after a loop restart | Missed schedule alerts | user restarts loop while changes were pending | `--no-prime` opt-out documented in launcher usage; changelog notes the tradeoff | coder |
| Prime persists a partial baseline if a subject download fails midway | Later run diffs against incomplete cache | network/parse error during `check_for_changes` | Let the error propagate so cache/memory are not half-written (match `run_report`'s send-before-persist ordering); prime writes cache+memory only after a clean fetch pass | coder |

## Documentation execution

- Patch 1: add a `docs/CHANGELOG.md` entry under the current date documenting the
  Dock-icon root cause (in-process PyObjC load in the long-lived daemon) and the fix
  (subprocess-per-fire isolation, lazy `report_pipeline` import), including the
  decision to reject the AppKit activation-policy approach. Correct the
  `report_scheduler.py` and `report_pipeline.py` module docstrings in the same patch.
- Patch 2: add a `docs/CHANGELOG.md` entry for the baseline-flush feature (prime
  mode, launcher prime-by-default with `--no-prime`); add a `--prime`/`--no-prime`
  section to `docs/USAGE.md`.

## Open decisions

- None blocking. M1 approach is subprocess isolation (Option A); the
  activation-policy alternative (Option B) is rejected in Design philosophy. M2
  triggering is prime-by-default with a `--no-prime` opt-out, per the user's choice.
