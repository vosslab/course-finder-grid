"""Term code to human-readable label conversion for Banner term codes."""


#============================================

def term_code_to_label(term_code: str) -> str:
	"""
	Convert a Banner term code to a human-readable label.

	Args:
		term_code: Six-digit term code like 202710.

	Returns:
		Label like Fall_2026, Spring_2027, or the raw code if unrecognized.
	"""
	if len(term_code) != 6:
		return term_code
	year = term_code[:4]
	suffix = term_code[4:]
	# suffix 10 = Fall (belongs to previous calendar year), 20 = Spring, 30 = Summer
	suffix_map = {
		"10": f"Fall_{int(year) - 1}",
		"20": f"Spring_{year}",
		"30": f"Summer_{year}",
	}
	label = suffix_map.get(suffix, term_code)
	return label
