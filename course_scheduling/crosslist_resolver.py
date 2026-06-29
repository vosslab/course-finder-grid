"""
Union-find cross-list merging for parsed course dicts.

Discovers transitive cross-list groups, validates that each group is fully
connected, and merges same-subject cross-listed sections into single entries
with slash-delimited labels.
"""

# Standard Library
import collections

# local repo modules
import course_scheduling.course_label


#============================================

def uf_find(parent: dict, x: str) -> str:
	"""Find root of x with path compression."""
	while parent[x] != x:
		parent[x] = parent[parent[x]]
		x = parent[x]
	return x


#============================================

def uf_union(parent: dict, a: str, b: str) -> None:
	"""Union two elements in the union-find structure."""
	ra = uf_find(parent, a)
	rb = uf_find(parent, b)
	if ra != rb:
		parent[ra] = rb


#============================================

def build_merged_label(subject: str, course_numbers: list, sections: list) -> str:
	"""
	Build a slash-delimited merged label from course numbers and sections.

	Args:
		subject: The course subject code (e.g. "BIOL").
		course_numbers: Sorted list of unique course numbers.
		sections: Sorted list of unique section strings.

	Returns:
		Merged label string like "BIOL 318/418-01/20".
	"""
	numbers_part = "/".join(str(n) for n in course_numbers)
	sections_part = "/".join(sections)
	merged_label = f"{subject} {numbers_part}-{sections_part}"
	return merged_label


#============================================

def validate_crosslist_symmetry(courses: list, course_by_label: dict) -> list:
	"""
	Check that every cross-list group is fully connected.

	Each course in a cross-list group should reference every other member.
	Uses union-find to discover transitive groups, then verifies every
	member declares every other member as a peer.

	Args:
		courses: List of all intermediate course dicts.
		course_by_label: Dict mapping label to course dict.

	Returns:
		List of warning message strings for any incomplete links found.
	"""
	# Build peer map: label -> set of declared peers present in our data
	peer_map = {}
	for course in courses:
		label = course["label"]
		declared_peers = set()
		for cl_label in course["crosslist_labels"]:
			_, _, _, normalized = course_scheduling.course_label.normalize_course_label(cl_label)
			if normalized is None:
				continue
			if normalized in course_by_label:
				declared_peers.add(normalized)
		peer_map[label] = declared_peers

	# Union-find to discover transitive cross-list groups
	parent = {}
	for label in peer_map:
		parent[label] = label
	for label, peers in peer_map.items():
		for peer_label in peers:
			uf_union(parent, label, peer_label)

	# Collect groups by root
	groups = collections.defaultdict(set)
	for label in parent:
		root = uf_find(parent, label)
		groups[root].add(label)

	# Check completeness: every member must declare every other member
	warnings = []
	for group_members in groups.values():
		# Skip singleton groups (no cross-listing)
		if len(group_members) < 2:
			continue
		for label in sorted(group_members):
			for other in sorted(group_members):
				if other == label:
					continue
				if other not in peer_map[label]:
					# Find an intermediary that links both courses
					shared = peer_map[label] & peer_map[other]
					if shared:
						via = sorted(shared)[0]
						msg = f"cross-list incomplete: {label} does not list {other} (linked via {via})"
					else:
						msg = f"cross-list incomplete: {label} does not list {other}"
					warnings.append(msg)
	return warnings


#============================================

def merge_cross_listed_courses(courses: list) -> list:
	"""
	Merge cross-listed courses into single entries using union-find.

	Args:
		courses: List of intermediate course dicts with crosslist_labels.

	Returns:
		List of merged intermediate course dicts.
	"""
	# Build a label-to-course lookup for courses we actually have
	course_by_label = {}
	for course in courses:
		course_by_label[course["label"]] = course

	# Validate cross-list symmetry and log any warnings
	crosslist_warnings = validate_crosslist_symmetry(courses, course_by_label)
	for warning in crosslist_warnings:
		print(f"WARNING: {warning}")

	# Initialize union-find with all course labels
	parent = {}
	for course in courses:
		label = course["label"]
		if label not in parent:
			parent[label] = label
		# Add crosslist labels that exist in our data
		for cl_label in course["crosslist_labels"]:
			# Normalize the cross-list label
			_, _, _, normalized = course_scheduling.course_label.normalize_course_label(cl_label)
			if normalized and normalized in course_by_label:
				if normalized not in parent:
					parent[normalized] = normalized
				uf_union(parent, label, normalized)

	# Group courses by their root
	groups = collections.defaultdict(list)
	for course in courses:
		root = uf_find(parent, course["label"])
		groups[root].append(course)

	# Merge each group into one entry
	merged_courses = []
	for group in groups.values():
		if len(group) == 1:
			# No merging needed
			merged_courses.append(group[0])
			continue

		# Collect unique subjects
		subjects = sorted(set(c["subject"] for c in group))
		if len(subjects) > 1:
			# Cross-subject listing: do not merge, keep separate
			merged_courses.extend(group)
			continue

		subject = subjects[0]
		# Collect unique course numbers and sections
		course_numbers = sorted(set(c["course_number"] for c in group))
		sections = sorted(set(c["section"] for c in group))

		merged_label = build_merged_label(subject, course_numbers, sections)

		# Use first course's meetings as representative
		representative = group[0]
		merged_course = {
			"label": merged_label,
			"subject": subject,
			"course_number": course_numbers[0],
			"section": sections[0],
			"meetings": representative["meetings"],
			"waitlisted": any(c["waitlisted"] for c in group),
			"enrollment_ratio": max(
				(c["enrollment_ratio"] for c in group if c["enrollment_ratio"] is not None),
				default=None,
			),
			"crosslist_labels": [],
		}
		merged_courses.append(merged_course)

	return merged_courses
