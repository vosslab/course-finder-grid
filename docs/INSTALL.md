# Install

This repository runs directly from its source tree; it has no package-install step. Use Python
3.12 through `source source_me.sh && python3` for every Python command.

## Requirements

- Python 3.12 via Homebrew
- For the optional email daemon: macOS, tmux, Xcode or Xcode Command Line Tools
  with Swift, a configured Mail.app account, and Automation permission for
  CourseFinderMailer to control Mail.app.

## Install steps

1. Clone the repo and enter it:

   ```bash
   git clone <repo-url>
   cd course-finder-grid
   ```

2. Install the declared Homebrew dependency (Python 3.12):

   ```bash
   brew bundle
   ```

3. Install Python runtime dependencies with the project interpreter:

   ```bash
   source source_me.sh && python3 -m pip install -r pip_requirements.txt
   ```

4. Install development dependencies when you will run tests:

   ```bash
   source source_me.sh && python3 -m pip install -r pip_requirements-dev.txt
   ```

## Verify install

```bash
source source_me.sh && python3 build_grids_from_html.py --help
```

Expected output: a usage message listing `-t / --term` and `--subject`.

## Email daemon setup

Grid generation does not require the native helper. On macOS, build the optional
email helper at the repository root, then run the permission test. Click **Allow**
if macOS asks whether CourseFinderMailer may control Mail:

```bash
./build_course_finder_mailer.sh
source source_me.sh && python3 test_email_permission.py
```

Then launch the daemon. Each launch runs another test email and starts scheduling only after
the same helper identity succeeds:

```bash
./run_email_tmux.sh
```

See [USAGE.md](USAGE.md#email-report-daemon-tmux) for the helper permission, rebuild, and
session workflows.

## Troubleshooting

If the helper build cannot find Swift, install Xcode or Xcode Command Line Tools. The build
script invokes `xcrun swiftc`, verifies the app signature, and validates its `Info.plist`.

If the permission test is denied, enable CourseFinderMailer under **System Settings > Privacy &
Security > Automation**, then rerun the test. Rebuilding the helper gives it a new local ad-hoc
signature, so macOS can request Automation permission again.

## Known gaps

- tmux is used by `run_email_tmux.sh` but is not listed in `Brewfile`; install it separately
  with `brew install tmux` before using the daemon workflow.
- Email sending via Mail.app is macOS-only; Linux and Windows are untested.
