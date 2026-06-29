# Standard Library
import argparse

# local repo modules
import course_scheduling.cs_cli
import course_scheduling.course_filter


#============================================

def test_filter_spec_from_args_builds_spec() -> None:
	"""filter_spec_from_args maps argparse.Namespace fields to a FilterSpec."""
	args = argparse.Namespace(
		subjects=['BIOL'],
		campus=None,
		levels=['U'],
		number=[100],
		lab_only=False,
	)
	spec = course_scheduling.cs_cli.filter_spec_from_args(args)
	assert isinstance(spec, course_scheduling.course_filter.FilterSpec)
	# spot-check one field to catch a crossed assignment
	assert spec.subjects == ['BIOL']


#============================================

def test_filter_spec_from_args_lab_only() -> None:
	"""filter_spec_from_args sets lab_only when the flag is True."""
	args = argparse.Namespace(
		subjects=None,
		campus=None,
		levels=None,
		number=None,
		lab_only=True,
	)
	spec = course_scheduling.cs_cli.filter_spec_from_args(args)
	assert spec.lab_only is True
