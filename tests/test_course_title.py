"""
Tests for Banner course title display formatting.

Banner ships titles in ALL CAPS. These cover the capitalization contract:
readable title case, uppercase tokens preserved, minor words lowered only in
the middle of a title, and digit-bearing tokens left untouched.
"""

# local repo modules
import course_scheduling.course_title


#============================================
# basic title case

def test_all_caps_title_becomes_readable() -> None:
	"""A plain ALL CAPS title renders in title case."""
	result = course_scheduling.course_title.smart_title_case("FOUNDATIONS OF CHEMISTRY")
	assert result == "Foundations of Chemistry"


def test_hyphenated_word_capitalizes_each_part() -> None:
	"""Each hyphen-separated part is capitalized, not just the first."""
	result = course_scheduling.course_title.smart_title_case("HUMAN BIOLOGY-LECT")
	assert result == "Human Biology-Lect"


#============================================
# preserved uppercase tokens

def test_roman_numeral_stays_uppercase() -> None:
	"""A course sequence numeral stays uppercase instead of becoming "Ii"."""
	result = course_scheduling.course_title.smart_title_case("ORGANIC CHEMISTRY II")
	assert result == "Organic Chemistry II"


def test_roman_numeral_inside_a_hyphenated_word_stays_uppercase() -> None:
	"""Real Banner form "GENERAL CHEMISTRY II-LECT" keeps the numeral uppercase."""
	result = course_scheduling.course_title.smart_title_case("GENERAL CHEMISTRY II-LECT")
	assert result == "General Chemistry II-Lect"


#============================================
# minor words and digits

def test_minor_word_stays_capitalized_at_the_edges() -> None:
	"""A minor word capitalizes when it opens or closes the title."""
	result = course_scheduling.course_title.smart_title_case("THE SCIENCE OF THE MIND")
	assert result == "The Science of the Mind"


def test_word_run_together_with_an_ampersand_capitalizes() -> None:
	"""Real Banner form "ANATOMY &PHYSIOLOGY I" capitalizes past the ampersand."""
	result = course_scheduling.course_title.smart_title_case("ANATOMY &PHYSIOLOGY I")
	assert result == "Anatomy &Physiology I"


def test_digit_bearing_token_is_left_alone() -> None:
	"""Course numbers and dimension tokens are not recased."""
	result = course_scheduling.course_title.smart_title_case("BIOLOGY 101 LAB")
	assert result == "Biology 101 Lab"


#============================================
# whitespace contract with the caller

def test_surrounding_and_internal_whitespace_collapses() -> None:
	"""Realistic Banner spacing collapses to single spaces."""
	result = course_scheduling.course_title.smart_title_case("  GENERAL   BIOLOGY  ")
	assert result == "General Biology"
