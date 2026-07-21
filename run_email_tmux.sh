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
#   ./run_email_tmux.sh --no-prime
#
# The tmux session is named 'course_email'. Attach with:
#   tmux attach -t course_email

SESSION_NAME="course_email"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
LOGFILE="$REPO_ROOT/logs/email_schedule_report.log"
TERM_CODE="202710"
PRIME_ON=1

if [ "$#" -eq 0 ]; then
	:
elif [ "$#" -eq 1 ] && [ "$1" = "--no-prime" ]; then
	PRIME_ON=0
else
	echo "Usage: $0 [--no-prime]"
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
if [ "$PRIME_ON" -eq 1 ]; then
	TMUX_COMMAND="cd $REPO_ROOT && source source_me.sh && python3 tools/email_schedule_report.py -t $TERM_CODE --prime && python3 tools/email_schedule_report.py --loop --term $TERM_CODE"
else
	TMUX_COMMAND="cd $REPO_ROOT && source source_me.sh && python3 tools/email_schedule_report.py --loop --term $TERM_CODE"
fi

tmux new-session -d -s "$SESSION_NAME" \
	"$TMUX_COMMAND"
sleep 1

echo "Session '$SESSION_NAME' started."
echo "  attach: tmux attach -t $SESSION_NAME"
echo "  log:    $LOGFILE"
