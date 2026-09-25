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
#   ./run_email_tmux.sh --no-prime
#
# The daemon uses the default tmux server and a short 'cfmail' session. Attach with:
#   tmux attach -t cfmail

SESSION_NAME="cfmail"
ISOLATED_SESSION_NAME="cfmail"
ISOLATED_TMUX_SOCKET="cfmail"
LEGACY_SESSION_NAME="course_email"
LEGACY_TMUX_SOCKET="course_email_daemon"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
LOGFILE="$REPO_ROOT/logs/email_schedule_report.log"
MAILER_EXECUTABLE="$REPO_ROOT/CourseFinderMailer.app/Contents/MacOS/CourseFinderMailer"
TERM_CODE="202720"
REFRESH_BASELINE_ON=1

if [ "$#" -eq 0 ]; then
	:
elif [ "$#" -eq 1 ] && {
		[ "$1" = "--skip-baseline-refresh" ] || [ "$1" = "--no-prime" ]
	}; then
	REFRESH_BASELINE_ON=0
else
	echo "Usage: $0 [--skip-baseline-refresh|--no-prime]"
	exit 1
fi

export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

if [ ! -x "$MAILER_EXECUTABLE" ]; then
	echo "ERROR: CourseFinderMailer.app is missing or not executable."
	echo "Build it first: ./build_course_finder_mailer.sh"
	exit 1
fi

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
	echo "Session '$SESSION_NAME' already running."
	echo "  attach: tmux attach -t $SESSION_NAME"
	exit 0
fi

# Do not start a duplicate while the briefly used 'cfmail' isolated server runs.
if tmux -L "$ISOLATED_TMUX_SOCKET" has-session -t "$ISOLATED_SESSION_NAME" 2>/dev/null; then
	echo "ERROR: The daemon is still running on the isolated tmux server."
	echo "  attach: tmux -L $ISOLATED_TMUX_SOCKET attach -t $ISOLATED_SESSION_NAME"
	echo "Remove that server before starting the visible default-server session:"
	echo "  tmux -L $ISOLATED_TMUX_SOCKET kill-server"
	exit 1
fi

# Do not start a second daemon while the previous dedicated server is running.
if tmux -L "$LEGACY_TMUX_SOCKET" has-session -t "$LEGACY_SESSION_NAME" 2>/dev/null; then
	echo "ERROR: The daemon is still running under its previous tmux names."
	echo "  attach: tmux -L $LEGACY_TMUX_SOCKET attach -t $LEGACY_SESSION_NAME"
	echo "Stop that session before migrating:"
	echo "  tmux -L $LEGACY_TMUX_SOCKET kill-session -t $LEGACY_SESSION_NAME"
	echo "Then rerun this launcher."
	exit 1
fi

# Do not start a second daemon while the old default-socket session exists.
if tmux has-session -t "$LEGACY_SESSION_NAME" 2>/dev/null; then
	echo "ERROR: A legacy '$LEGACY_SESSION_NAME' session is running on the default tmux server."
	echo "Stop it first: tmux kill-session -t $LEGACY_SESSION_NAME"
	echo "Then rerun this launcher."
	exit 1
fi

echo "Starting the default-server tmux session and Mail.app permission test..."
echo "If macOS asks whether CourseFinderMailer may control Mail, click Allow."
echo "Starting tmux session '$SESSION_NAME'..."
mkdir -p "$REPO_ROOT/logs"

# A private unique directory prevents a stale or planted status file from
# satisfying this launch's fail-closed permission gate.
if ! STARTUP_STATUS_DIR="$(
	mktemp -d "$REPO_ROOT/logs/email_scheduler_startup.XXXXXX"
)"; then
	echo "ERROR: Could not create the private startup-status directory."
	exit 1
fi
STARTUP_STATUS_FILE="$STARTUP_STATUS_DIR/status"

cleanup_startup_status() {
	rm -f "$STARTUP_STATUS_FILE"
	rmdir "$STARTUP_STATUS_DIR" 2>/dev/null || true
}

SUPERVISOR_COMMAND="./tools/run_email_scheduler.sh \"$TERM_CODE\" \"$STARTUP_STATUS_FILE\""
if [ "$REFRESH_BASELINE_ON" -eq 0 ]; then
	SUPERVISOR_COMMAND+=" --skip-baseline-refresh"
fi
TMUX_COMMAND="cd \"$REPO_ROOT\" && source source_me.sh && exec $SUPERVISOR_COMMAND"
if ! tmux new-session -d -s "$SESSION_NAME" "$TMUX_COMMAND"; then
	cleanup_startup_status
	echo "ERROR: tmux could not create session '$SESSION_NAME'."
	exit 1
fi

# Wait for an explicit result instead of treating process liveness as readiness.
while [ ! -f "$STARTUP_STATUS_FILE" ]; do
	if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
		cleanup_startup_status
		echo "ERROR: Session '$SESSION_NAME' exited before reporting startup status."
		echo "Check $LOGFILE for the startup error."
		exit 1
	fi
	sleep 1
done

IFS= read -r STARTUP_STATE < "$STARTUP_STATUS_FILE"
cleanup_startup_status
if [ "$STARTUP_STATE" != "ready" ]; then
	echo "ERROR: Mail.app permission test failed; scheduler was not started."
	echo "Check $LOGFILE for the native helper or Mail Automation error."
	echo "In System Settings > Privacy & Security > Automation, allow"
	echo "CourseFinderMailer to control Mail, then run this launcher again."
	exit 1
fi

echo "Mail.app permission test passed; session '$SESSION_NAME' started."
echo "  attach: tmux attach -t $SESSION_NAME"
echo "  log:    $LOGFILE"
