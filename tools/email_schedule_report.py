#!/usr/bin/env python3
"""Email schedule report: one-shot or recurring --loop mode."""

# Standard Library
import os
import sys
import logging
import argparse
import subprocess

# Add repo root to sys.path so course_scheduling and cli are importable when
# this script is run from any directory (e.g. python3 tools/email_schedule_report.py).
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
	sys.path.insert(0, _repo_root)

# local repo modules
import course_scheduling.report_logging
import course_scheduling.report_scheduler

# Default science subject set; the library is subject-agnostic.
# Override with --subject to run another department's subject set.
DEFAULT_SUBJECTS = ["BIOL", "PHYS", "CHEM", "BCHM"]


#============================================

def build_child_command(term_code: str, subjects: list) -> list:
	"""
	Build the one-shot scheduled-report command for a term and subject set.

	Args:
		term_code: Banner term code.
		subjects: Subject codes to check and grid across.

	Returns:
		Argument vector for a sending one-shot child process.
	"""
	command = [sys.executable, os.path.abspath(__file__), '-t', term_code]
	for subject in subjects:
		command.extend(['--subject', subject])
	command.append('-e')
	return command


#============================================

def parse_args() -> argparse.Namespace:
	"""
	Parse command-line arguments.

	Returns:
		Arguments with term, subjects, dry-run, loop, and baseline-refresh state.
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
	mode_group = parser.add_mutually_exclusive_group()
	mode_group.add_argument(
		'--loop', action='store_true',
		help='Run on a recurring schedule (Mon-Thu 8:03am, Fri 8:03am + 6:07pm)',
	)
	mode_group.add_argument(
		'--refresh-baseline', '--prime', dest='refresh_baseline',
		action='store_true',
		help='Fetch and save a baseline without composing or sending email',
	)
	args = parser.parse_args()
	# Apply the science default if no --subject flags were given.
	if not args.subjects:
		args.subjects = list(DEFAULT_SUBJECTS)
	return args


#============================================

def process_mode(args: argparse.Namespace) -> str:
	"""
	Return the human-readable execution mode for logging.

	Args:
		args: Parsed command-line arguments.

	Returns:
		One of loop, baseline-refresh, dry-run, or send.
	"""
	if args.loop:
		return "loop"
	if args.refresh_baseline:
		return "baseline-refresh"
	if args.dry_run:
		return "dry-run"
	return "send"


#============================================

def run_mode(args: argparse.Namespace) -> None:
	"""
	Run the selected report mode after logging is configured.

	In --loop mode the callback is bound with the term and subjects so the
	scheduler stays term- and subject-agnostic. In single-shot mode the report
	runs once (dry-run by default; pass -e/--send-email to send). The
	--refresh-baseline mode fetches and persists a snapshot without an email.
	"""
	term_code = args.term_code
	subjects = args.subjects
	if args.loop:
		logging.info(
			"Email scheduler loop starting: term=%s subjects=%s",
			term_code,
			",".join(subjects),
		)
		# Bind the sending child command into a zero-argument scheduler callback.
		def report_callback() -> None:
			"""Run one scheduled report pass in a short-lived sending child."""
			command = build_child_command(term_code, subjects)
			logging.info(
				"Scheduled report child starting: term=%s subjects=%s",
				term_code,
				",".join(subjects),
			)
			result = subprocess.run(command, check=False)
			if result.returncode != 0:
				logging.error(
					"Scheduled report child failed: term=%s exit_code=%d; scheduler continues",
					term_code,
					result.returncode,
				)
			else:
				logging.info("Scheduled report child completed: term=%s", term_code)
		course_scheduling.report_scheduler.run_loop(report_callback)
		return

	import course_scheduling.report_pipeline as report_pipeline
	if args.refresh_baseline:
		report_pipeline.refresh_baseline(term_code, subjects)
		return
	report_pipeline.run_report(term_code, subjects, args.dry_run)


#============================================

def main() -> None:
	"""
	Configure logging and run one report-process mode.
	"""
	args = parse_args()
	course_scheduling.report_logging.setup_logging()
	mode = process_mode(args)
	logging.info(
		"Email schedule process starting: mode=%s term=%s subjects=%s",
		mode,
		args.term_code,
		",".join(args.subjects),
	)
	try:
		run_mode(args)
	except Exception:
		course_scheduling.report_logging.log_process_failure(
			mode, args.term_code, args.subjects
		)
		raise


if __name__ == '__main__':
	main()
