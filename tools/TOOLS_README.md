# tools scripts

`tools/` holds standalone entry-point scripts for repository-facing tasks. These
files are not product code and are not an importable library namespace. For
maintainer-only helpers, see [devel/DEVEL_README.md](../devel/DEVEL_README.md).

Use this folder for scripts that users or maintainers run directly to perform a
focused repository task:

- Repository inspection, reporting, or one-off transformations.
- Commands that coordinate a real package's public behavior.
- Small launchers that keep command-line options near the command a person runs.

Do not put reusable library code, runtime application code, or permanent tests
here. Put reusable behavior in an explicit importable package, and keep the
`tools/` file as a thin entry point that imports from that package.

## Import boundary

`tools/`, `devel/`, and `tests/` are support directories, not package roots.
No file imports `tools`, `devel`, or `tests` as a package, including a file that
already lives in one of those directories. A `tools/` script also does not
import a sibling script; shared behavior belongs in a real package instead.

The related folders have narrow, intentional exceptions:

- `devel/` may use flat sibling helpers for vendored development tooling. That
  exception does not permit `devel.*` package imports.
- Tests may use flat, same-directory helpers such as `file_utils`, because
  `tests/conftest.py` and pytest arrange that directory. They do not import
  `tests.file_utils` or another `tests.*` package path.

## Current tool scripts

| File | Kind of work |
| --- | --- |
| [build_grid_from_csv.py](build_grid_from_csv.py) | Build one schedule grid from a draft CSV export. |
| [email_schedule_report.py](email_schedule_report.py) | Run change detection once or on its schedule. |
| [run_email_scheduler.sh](run_email_scheduler.sh) | Supervise the scheduled report loop for the root tmux launcher. |

## Migration direction

The support-directory gate is detection only. When propagation reports a
violation, the consumer repository's maintainer owns the repair; this template
does not modify consumer code.

Move reusable behavior into the consumer's real package and leave a thin
`tools/` entry point behind. A test that must exercise a standalone script may
instead load it by file path, as
`protein-image-grader/tests/test_copy_archive_images.py` does, without making
`tools/` a package.

The completed audit identifies these original plan-audited consumers and their
migration targets:

| Consumer repository | Module that moves into its package |
| --- | --- |
| `populous-python-nvl` | `tools.headless_runner` into `populous_game/` |
| `iptv-filters` | `tools.validate_m3u` into `iptv_filters/` |
| `marp-slides` | `tools.pptx_to_marp` into `marp_lib/` |
| `track-runner-virtual-dolly-cam` | `tools.refresh_mode_docs` into `track_runner/` |

The original four reports remain test importers, but the completed survey found
runtime drift too: `populous-python-nvl` imports `tools.headless_runner` from
runtime and smoke code, while `marp-slides` tool scripts import
`odp_to_marp`, `odp_visibility`, and `pptx_to_marp` from each other. Those
findings use the same package-plus-thin-script migration; they do not widen the
support-directory exception.

## Running scripts

For Python scripts, use the repo bootstrap environment:

```bash
source source_me.sh && python3 tools/<script>.py
```

Run individual scripts with `--help` for current options. Keep command details
in script help output instead of duplicating them here.
