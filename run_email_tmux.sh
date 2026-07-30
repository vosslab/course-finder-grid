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

if [ "$PRIME_ON" -eq 1 ]; then
	echo "Priming the baseline before daemon startup..."
	if (
		cd "$REPO_ROOT" || exit 1
		source source_me.sh || exit 1
		python3 tools/email_schedule_report.py -t "$TERM_CODE" --prime
	); then
		echo "Baseline prime completed."
	else
		echo "WARNING: Baseline prime failed; starting the daemon with the existing cache."
	fi
fi

echo "Starting tmux session '$SESSION_NAME'..."
SUPERVISOR_COMMAND="./tools/run_email_scheduler.sh \"$TERM_CODE\""
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
