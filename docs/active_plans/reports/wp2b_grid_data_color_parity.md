# WP-2B grid data and color parity lane record

Plan reference: we-got-this-code-tidy-owl.md#WP-2B

## Summary

Created `tests/e2e/e2e_parity_grid.py`, an e2e parity harness that runs the
old and new grid-generation paths across all nine worksheet configurations and
asserts identical cell values, merged-range sets, and fill hex colors. The old
modules are loaded through `tests/e2e/old_code_bridge.py`, which keeps the old
tree byte-identical.

Result: all nine configs, every category (input-row gate, cell values, merge
sets, fill hex), PASS, exit 0.

## Files changed

- Added `tests/e2e/e2e_parity_grid.py` (only file created).

No production module, the old tree, the fixtures, or the bridge were modified.

## Verification output

Command: `source source_me.sh && python3 tests/e2e/e2e_parity_grid.py`

```
  [PASS] lower_undergrad_202710: input rows identical old-vs-new
  [PASS] undergrad_level_202710: input rows identical old-vs-new
  [PASS] 300_level_undergrad_202710: input rows identical old-vs-new
  [PASS] graduate_level_202710: input rows identical old-vs-new
  [PASS] schaumburg_202710: input rows identical old-vs-new
  [PASS] lab_chicago_202710: input rows identical old-vs-new
  [PASS] lab_schaumburg_202710: input rows identical old-vs-new
  [PASS] raw_table_202710: input rows identical old-vs-new
  [PASS] all_courses_in_dept_202710: input rows identical old-vs-new
  [PASS] lower_undergrad_202710: cells, merges, and fills identical
  [PASS] undergrad_level_202710: cells, merges, and fills identical
  [PASS] 300_level_undergrad_202710: cells, merges, and fills identical
  [PASS] graduate_level_202710: cells, merges, and fills identical
  [PASS] schaumburg_202710: cells, merges, and fills identical
  [PASS] lab_chicago_202710: cells, merges, and fills identical
  [PASS] lab_schaumburg_202710: cells, merges, and fills identical
  [PASS] raw_table_202710: cells, merges, and fills identical
  [PASS] all_courses_in_dept_202710: cells, merges, and fills identical
  configs compared: 9
  gate failures (parse/filter/sort/merge): 0
  blocking cell/merge/fill failures: 0
  incidental styling notes (non-blocking): 0
RESULT: PASS (full grid-data and color parity across all nine configs)
```

Command: `source source_me.sh && pyflakes tests/e2e/e2e_parity_grid.py`
Output: none (clean).

Negative self-test: the harness was confirmed to flag injected cell-value,
merge-removal, and fill-hex differences before re-running clean.

## Coverage summary by category

| Category | Scope | Result |
| --- | --- | --- |
| Input-row gate | All 9 configs | PASS |
| Cell values | all_courses_in_dept_202710: 575; lab_chicago_202710: 468; raw_table_202710: 3961; other six: identical (count not separately captured) | PASS |
| Merged-range sets | all_courses_in_dept_202710: 160 blocks; lab_chicago_202710: 53 blocks; other six: identical (count not separately captured) | PASS |
| Fill hex (color) | All schedule-grid tabs (raw_table excluded, string-only) | PASS |

Exact per-sheet counts were captured for three representative sheets
(all_courses_in_dept_202710, lab_chicago_202710, raw_table_202710); the
remaining six configs were verified identical without a captured numeric count.

## Design note: raw_table normalization

The `raw_table` tab is written by pandas (old code) vs openpyxl (new code).
Cell values are compared under numeric/empty-string normalization so pandas
float-coercion (e.g., `201.0`) vs new int (`201`) is treated as
representation-equal, not a regression. All schedule-grid tabs are string-only
and matched exactly without relying on this normalization.

Category: accepted-intentional-difference (implementation detail of the
output library, not a behavioral regression).

## Divergences

Zero value mismatches in every category. No regressions, no
inconclusive fixture issues.

## Notes for close-out

docs/CHANGELOG.md will be updated by the docs subagent at close-out; this lane
did not edit the changelog.
