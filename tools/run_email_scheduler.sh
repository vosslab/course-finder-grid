#!/bin/bash

# Keep the pure-stdlib email scheduler running inside tmux.
# Each scheduled report remains a short-lived Python child process.

RESTART_DELAY=60
REFRESH_BASELINE_ON=1

if [ "$#" -eq 1 ]; then
	:
elif [ "$#" -eq 2 ] && {
		[ "$2" = "--skip-baseline-refresh" ] || [ "$2" = "--no-prime" ]
	}; then
	REFRESH_BASELINE_ON=0
else
	echo "Usage: $0 TERM_CODE [--skip-baseline-refresh]"
	exit 1
fi

TERM_CODE="$1"

# Treat an interactive interrupt or tmux termination as an intentional stop.
trap 'exit 130' INT
trap 'exit 143' TERM

log_supervisor_event() {
	MESSAGE="$1"
	# Use the same bounded rotating handler as the Python report processes.
	if ! python3 -m course_scheduling.report_logging "$MESSAGE"; then
		TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
		echo "$TIMESTAMP WARNING $MESSAGE"
	fi
}

if [ "$REFRESH_BASELINE_ON" -eq 1 ]; then
	python3 tools/email_schedule_report.py --term "$TERM_CODE" --refresh-baseline
	REFRESH_EXIT_CODE=$?
	if [ "$REFRESH_EXIT_CODE" -eq 130 ] || [ "$REFRESH_EXIT_CODE" -eq 143 ]; then
		exit "$REFRESH_EXIT_CODE"
	fi
	if [ "$REFRESH_EXIT_CODE" -ne 0 ]; then
		MESSAGE="Baseline refresh exited with status $REFRESH_EXIT_CODE;"
		MESSAGE+=" starting scheduler with the existing cache"
		log_supervisor_event "$MESSAGE"
	fi
fi

while true; do
	python3 tools/email_schedule_report.py --loop --term "$TERM_CODE"
	EXIT_CODE=$?

	# Signal exits are intentional and should not be restarted.
	if [ "$EXIT_CODE" -eq 130 ] || [ "$EXIT_CODE" -eq 143 ]; then
		exit "$EXIT_CODE"
	fi

	MESSAGE="Email scheduler exited with status $EXIT_CODE;"
	MESSAGE+=" restarting in $RESTART_DELAY seconds"
	log_supervisor_event "$MESSAGE"
	sleep "$RESTART_DELAY"
done
