# Course Schedule Email Reporter

Automated schedule grid for Roosevelt University science courses: generates weekly Excel spreadsheets from Banner enrollment data and delivers faculty email reports via a tmux-based scheduler.

## Quick start

Start the tmux-based scheduler:

```bash
./course_scheduling/run_email_tmux.sh
```

Attach to the running session:

```bash
tmux attach -t course_email
```

The runner sends schedule reports Mon-Thu at 8:03am and Fri at 8:03am and 6:07pm.

## Documentation

- [docs/AUTHORS.md](docs/AUTHORS.md): project maintainers and contributors.
- [docs/CHANGELOG.md](docs/CHANGELOG.md): chronological record of changes.
