# course_scheduling rewrite trust report

Plan reference: we-got-this-code-tidy-owl.md#WP-3

## Scope

The flat scripts at `/Users/vosslab/nsh/junk-drawer/course_scheduling/` were
reorganized into the new `course_scheduling/` package. Three behavioral-parity
e2e lanes ran against all affected paths. This report synthesizes their results
into a single safe / not-safe verdict for human review.

Old-code retirement is a separate human follow-up action outside this plan.

## Lane records referenced

- [docs/active_plans/reports/wp2a_pure_function_parity_lane.md](wp2a_pure_function_parity_lane.md) -- pure functions (30 functions, 2181 checks).
- [docs/active_plans/reports/wp2b_grid_data_color_parity.md](wp2b_grid_data_color_parity.md) -- grid data and color (all nine configs).
- [docs/active_plans/reports/wp2c_email_change_detection_parity.md](wp2c_email_change_detection_parity.md) -- email change-detection and rendering (11 cases, Level 1 + Level 2).

## Email claims (three distinct assertions)

### (a1) Email templates -- format strings verified identical

The format strings in the old `email_schedule_report.py` and the new
`email_report.py` + `change_summary.py` match byte-for-byte. This was
established by a verbatim format-string diff before the e2e lanes ran and is
independent of runtime behavior.

Category: accepted-intentional-difference (naming split; content identical).

### (a2) Email change-detection -- WP-2C Level 1

Eleven change-detection scenarios exercised: added CRN, removed CRN, changed
time, changed room, changed instructor, enrollment-only noise suppression,
waitlist-only noise suppression, first full event, already-known full (silent),
capacity increase on known-full, first-run silent seeding.

Result: PASS across all 11 cases.

### (a3) Final rendered email content -- WP-2C Level 2

Subject line, change-summary block, and body all match old-vs-new on the same
inputs.

Result: PASS.

## Tab differences (b)

The new workbook writes 9 tabs; the old workbook wrote 11. The two missing tabs
are written as separate standalone analysis files by design in the new code, not
omitted. Additionally, tab 1 was renamed from
`lower_undergrade` (typo in the old code) to `lower_undergrad`. Both
differences were confirmed by the user as intentional, not regressions.

Category: accepted-intentional-difference (architecture change for the
separate-files design; typo correction).

## Grid results (c) -- WP-2B

Input-row equivalence gate ran first and PASSED for all nine configurations.
Per-sheet comparison then ran across cell values, merged-range sets, and merged-
block fill hex.

| Config | Populated cells | Merged blocks | Fill hex | Result |
| --- | --- | --- | --- | --- |
| all_courses_in_dept_202710 | 575 | 160 | checked | PASS |
| lab_chicago_202710 | 468 | 53 | checked | PASS |
| raw_table_202710 | 3961 | n/a | n/a | PASS |
| lab_schaumburg_202710 | identical (count not captured) | identical (count not captured) | checked | PASS |
| lower_undergrad_202710 | identical (count not captured) | identical (count not captured) | checked | PASS |
| undergrad_level_202710 | identical (count not captured) | identical (count not captured) | checked | PASS |
| 300_level_undergrad_202710 | identical (count not captured) | identical (count not captured) | checked | PASS |
| graduate_level_202710 | identical (count not captured) | identical (count not captured) | checked | PASS |
| schaumburg_202710 | identical (count not captured) | identical (count not captured) | checked | PASS |

Exact per-sheet counts were captured for three representative sheets
(all_courses_in_dept_202710, lab_chicago_202710, raw_table_202710); the
remaining six configs were verified identical without a captured numeric count.

Negative self-test confirmed comparators flag injected cell-value, merge-removal,
and fill-hex differences. Zero mismatches in every category.

## Pure function results (d) -- WP-2A

30 functions, 2181 checks, exit 0, pyflakes clean.

| Check type | Count | Result |
| --- | --- | --- |
| Pure-return functions paired | 28 | PASS |
| Side-effect functions paired | 2 | PASS |
| Total checks | 2181 | PASS |

Noteworthy counts: `label_to_pastel_hex` 1192 checks, `split_course_label`
155 checks, `evaluate_class_inclusion` 49 checks.

## Complete mismatch and caveat register

Every disclosed mismatch and caveat carries exactly one category tag.

| Item | Category |
| --- | --- |
| evaluate_class_inclusion: old argparse Namespace vs new FilterSpec (same 5 fields) | accepted-intentional-difference |
| find_available_column: old unused `ws` arg dropped from new signature | accepted-intentional-difference |
| extract_course_number: old raises on non-matching label, new returns None | accepted-intentional-difference |
| should_include_class: old prints exclusion reasons as side effect (bool return matched) | accepted-intentional-difference |
| number_to_pastel_hex: old legacy HSV helper left unpaired (dead code not on live path) | accepted-intentional-difference |
| raw_table: pandas float-coercion (201.0) vs openpyxl int (201) treated as representation-equal | accepted-intentional-difference |
| Email templates: naming split across email_report.py + change_summary.py (content byte-for-byte identical) | accepted-intentional-difference |
| Tab count: 9 new vs 11 old (separate-files design; user-confirmed) | accepted-intentional-difference |
| Tab 1 name: lower_undergrade (typo) corrected to lower_undergrad (user-confirmed) | accepted-intentional-difference |
| WP-2C fidelity: old change-detection imported directly (tree confirmed byte-identical) | accepted-intentional-difference |
| WP-2C fidelity: full-event sub-cases run on synthetic CRN data, not production-parsed CRNs | inconclusive-fixture-issue |

Total tagged items: 11. No items carry old-code-bug-preserved or
new-code-regression. The single inconclusive-fixture-issue item
(synthetic CRN in full-event sub-cases) does not affect value parity; it
narrows the validation scope for those four sub-cases only.

## Verdict

SAFE TO RETIRE old code.

All three e2e lanes exited 0 with PASS results. The 2181 pure-function checks,
9-config grid-data checks, and 11-scenario email checks produce zero value
mismatches. Every divergence is tagged accepted-intentional-difference or
inconclusive-fixture-issue; none are old-code-bug-preserved or
new-code-regression. The inconclusive-fixture-issue item (full-event sub-cases
on synthetic CRN data) does not introduce a functional regression -- both old
and new code received identical inputs and produced identical outputs. The new
package is behaviorally equivalent to the old flat scripts for all tested
paths. The old flat scripts at
`/Users/vosslab/nsh/junk-drawer/course_scheduling/` may be retired at the
human's discretion.

## Notes for close-out

- docs/CHANGELOG.md was updated at close-out; the throwaway parity harness was
  removed after sign-off per the plan, and this report did not edit the
  changelog itself.
- Old-code retirement is a separate human follow-up action outside this plan.
