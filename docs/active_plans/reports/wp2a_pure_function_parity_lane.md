# WP-2A pure-function parity lane record

Plan reference: we-got-this-code-tidy-owl.md#WP-2A

## Summary

Created `tests/e2e/e2e_parity_functions.py`, an e2e parity harness that feeds a
shared input set to every pure helper carried from the old flat
`course_scheduling` tree into the new `course_scheduling` package and asserts
identical return values. The old modules are loaded through
`tests/e2e/old_code_bridge.py`, which keeps the old tree byte-identical.

Result: 30 functions, 2181 checks, all PASS, exit 0.

## Files changed

- Added `tests/e2e/e2e_parity_functions.py` (only file created).

No production module, the old tree, the fixtures, or the bridge were modified.

## Verification output

Command: `source source_me.sh && python3 tests/e2e/e2e_parity_functions.py`

```
Old modules loaded; stray-output temp dir: /var/folders/.../old_code_bridge_dcaxa6zp
Harvested 136 strict labels from fixtures
subject filter remove: CHEM 450-01
... (old should_include_class print side effects) ...
RESULT: PASS (2181 checks across 30 functions agree)
EXIT=0
```

Per-function summary line: every entry is `PASS <name> (<checks> checks)`;
notable counts include `label_to_pastel_hex (1192 checks)`,
`evaluate_class_inclusion (49 checks)`, `should_include_class (49 checks)`,
`split_course_label (155 checks)`, `populate_schedule_grid (1 checks)`.

Command: `source source_me.sh && pyflakes tests/e2e/e2e_parity_functions.py`
Output: none (clean).

## Old to new function mapping

Pure-return functions (return value compared directly):

| Old (course_finder_lib unless noted) | New module.function |
| --- | --- |
| split_course_label | course_label.split_course_label |
| normalize_course_label | course_label.normalize_course_label |
| normalize_label_key | course_label.normalize_label_key |
| parse_merged_label | course_label.parse_merged_label |
| extract_course_number | course_label.extract_course_number |
| convert_section_number | course_label.convert_section_number |
| course_number_to_level | course_label.course_number_to_level |
| infer_level_from_course_number | course_label.infer_level_from_course_number |
| label_to_pastel_hex | schedule_colors.label_to_pastel_hex |
| hls_to_hex | schedule_colors.hls_to_hex |
| string_to_anger | schedule_colors.string_to_anger |
| parse_enrollment_ratio | enrollment_parse.parse_enrollment_ratio |
| time_to_military | schedule_time.time_to_military |
| is_common_hour_conflict | schedule_time.is_common_hour_conflict |
| is_official_time_block | schedule_time.is_official_time_block |
| time_to_slot | schedule_time.time_to_slot |
| round_down_to_nearest_15 | schedule_time.round_down_to_nearest_15 |
| time_slot_to_row_number | grid_model.time_slot_to_row_number |
| compute_columns_info | grid_model.compute_columns_info |
| find_available_column | grid_model.find_available_column |
| get_lab_filter_details | lab_filter.get_lab_filter_details (dict compared) |
| evaluate_class_inclusion | course_filter.evaluate_class_inclusion (tuple compared) |
| should_include_class | course_filter.should_include_class (bool compared) |
| grid_courses_from_html.normalize_day_token | html_tokens.normalize_day_token |
| grid_courses_from_html.parse_html_time | html_tokens.parse_html_time |
| grid_courses_from_html.normalize_label_text | html_tokens.normalize_label_text |
| grid_courses_from_html.parse_meeting_blocks | html_tokens.parse_meeting_blocks (list compared) |
| grid_courses_from_html.infer_campus_from_text | html_tokens.infer_campus_from_text |

Side-effect-producing functions (compared by mutated/returned structure):

| Old | New | Comparison basis |
| --- | --- | --- |
| populate_schedule_grid | grid_model.populate_schedule_grid | returned grid dict |
| fill_the_status_grid | grid_model.fill_the_status_grid | mutated status dict |

## Mapping choices and divergences

- evaluate_class_inclusion / should_include_class: the old functions take an
  argparse-style Namespace; the new ones take a FilterSpec dataclass with the
  same five fields (subjects, campus, levels, number, lab_only). Pairs were
  built with matched values via `build_filter_pairs()`. Classified as
  accepted-intentional-difference (interface change only); return values agree.
- find_available_column: the old signature carries an unused leading worksheet
  argument (`ws`); the new signature drops it. Paired by calling the old form
  with `ws=None`. Accepted-intentional-difference; return value agrees.
- should_include_class: the old function prints exclusion reasons to stdout as a
  side effect (visible as `subject filter remove:` lines during the run). Only
  the boolean return is compared. Old-code behavior preserved; not a mismatch.
- extract_course_number: the old function raises on a non-matching label (it
  unpacks a `None` return), while the new function guards and returns `None`.
  Parity is checked on strict labels only; the new None-handling is an
  intentional robustness improvement, documented here rather than flagged as a
  mismatch. Accepted-intentional-difference.
- number_to_pastel_hex (old, course_finder_lib) has no new counterpart: it is a
  legacy HSV helper that the old `label_to_pastel_hex` does not call (the
  fallback hue math is inlined in both old and new). Left unpaired as dead/
  legacy code; the live color path is fully covered by label_to_pastel_hex.

No mismatches were found. No regressions, no inconclusive fixture issues.

## Notes for close-out

docs/CHANGELOG.md will be updated by the docs subagent at close-out; this lane
did not edit the changelog.
