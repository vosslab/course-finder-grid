#!/usr/bin/env python3
"""Build an Excel schedule grid from a draft-schedule CSV file (thin CLI)."""

# Standard Library
import os
import sys
import argparse

# Add repo root to sys.path so course_scheduling is importable when
# this script is run from any directory (e.g. python3 tools/build_grid_from_csv.py).
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
	sys.path.insert(0, _repo_root)

# local repo modules
import course_scheduling.cs_cli
import course_scheduling.csv_courses
import course_scheduling.grid_model
import course_scheduling.xlsx_writer


#============================================

def parse_args() -> argparse.Namespace:
	"""
	Parse command-line arguments.

	Returns:
		argparse.Namespace with input_file, output_file, and common filter flags.
	"""
	parser = argparse.ArgumentParser(
		description='Build an Excel schedule grid from a draft-schedule CSV file.'
	)
	# Input/output file arguments
	parser.add_argument(
		'-i', '-f', '--file', dest='input_file', required=True,
		help='Path to the CSV file with class data',
	)
	parser.add_argument(
		'-o', '--output', dest='output_file',
		help='Output path for the Excel grid file (derived from filters if omitted)',
	)
	# Shared filter flags (campus, level, number series, subject, lab-only)
	course_scheduling.cs_cli.add_common_filters(parser)
	return parser.parse_args()


#============================================

def main() -> None:
	"""
	Parse a draft-schedule CSV into an Excel schedule grid.

	Loads grid rows from the input CSV applying the FilterSpec, builds the
	in-memory schedule grid, then writes the Excel spreadsheet to the output
	path (or a name derived from the active filters).
	"""
	args = parse_args()

	# Build a FilterSpec from the parsed args (single argparse->FilterSpec boundary).
	filter_spec = course_scheduling.cs_cli.filter_spec_from_args(args)

	# Load and filter grid rows from the CSV file.
	classes = course_scheduling.csv_courses.load_grid_rows(args.input_file, filter_spec)
	sorted_classes = sorted(classes, key=lambda row: row["Label"])

	# Build the in-memory schedule grid from the sorted rows.
	schedule_grid = course_scheduling.grid_model.populate_schedule_grid(sorted_classes)

	# Determine the output filename (explicit arg or derived from filter selections).
	output_file = args.output_file if args.output_file else course_scheduling.cs_cli.output_filename_from_args(args)

	# Render and write the Excel spreadsheet.
	course_scheduling.xlsx_writer.create_spreadsheet(schedule_grid, sorted_classes, output_file)


if __name__ == '__main__':
	main()
