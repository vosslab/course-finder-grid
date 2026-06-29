"""
Command-layer argument adapter for course-scheduling CLI commands.

This is the one module under course_scheduling/ that imports argparse.
Every other course_scheduling module stays argparse-free. Entry-point
scripts call the three public functions here to share flag definitions
and to convert parsed Namespace values into library-facing types.
"""

# Standard Library
import argparse

# local repo modules
import course_scheduling.course_filter
import course_scheduling.output_naming


#============================================

def add_common_filters(parser: argparse.ArgumentParser) -> None:
	"""
	Add the shared course-filter flags to an argument parser.

	Covers campus, level, course-number series, subject, and lab-only filters.
	Every command that accepts these flags calls this function once so the
	flag definitions stay in a single place.

	Args:
		parser: The argparse ArgumentParser to augment.
	"""
	# Campus filters: append a campus constant to the campus list
	parser.add_argument('-s', '--schaumburg', dest='campus', action='append_const', const='SCHAUMBURG CAMPUS', help='Filter for Schaumburg campus')
	parser.add_argument('-c', '--chicago', dest='campus', action='append_const', const='CHICAGO CAMPUS', help='Filter for Chicago campus')
	# Level filters: U for undergraduate, G for graduate
	parser.add_argument('-u', '--undergrad', '--undergraduate', dest='levels', action='append_const', const='U', help='Filter for undergraduate level classes')
	parser.add_argument('-g', '--grad', '--graduate', dest='levels', action='append_const', const='G', help='Filter for graduate level classes')
	# Course number series filter (100, 200, 300, 400)
	parser.add_argument('-n', '--number', type=int, choices=[100, 200, 300, 400],
		action='append', help='Filter for specific course number series (100, 200, 300, 400)')
	# Subject flags: repeatable append_const per subject code
	parser.add_argument('--biol', dest='subjects', action='append_const', const='BIOL', help='Filter for BIOL subject')
	parser.add_argument('--chem', dest='subjects', action='append_const', const='CHEM', help='Filter for CHEM subject')
	parser.add_argument('--phys', dest='subjects', action='append_const', const='PHYS', help='Filter for PHYS subject')
	parser.add_argument('--bchm', dest='subjects', action='append_const', const='BCHM', help='Filter for BCHM subject')
	parser.add_argument('--math', dest='subjects', action='append_const', const='MATH', help='Filter for MATH subject')
	# Lab-only mode: keep only sections that look like lab meetings
	parser.add_argument('--lab-only', action='store_true', help='Filter for likely lab sections only')


#============================================

def filter_spec_from_args(args: argparse.Namespace) -> course_scheduling.course_filter.FilterSpec:
	"""
	Build a FilterSpec from parsed command-line arguments.

	This is the single argparse->FilterSpec boundary; every command that
	accepts filter flags calls this to convert the parsed Namespace into a
	FilterSpec that the library can consume without importing argparse.

	Args:
		args: Parsed argparse Namespace; must carry subjects, campus, levels,
			number, and lab_only attributes (as populated by add_common_filters).

	Returns:
		course_scheduling.course_filter.FilterSpec: Populated filter spec.
	"""
	filter_spec = course_scheduling.course_filter.FilterSpec(
		subjects=args.subjects,
		campus=args.campus,
		levels=args.levels,
		number=args.number,
		lab_only=args.lab_only,
	)
	return filter_spec


#============================================

def output_filename_from_args(args: argparse.Namespace) -> str:
	"""
	Derive an output filename from the active filter selections in parsed args.

	Args:
		args: Parsed argparse Namespace; must carry subjects, levels, number,
			and campus attributes (as populated by add_common_filters).

	Returns:
		str: Generated output filename.
	"""
	filename = course_scheduling.output_naming.generate_output_filename(
		args.subjects, args.levels, args.number, args.campus
	)
	return filename
