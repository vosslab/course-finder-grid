# WP-2C email change-detection parity lane record

Plan reference: we-got-this-code-tidy-owl.md#WP-2C

## Summary

Created `tests/e2e/e2e_parity_email.py`, an e2e parity harness that exercises
old and new change-detection and email-rendering paths across 11 scenario
cases and asserts identical outputs at two levels: detection (Level 1) and
rendered email content (Level 2). The old modules are loaded through
`tests/e2e/old_code_bridge.py`, which keeps the old tree byte-identical.

Result: all 11 cases at both levels, PASS, exit 0.

## Files changed

- Added `tests/e2e/e2e_parity_email.py` (only file created).

No production module, the old tree, the fixtures, or the bridge were modified.

## Verification output

Command: `source source_me.sh && python3 tests/e2e/e2e_parity_email.py`

```
PASS Level 1 added_crn
PASS Level 1 removed_crn
PASS Level 1 changed_time
PASS Level 1 changed_room
PASS Level 1 changed_instructor
PASS Level 1 enrollment_only (noise-suppressed)
PASS Level 1 waitlist_only (noise-suppressed)
PASS Level 1 first_full_event (fires)
PASS Level 1 already_known_full (silent)
PASS Level 1 capacity_increase_on_known_full (fires with "was full at 24" annotation)
PASS Level 1 first_run_silent_seeding
PASS Level 2 subject, change_summary, body all match old-vs-new
PASS: full old-vs-new parity (Level 1 + Level 2)
EXIT=0
```

Command: `source source_me.sh && pyflakes tests/e2e/e2e_parity_email.py`
Output: none (clean).

## Old-to-new module mapping exercised

| Old location | New location |
| --- | --- |
| email_schedule_report.diff_rows | csv_diff.diff_rows |
| email_schedule_report.evaluate_subject_changes | change_detect.evaluate_subject_changes |
| email_schedule_report.detect_full_events / seed_full_sections / full_course_memory | full_course_memory module |
| email_schedule_report.build_change_summary / describe_* | change_summary module |
| email_schedule_report inline subject/body builders | email_report module |

## Coverage summary by level

| Level | Cases covered | Result |
| --- | --- | --- |
| Level 1 detection | 11 cases (see list below) | PASS |
| Level 2 render | subject, change_summary, body | PASS |

Level 1 cases:

- added_crn -- new CRN fires a change event.
- removed_crn -- dropped CRN fires a change event.
- changed_time -- meeting-time edit detected.
- changed_room -- room edit detected.
- changed_instructor -- instructor edit detected.
- enrollment_only -- enrollment-count-only delta is noise-suppressed (no email).
- waitlist_only -- waitlist-count-only delta is noise-suppressed (no email).
- first_full_event -- first time a section goes full, email fires.
- already_known_full -- section already in full-course memory, stays silent.
- capacity_increase_on_known_full -- section was full and capacity grew; email fires
  with "was full at 24" annotation.
- first_run_silent_seeding -- first-run seed pass populates memory silently.

## Fidelity caveats

### Old change-detection import path

The old change-detection code lives in `email_schedule_report.py`, which the
WP-1 bridge does not export as a top-level module. The harness imported it
directly while reusing `old_code_bridge._compute_tree_snapshot` and
`_assert_tree_unchanged` so the old tree remained byte-identical
(snapshot -> path-insert -> import -> assert unchanged). The approach is sound
and the old tree was confirmed unchanged after import; disclosed here for
transparency.

Category: accepted-intentional-difference (test implementation detail, not a
production code concern).

### Synthetic CRN in full-event cases

Real csv_cache snapshots predate the CRN column. For the full-event sub-cases
(first_full_event, already_known_full, capacity_increase_on_known_full,
first_run_silent_seeding), the harness injected a deterministic synthetic CRN
into both before and after rows with identical schema. Both old and new code
receive byte-identical input, so value parity holds; however, these sub-cases
run on synthetic CRN data rather than production-parsed CRNs.

Category: inconclusive-fixture-issue (parity itself is clean; the full-event
sub-cases are not validated against production CRN data).

## Divergences

No value mismatches at Level 1 or Level 2. The two fidelity caveats above
carry category tags; neither is a regression.

## Notes for close-out

docs/CHANGELOG.md will be updated by the docs subagent at close-out; this lane
did not edit the changelog.
