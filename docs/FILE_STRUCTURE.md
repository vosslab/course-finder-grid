# File structure

Directory map for the repo: what belongs where, what is generated, and where to
add new work.

## Top-level layout

```text
course-finder-grid/
+- build_grids_from_html.py   # root entry point: HTML -> merged xlsx workbook
+- run_email_tmux.sh          # start the email daemon in a tmux session
+- source_me.sh               # bootstrap: sets PYTHONPATH, env vars
+- AGENTS.md                  # agent instructions and repo guardrails
+- CLAUDE.md                  # Claude Code project config (loads AGENTS.md)
+- README.md                  # project purpose and quick start
+- VERSION                    # single version source (CalVer)
+- REPO_TYPE                  # repo type marker (value: python)
+- Brewfile                   # Homebrew dependency manifest
+- pip_requirements.txt       # runtime pip dependencies
+- pip_requirements-dev.txt   # dev/test pip dependencies (pytest, etc.)
+- LICENSE                    # symlink to primary license
+- LICENSE.GPL-3.0.md         # GPLv3 license text
+- course_scheduling/         # core Python package (code only, no runtime state)
+- tools/                     # secondary CLI entry points
+- tests/                     # pytest suite + E2E scripts
+- docs/                      # all project documentation
+- devel/                     # developer tools (version bumps, changelog helpers)
+- data/                      # conventional location for user-supplied input CSV (not in repo)
+- cache/                     # runtime: per-subject CSV snapshots (gitignored)
+- logs/                      # runtime: email-report log (gitignored)
+- output/                    # runtime: generated xlsx workbooks (gitignored)
+- classic/                   # local reference workbooks for manual comparison (gitignored)
```

## Key subtrees

### course_scheduling/

The pure-code package. No generated files, no runtime state. Every module is
argparse-free except `cs_cli.py`.

```text
course_scheduling/
+- __init__.py                  # empty (one-line docstring only)
+- banner_http.py               # Banner HTTP session: fetch, POST, save HTML
+- banner_parser.py             # lxml parse of saved HTML -> course dicts
+- html_tokens.py               # day/time token normalization, meeting-block parsing
+- html_courses.py              # FilterSpec application + expand to grid rows
+- crosslist_resolver.py        # union-find cross-list merging
+- enrollment_parse.py          # enrolled/capacity ratio parser
+- csv_courses.py               # draft-schedule CSV -> grid rows
+- course_filter.py             # FilterSpec dataclass + evaluate_class_inclusion
+- course_label.py              # label normalization, course-number extraction
+- lab_filter.py                # lab-section heuristic
+- grid_model.py                # pure in-memory 15-minute time-slot grid
+- xlsx_writer.py               # openpyxl grid renderer
+- schedule_colors.py           # deterministic pastel fill colors
+- schedule_time.py             # time-slot arithmetic helpers
+- workbook_builder.py          # coordinator: GridConfig matrix, download->merge pipeline
+- xlsx_merge.py                # merge per-tab xlsx files into one workbook
+- parser_audit_tables.py       # raw/debug audit table writers (csv + xlsx)
+- schedule_analysis_tables.py  # policy-audit table writers (common-hour, time-blocks)
+- cs_cli.py                    # shared argparse flag definitions (only argparse module)
+- output_naming.py             # descriptive xlsx filename builder from FilterSpec
+- term_code.py                 # Banner term code -> human label (e.g. 202710 -> Fall_2026)
+- change_detect.py             # per-subject change detection; pure diff seam + download path
+- csv_diff.py                  # CSV row loading and row-level comparison
+- csv_cache.py                 # on-disk cache (cache/ dir); snapshot persistence
+- full_course_memory.py        # YAML-backed "now full" CRN memory per term
+- change_summary.py            # human-readable diff text builders
+- email_report.py              # email subject + body composition
+- email_sender.py              # AppleScript transport via Mail.app
+- report_pipeline.py           # end-to-end orchestration for one report run
+- report_scheduler.py          # sleep-loop scheduler (Mon-Thu + Fri schedule)
```

### tools/

Secondary CLI entry points run directly or via `source source_me.sh && python3`.

```text
tools/
+- build_grid_from_csv.py    # grid from draft-schedule CSV; full filter set
+- email_schedule_report.py  # one-shot or looping change-detection report
```

### tests/

Fast pytest tests under `tests/`; E2E scripts under `tests/e2e/` (excluded from
pytest via `conftest.py`).

```text
tests/
+- conftest.py                      # pytest config; excludes e2e/ and playwright/
+- file_utils.py                    # shared get_repo_root() helper
+- TESTS_README.md                  # test suite overview
+- test_full_report_integration.py  # integration: change-detect + email pipeline
+- test_cli_filters.py              # filter predicate unit tests
+- test_full_course_memory.py       # full-section memory unit tests
+- test_pyflakes_code_lint.py       # repo-wide pyflakes gate
+- test_function_typing.py          # type-annotation enforcement
+- test_shebangs.py                 # shebang + executable bit consistency
+- test_ascii_compliance.py         # ASCII/ISO-8859-1 character gate
+- test_markdown_links.py           # local Markdown link validity
+- test_import_requirements.py      # third-party import declaration gate
+- test_import_dot.py               # no relative imports gate
+- test_import_star.py              # no import * gate
+- test_indentation.py              # tabs-only indentation gate
+- test_init_files.py               # __init__.py content gate
+- test_whitespace.py               # trailing whitespace gate
+- test_bandit_security.py          # bandit security linter gate
+- test_pytest_hygiene.py           # test file self-hygiene check
+- test_readme_first_paragraph.py   # README first-paragraph format check
+- check_ascii_compliance.py        # single-file ASCII check helper
+- fix_ascii_compliance.py          # single-file ASCII fix helper
+- fix_whitespace.py                # single-file whitespace fix helper
+- e2e/                             # non-browser E2E scripts (not run by pytest)
|  +- run_all.sh                    # run all e2e_* scripts
|  `- e2e_build_grids.py            # full HTML -> xlsx pipeline smoke test
```

### docs/

All project documentation. Files follow SCREAMING_SNAKE_CASE naming.

```text
docs/
+- CHANGELOG.md               # chronological record of changes
+- CODE_ARCHITECTURE.md       # system design, components, data flow
+- FILE_STRUCTURE.md          # this file: directory map
+- USAGE.md                   # CLI flags, workflows, output locations
+- AUTHORS.md                 # maintainers and contributors
+- PYTHON_STYLE.md            # Python coding conventions
+- REPO_STYLE.md              # repo-wide organization conventions
+- PYTEST_STYLE.md            # pytest test-writing rules
+- MARKDOWN_STYLE.md          # Markdown writing rules
+- E2E_TESTS.md               # E2E test conventions
+- CLAUDE_HOOK_USAGE_GUIDE.md # Claude Code hook behavior reference
+- active_plans/              # working planning artifacts (in-flight)
```

### devel/

Developer tools not shipped with the package.

```text
devel/
+- changelog_lib.py       # shared parser/serializer for changelog tools
+- rotate_changelog.py    # rotate docs/CHANGELOG.md when it reaches ~1000 lines
+- query_changelog.py     # search changelog by date, category, or keyword
+- commit_changelog.py    # draft commit message from new changelog bullets
+- bump_version.py        # bump VERSION and pyproject.toml together
+- dist_clean.sh          # clean build/dist artifacts
+- flatten_broken_md_links.py  # repair broken Markdown links
+- DEVEL_README.md        # developer tool reference
```

### data/

Conventional location for user-supplied input CSVs. No sample CSV ships with
the repository; create `data/` and add your own draft-schedule export (for
example `data/spring_2026_sample_courses.csv`). Generated outputs do not live
here.

## Generated artifacts

All generated artifacts are gitignored and live outside `course_scheduling/`.

| Location | Contents |
| --- | --- |
| `cache/` | Per-subject CSV snapshots; `full_course_memory.yaml` (durable full-section memory) |
| `logs/` | `email_schedule_report.log` (appended each run) |
| `output/` | Merged term workbook (`<term>-merged-grid.xlsx`), per-tab grid xlsx files, audit tables |
| `classic/` | Local reference workbooks for manual comparison (not committed) |

## Documentation map

Root docs: [README.md](../README.md), [AGENTS.md](../AGENTS.md), [VERSION](../VERSION).

All other docs live under `docs/`. Key files for contributors:

- [docs/CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md): system design and data flow.
- [docs/FILE_STRUCTURE.md](FILE_STRUCTURE.md): this file.
- [docs/USAGE.md](USAGE.md): CLI flags, workflows, output locations, color scheme.
- [docs/CHANGELOG.md](CHANGELOG.md): chronological change record.
- [docs/PYTHON_STYLE.md](PYTHON_STYLE.md): Python coding conventions (tabs, type hints, no try/except, etc.).

## Where to add new work

| Work type | Location |
| --- | --- |
| New library module | `course_scheduling/<module>.py` |
| New root entry point (standalone CLI) | `<name>.py` at repo root with shebang |
| New secondary tool | `tools/<name>.py` with shebang |
| Fast pytest test | `tests/test_<name>.py` |
| E2E test | `tests/e2e/e2e_<name>.py` or `tests/e2e/e2e_<name>.sh` |
| Documentation | `docs/<NAME>.md` (SCREAMING_SNAKE_CASE) |
| Sample input data | `data/` |
| Developer helper script | `devel/` |
| Temporary scratch files | `_temp*.py` or `/tmp/` (both gitignored / auto-deleted) |
