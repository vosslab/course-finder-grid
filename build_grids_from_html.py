#!/usr/bin/env python3

"""Generate schedule grid workbooks from Banner HTML course data.

Downloads course HTML for each subject, builds filtered schedule grids,
and merges them into a single multi-tab xlsx workbook.
"""

# Standard Library
import os
import argparse

# local repo modules
import course_scheduling.workbook_builder

# Science default subject set; the library is subject-agnostic and takes
# subjects as a parameter. The default lives here at the command layer,
# not in the library, so the library stays general.
_DEFAULT_SUBJECTS = ["BIOL", "PHYS", "CHEM", "BCHM"]


#============================================
def parse_args() -> argparse.Namespace:
	"""Parse command-line arguments."""
	parser = argparse.ArgumentParser(
		description="Generate schedule grid workbooks from Banner HTML course data."
	)
	parser.add_argument(
		'-t', '--term', dest='term_code', required=True,
		help="Banner term code, e.g. 202710"
	)
	# Repeatable --subject flag; the science default is applied in main()
	# when no subject flag is given. Defaults to None so any explicit subject
	# flag replaces the whole default set rather than appending to it.
	parser.add_argument(
		'--subject', dest='subjects', action='append', metavar='SUBJECT',
		help='Subject code to include (repeatable; default: BIOL PHYS CHEM BCHM)'
	)
	args = parser.parse_args()
	return args


#============================================
def main() -> None:
	"""Main entry point."""
	args = parse_args()
	term_code = args.term_code
	# Apply the science default when no subject flags were given.
	subjects = args.subjects if args.subjects else list(_DEFAULT_SUBJECTS)
	# This script lives at the repo root; all generated outputs live under
	# the repo-root output/ dir, kept out of the course_scheduling/ package.
	repo_root = os.path.dirname(os.path.abspath(__file__))
	output_dir = os.path.join(repo_root, 'output')
	os.makedirs(output_dir, exist_ok=True)
	# Build the preset grid-config matrix for this term and subject set,
	# then run the full download -> parse -> grid -> merge pipeline.
	grid_configs = course_scheduling.workbook_builder.default_grid_configs(term_code, subjects, output_dir)
	xlsx_path = course_scheduling.workbook_builder.build_term_workbook(term_code, subjects, grid_configs, output_dir)
	# The final stdout line is the merged workbook path.
	print(xlsx_path)


if __name__ == '__main__':
	main()
