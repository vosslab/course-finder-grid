# Development

Use this guide when changing the repository itself. It connects the local edit,
build, and verification workflow; [INSTALL.md](INSTALL.md) owns dependencies,
and [USAGE.md](USAGE.md) owns end-user commands and flags.

## Development boundaries

- Run Python from the repository root through `source source_me.sh && python3`.
- Keep runtime state out of `course_scheduling/`. Generated `cache/`, `logs/`,
  `output/`, `build/`, and `CourseFinderMailer.app/` are gitignored.
- Keep application code in `course_scheduling/`, secondary command-line tools
  in `tools/`, and maintainer-only helpers in `devel/`.
- Use the module-level ownership and data-flow map in
  [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) before changing a boundary.
- Follow [PYTHON_STYLE.md](PYTHON_STYLE.md) and [PYTEST_STYLE.md](PYTEST_STYLE.md)
  when adding code or tests.

## Fast feedback loop

Start with the fast offline suite after a Python, shell, or documentation
change:

```bash
source source_me.sh && python3 -m pytest tests/
git diff --check
```

The pytest lane includes unit, integration, Markdown-link, ASCII, whitespace,
import, typing, shebang, and security checks. It intentionally excludes
`tests/e2e/`, so success here does not validate the live Banner path, Mail.app,
or macOS Automation consent.

When shell launch behavior changes, also parse the affected scripts without
starting a daemon or sending mail:

```bash
bash -n run_email_tmux.sh
bash -n tools/run_email_scheduler.sh
bash -n build_course_finder_mailer.sh
```

Use `--help` to confirm a Python command's argument interface without fetching
course data or writing output:

```bash
source source_me.sh && python3 build_grids_from_html.py --help
source source_me.sh && python3 tools/build_grid_from_csv.py --help
source source_me.sh && python3 tools/email_schedule_report.py --help
```

## Verification lanes

Choose the smallest lane that proves the changed behavior.

| Change | Verification |
| --- | --- |
| Parser, filter, renderer, or report logic | Fast pytest suite |
| Local Markdown links or whitespace | The fast suite plus `git diff --check` |
| Root or tool CLI arguments | The relevant `--help` command, then the fast suite |
| Full Banner HTML-to-workbook path | Live E2E command below |
| Native Mail helper source or build script | Rebuild and validate the helper as described below |

The HTML E2E test contacts the live Banner service and writes generated
workbooks under `output/`; use a current six-digit term code. It is deliberately
outside the fast lane. [E2E_TESTS.md](E2E_TESTS.md) defines the test boundary
and [tests/TESTS_README.md](../tests/TESTS_README.md) lists the available tiers.

```bash
source source_me.sh && python3 tests/e2e/e2e_build_grids.py <term>
```

## Native helper work

Changes under `course_finder_mailer/`, `course_scheduling/email_sender.py`, or
`build_course_finder_mailer.sh` cross the Python-to-macOS boundary.
After the fast suite passes, rebuild the helper:

```bash
./build_course_finder_mailer.sh
```

The build compiles the Swift source, applies the checked-in entitlements,
verifies the app signature and plist, and replaces the gitignored
`CourseFinderMailer.app/`. It requires macOS plus Xcode or Xcode Command Line
Tools.

The following is an external side-effect acceptance check, not an ordinary
development smoke test: it opens the Mail automation path and sends a real test
email to the fixed operator address.

```bash
source source_me.sh && python3 test_email_permission.py
```

If macOS requests consent, allow CourseFinderMailer to control Mail.app. A
successful fast suite cannot establish the OS-managed Automation grant. See
[INSTALL.md](INSTALL.md) for prerequisites and [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
for recovery steps.

## Maintainer tasks

`devel/` contains maintainer utilities; its
[DEVEL_README.md](../devel/DEVEL_README.md) is the command reference. Use
`--help` before a tool that can write or reorganize repository files.

- Update [CHANGELOG.md](CHANGELOG.md) for every repository change; humans own
  commits.
- Use `devel/bump_version.py` in its default dry-run mode to preview version
  changes, and pass `--apply` only when the release version is decided.
- Use `devel/make_release.py --dry-run` to inspect a source-release plan. It
  reports commands for a human to run; `--write` builds release archives.
- `devel/clean_build.sh` removes generated build and test artifacts while
  retaining dependency installs. `devel/dist_clean.sh` also removes dependency
  installs, so use it only when a full local reset is intended.

## Related references

- [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - component ownership and data flow.
- [FILE_STRUCTURE.md](FILE_STRUCTURE.md) - where source, tests, generated files,
  and developer tools belong.
- [E2E_TESTS.md](E2E_TESTS.md) - slow and external-system test conventions.
- [REPO_STYLE.md](REPO_STYLE.md) - repository, changelog, and release rules.
