#!/bin/bash

# Keep the pure-stdlib email scheduler running inside tmux.
# Each scheduled report remains a short-lived Python child process.

RESTART_DELAY=60

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 TERM_CODE"
	exit 1
fi

TERM_CODE="$1"

# Treat an interactive interrupt or tmux termination as an intentional stop.
trap 'exit 130' INT
trap 'exit 143' TERM

while true; do
	python3 tools/email_schedule_report.py --loop --term "$TERM_CODE"
	EXIT_CODE=$?

	# Signal exits are intentional and should not be restarted.
	if [ "$EXIT_CODE" -eq 130 ] || [ "$EXIT_CODE" -eq 143 ]; then
		exit "$EXIT_CODE"
	fi

	MESSAGE="Email scheduler exited with status $EXIT_CODE;"
	MESSAGE+=" restarting in $RESTART_DELAY seconds"
	# Use the same bounded rotating handler as the Python report processes.
	if ! python3 -m course_scheduling.report_logging "$MESSAGE"; then
		TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
		echo "$TIMESTAMP WARNING $MESSAGE"
	fi
	sleep "$RESTART_DELAY"
done
