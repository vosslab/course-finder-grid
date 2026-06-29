#!/usr/bin/env python3
"""Email schedule report: one-shot or recurring --loop mode."""

# Standard Library
import os
import sys
import argparse

# Add repo root to sys.path so course_scheduling and cli are importable when
# this script is run from any directory (e.g. python3 tools/email_schedule_report.py).
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
	sys.path.insert(0, _repo_root)

# local repo modules
import course_scheduling.report_pipeline
import course_scheduling.report_scheduler

# Default science subject set; the library is subject-agnostic.
# Override with --subject to run another department's subject set.
DEFAULT_SUBJECTS = ["BIOL", "PHYS", "CHEM", "BCHM"]


#============================================

def parse_args() -> argparse.Namespace:
	"""
	Parse command-line arguments.

	Returns:
		argparse.Namespace with term_code, subjects, dry_run, and loop.
	"""
	parser = argparse.ArgumentParser(
		description="Download course HTML, detect changes, and email schedule grid xlsx."
	)
	parser.add_argument(
		'-t', '--term', dest='term_code', required=True,
		help='Banner term code, for example 202710',
	)
	parser.add_argument(
		'--subject', dest='subjects', action='append', metavar='SUBJ',
		help='Subject code (repeatable; default: BIOL PHYS CHEM BCHM)',
	)
	parser.add_argument(
		'-e', '--send-email', dest='dry_run', action='store_false',
		help='Send the email (default is dry-run mode)',
	)
	parser.add_argument(
		'-n', '--dry-run', dest='dry_run', action='store_true',
		help='Only detect changes; do not send email',
	)
	parser.set_defaults(dry_run=True)
	parser.add_argument(
		'--loop', action='store_true',
		help='Run on a recurring schedule (Mon-Thu 8:03am, Fri 8:03am + 6:07pm)',
	)
	args = parser.parse_args()
	# Apply the science default if no --subject flags were given.
	if not args.subjects:
		args.subjects = list(DEFAULT_SUBJECTS)
	return args


#============================================

def main() -> None:
	"""
	Run the email schedule report once, or loop on a recurring schedule.

	In --loop mode the callback is bound with the term and subjects so the
	scheduler stays term- and subject-agnostic. In single-shot mode the report
	runs once (dry-run by default; pass -e/--send-email to send).
	"""
	args = parse_args()
	term_code = args.term_code
	subjects = args.subjects
	if args.loop:
		# Bind term and subjects into a zero-argument callback for the scheduler.
		def report_callback() -> None:
			"""Run one scheduled report pass (dry_run=False in loop mode)."""
			course_scheduling.report_pipeline.run_report(term_code, subjects, dry_run=False)
		course_scheduling.report_scheduler.run_loop(report_callback)
	else:
		course_scheduling.report_pipeline.run_report(term_code, subjects, args.dry_run)


if __name__ == '__main__':
	main()
