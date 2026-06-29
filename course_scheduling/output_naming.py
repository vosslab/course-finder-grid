"""
Output filename construction from active filter selections.

Builds a descriptive xlsx filename that encodes the selected campus, level,
course-number series, and subject filters.
"""


#============================================

def generate_output_filename(subjects: list[str] | None, levels: list[str] | None, numbers: list[int] | None, campus: list[str] | None) -> str:
	"""
	Generate a dynamic output filename from the active filter selections.

	Args:
		subjects: Selected subject codes (e.g. ["BIOL", "CHEM"]) or None.
		levels: Selected levels ("U", "G") or None.
		numbers: Selected course-number series (100, 200, 300, 400) or None.
		campus: Selected campus names (e.g. ["CHICAGO CAMPUS"]) or None.

	Returns:
		str: Generated output filename.
	"""
	parts = ["class_schedule"]

	# Add campus filters
	if campus:
		parts.append("_".join([c.replace(" CAMPUS", "").lower() for c in campus]))

	# Add level filters (U for undergraduate, G for graduate)
	if levels:
		parts.append("".join(levels))  # e.g., "U", "G", "UG"

	# Add course number series (e.g., 100, 200)
	if numbers:
		parts.append("_".join(map(str, numbers)))  # e.g., "100200"

	# Add subject filters (e.g., BIOL, CHEM)
	if subjects:
		parts.append("_".join(subjects))  # e.g., "BIOLCHEM"

	# Merge parts and add file extension
	filename = "_".join(parts) + ".xlsx"
	return filename
