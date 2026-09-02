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
# The daemon uses a dedicated tmux server and a 'course_email' session. Attach with:
#   tmux -L course_email_daemon attach -t course_email

SESSION_NAME="course_email"
TMUX_SOCKET="course_email_daemon"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
LOGFILE="$REPO_ROOT/logs/email_schedule_report.log"
STARTUP_STATUS_FILE="$REPO_ROOT/logs/email_scheduler_startup_$$.status"
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
if tmux -L "$TMUX_SOCKET" has-session -t "$SESSION_NAME" 2>/dev/null; then
	echo "Session '$SESSION_NAME' already running."
	echo "  attach: tmux -L $TMUX_SOCKET attach -t $SESSION_NAME"
	exit 0
fi

# Do not start a second daemon while the old default-socket session exists.
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
	echo "ERROR: A legacy '$SESSION_NAME' session is running on the default tmux server."
	echo "Stop it first: tmux kill-session -t $SESSION_NAME"
	echo "Then rerun this launcher from Terminal.app."
	exit 1
fi

echo "Starting the dedicated tmux server and Mail.app permission test..."
echo "If macOS asks for Automation access, click Allow."
echo "Starting tmux session '$SESSION_NAME'..."
mkdir -p "$REPO_ROOT/logs"
SUPERVISOR_COMMAND="./tools/run_email_scheduler.sh \"$TERM_CODE\" \"$STARTUP_STATUS_FILE\""
if [ "$REFRESH_BASELINE_ON" -eq 0 ]; then
	SUPERVISOR_COMMAND+=" --skip-baseline-refresh"
fi
TMUX_COMMAND="cd \"$REPO_ROOT\" && source source_me.sh && exec $SUPERVISOR_COMMAND"
if ! tmux -L "$TMUX_SOCKET" new-session -d -s "$SESSION_NAME" "$TMUX_COMMAND"; then
	echo "ERROR: tmux could not create session '$SESSION_NAME'."
	exit 1
fi

# Wait for an explicit result instead of treating process liveness as readiness.
while [ ! -f "$STARTUP_STATUS_FILE" ]; do
	if ! tmux -L "$TMUX_SOCKET" has-session -t "$SESSION_NAME" 2>/dev/null; then
		echo "ERROR: Session '$SESSION_NAME' exited before reporting startup status."
		echo "Check $LOGFILE for the startup error."
		exit 1
	fi
	sleep 1
done

IFS= read -r STARTUP_STATE < "$STARTUP_STATUS_FILE"
rm -f "$STARTUP_STATUS_FILE"
if [ "$STARTUP_STATE" != "ready" ]; then
	echo "ERROR: Mail.app permission test failed; scheduler was not started."
	echo "Check $LOGFILE, then relaunch from a prompt-capable Terminal.app session."
	exit 1
fi

echo "Mail.app permission test passed; session '$SESSION_NAME' started."
echo "  attach: tmux -L $TMUX_SOCKET attach -t $SESSION_NAME"
echo "  log:    $LOGFILE"
