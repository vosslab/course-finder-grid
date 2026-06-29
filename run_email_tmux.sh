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
#
# The tmux session is named 'course_email'. Attach with:
#   tmux attach -t course_email

SESSION_NAME="course_email"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
LOGFILE="$REPO_ROOT/logs/email_schedule_report.log"
TERM_CODE="202710"

export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
	echo "Session '$SESSION_NAME' already running."
	echo "  attach: tmux attach -t $SESSION_NAME"
	exit 0
fi

echo "Starting tmux session '$SESSION_NAME'..."
tmux new-session -d -s "$SESSION_NAME" \
	"cd $REPO_ROOT && source source_me.sh && python3 tools/email_schedule_report.py --loop --term $TERM_CODE"
sleep 1

echo "Session '$SESSION_NAME' started."
echo "  attach: tmux attach -t $SESSION_NAME"
echo "  log:    $LOGFILE"
