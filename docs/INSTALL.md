# Install

This repo provides scripts run directly from the source tree - no package installation step
required. After cloning, install system and Python dependencies, then run any entry point via
`source source_me.sh && python3`.

## Requirements

- macOS (py-applescript uses Mail.app; email-send path is macOS-only)
- Python 3.12 via Homebrew
- tmux (required for the `run_email_tmux.sh` daemon workflow)

## Install steps

1. Clone the repo and enter it:

   ```bash
   git clone <repo-url>
   cd course-finder-grid
   ```

2. Install Homebrew dependencies (Python 3.12):

   ```bash
   brew bundle
   ```

3. Install Python runtime dependencies:

   ```bash
   python3 -m pip install -r pip_requirements.txt
   ```

4. (Optional) Install development dependencies for running tests:

   ```bash
   python3 -m pip install -r pip_requirements-dev.txt
   ```

## Verify install

```bash
source source_me.sh && python3 build_grids_from_html.py --help
```

Expected output: usage message listing `-t / --term` and `--subject` flags.

## Known gaps

- tmux is used by `run_email_tmux.sh` but is not listed in `Brewfile`; install it
  separately with `brew install tmux` before using the daemon workflow.
- Email sending via Mail.app is macOS-only; Linux and Windows are untested.
