"""Display formatting for Banner course titles.

Banner supplies course titles in ALL CAPS (for example "FOUNDATIONS OF
CHEMISTRY"), which reads as shouting inside a prose change report. This module
converts a Banner title to readable title case.

Scope decision: Banner's Title column is the source of truth for wording. This
module only changes capitalization. It never rewords, abbreviates, expands, or
reorders a title, so a reader can always match report text back to the Banner
listing. Resist adding further "smart" rewriting here.

Malformed spacing is preserved on purpose. Banner carries sloppy titles such as
"ANATOMY &PHYSIOLOGY I" (no space after the ampersand) and
"GENERAL CHEMISTRY II-DISC& LAB". Those render as "Anatomy &Physiology I" and
"General Chemistry II-Disc& Lab", not tidied to "Anatomy & Physiology I". The
report is a view of the catalog, so a bad title must stay visibly bad; cleaning
it here would hide a data-entry problem that belongs upstream in Banner.

Unknown acronyms: an acronym that is not in ALWAYS_UPPERCASE_WORDS is rendered
as an ordinary word ("MCAT" becomes "Mcat"). That is the intended fallback. Fix
it by adding the token to ALWAYS_UPPERCASE_WORDS, not by adding heuristics.
"""

# Tokens that stay fully uppercase. Checked per hyphen-separated part, so the
# numeral in "II-LECT" is caught as well as a standalone "II".
#
# Roman numerals carry course sequences and are the only entries the cached
# BIOL/PHYS/CHEM/BCHM titles actually exercise today ("GENERAL CHEMISTRY II",
# "ORGANIC CHEMISTRY I-DISC & LAB"). The science acronyms below are held for
# titles that have not appeared yet. Extend this set when a real title shows a
# new one; an unlisted acronym title-cases, which is the documented fallback.
ALWAYS_UPPERCASE_WORDS = {
	"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
	"DNA", "RNA", "PCR", "NMR", "MRI",
}

# Short function words that stay lowercase in the middle of a title.
ALWAYS_LOWERCASE_WORDS = {
	"a", "an", "and", "as", "at", "but", "by", "for", "from", "in",
	"nor", "of", "on", "or", "the", "to", "via", "with",
}


#============================================
def capitalize_first_letter(text: str) -> str:
	"""
	Lowercase text, then uppercase its first alphabetic character.

	str.capitalize() only touches position 0, so it leaves "&PHYSIOLOGY" as
	"&physiology". Banner titles run words together with an ampersand often
	enough that the first letter has to be found rather than assumed.

	Args:
		text: One hyphen-separated part of a title word.

	Returns:
		The part with its first letter capitalized.
	"""
	lowered = text.lower()
	for index, character in enumerate(lowered):
		if character.isalpha():
			return lowered[:index] + character.upper() + lowered[index + 1:]
	return lowered


#============================================
def format_title_part(part: str) -> str:
	"""
	Format one hyphen-separated part of a title word.

	Args:
		part: Text between hyphens, possibly empty for a leading hyphen.

	Returns:
		The part with display capitalization applied.
	"""
	# Uppercase tokens are checked here, not only on the whole word, so the
	# numeral in "II-LECT" survives as "II-Lect".
	if part.upper() in ALWAYS_UPPERCASE_WORDS:
		return part.upper()
	formatted_part = capitalize_first_letter(part)
	return formatted_part


#============================================
def format_title_word(word: str, is_edge_word: bool) -> str:
	"""
	Format a single whitespace-delimited word of a course title.

	Args:
		word: One word from the title, already stripped of surrounding spaces.
		is_edge_word: True for the first and last word, which never lowercase.

	Returns:
		The word with display capitalization applied.
	"""
	# Anything containing a digit is left alone: course numbers ("101"),
	# dimension tokens ("3D"), and section codes should not be recased.
	if any(character.isdigit() for character in word):
		return word

	lower_word = word.lower()
	if not is_edge_word and lower_word in ALWAYS_LOWERCASE_WORDS:
		return lower_word

	# Capitalize each hyphen-separated part so "BIOLOGY-LECT" becomes
	# "Biology-Lect" rather than "Biology-lect".
	parts = word.split("-")
	formatted_parts = []
	for part in parts:
		formatted_parts.append(format_title_part(part))
	formatted_word = "-".join(formatted_parts)
	return formatted_word


#============================================
def smart_title_case(text: str) -> str:
	"""
	Convert an ALL CAPS Banner course title to readable title case.

	Whitespace normalization is the caller's job (see
	change_summary.format_change_value); this function splits on whitespace and
	joins with single spaces, so incidental runs of spaces do collapse.

	Args:
		text: Course title text, typically ALL CAPS from Banner.

	Returns:
		The title with display capitalization applied.
	"""
	words = text.split()
	if not words:
		return ""

	last_index = len(words) - 1
	formatted_words = []
	for index, word in enumerate(words):
		is_edge_word = index == 0 or index == last_index
		formatted_words.append(format_title_word(word, is_edge_word))
	formatted_title = " ".join(formatted_words)
	return formatted_title
