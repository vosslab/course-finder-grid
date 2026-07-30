#!/bin/bash

# Launch course schedule email in a tmux session.
# Replaces the launchd plist which cannot send emails via Mail.app.
#
# Schedule (matches the old plist):
#   Mon-Thu: 8:03am
#   Fri:     8:03am and 6:07pm
#
# Usage:
#   ./run_email_tmux.sh
#   ./run_email_tmux.sh --skip-baseline-refresh
#
# The tmux session is named 'course_email'. Attach with:
#   tmux attach -t course_email

SESSION_NAME="course_email"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
LOGFILE="$REPO_ROOT/logs/email_schedule_report.log"
TERM_CODE="202710"
REFRESH_BASELINE_ON=1

if [ "$#" -eq 0 ]; then
	:
elif [ "$#" -eq 1 ] && {
		[ "$1" = "--skip-baseline-refresh" ] || [ "$1" = "--no-prime" ]
	}; then
	REFRESH_BASELINE_ON=0
else
	echo "Usage: $0 [--skip-baseline-refresh]"
	exit 1
fi

export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
	echo "Session '$SESSION_NAME' already running."
	echo "  attach: tmux attach -t $SESSION_NAME"
	exit 0
fi

echo "Starting tmux session '$SESSION_NAME'..."
SUPERVISOR_COMMAND="./tools/run_email_scheduler.sh \"$TERM_CODE\""
if [ "$REFRESH_BASELINE_ON" -eq 0 ]; then
	SUPERVISOR_COMMAND+=" --skip-baseline-refresh"
fi
TMUX_COMMAND="cd \"$REPO_ROOT\" && source source_me.sh && exec $SUPERVISOR_COMMAND"
if ! tmux new-session -d -s "$SESSION_NAME" "$TMUX_COMMAND"; then
	echo "ERROR: tmux could not create session '$SESSION_NAME'."
	exit 1
fi
sleep 1

if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
	echo "ERROR: Session '$SESSION_NAME' exited during daemon startup."
	echo "Run the supervisor in the foreground to inspect the startup error:"
	echo "  cd \"$REPO_ROOT\" && source source_me.sh && $SUPERVISOR_COMMAND"
	exit 1
fi

echo "Session '$SESSION_NAME' started."
echo "  attach: tmux attach -t $SESSION_NAME"
echo "  log:    $LOGFILE"
