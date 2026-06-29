# Course Schedule Email Reporter

Generates color-coded weekly schedule grids as Excel workbooks from course-listing HTML pages or CSV enrollment exports; lays sections on 15-minute time slots with subject and level colors; and emails enrollment-change reports on a tmux schedule.

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
