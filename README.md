# Course Schedule Email Reporter

Course finder grid generates weekly schedule spreadsheets for Roosevelt University science courses, fetches live Banner enrollment data, and delivers automated email reports to faculty via a tmux-based scheduler.

## Quick start

```bash
source source_me.sh
python3 course_scheduling/course_finder_lib.py
```

## Scheduler

The supported scheduler is the tmux runner. Start it with:

```bash
./course_scheduling/run_email_tmux.sh
```

Attach to the session with `tmux attach -t course_email`. The runner sends
schedule reports Mon-Thu at 8:03am and Fri at 8:03am and 6:07pm.

## Documentation

- [docs/CHANGELOG.md](docs/CHANGELOG.md)
- [docs/AUTHORS.md](docs/AUTHORS.md)
