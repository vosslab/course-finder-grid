"""
Banner Course Finder HTTP discovery and fetch.

Owns the live network side of the Course Finder workflow: opening a session,
fetching the search page, parsing the subject-option list off that page, posting
the FIND COURSES form for a single subject, and writing the returned results
HTML to disk. Saved-page parsing lives in course_scheduling.banner_parser.
"""

# Standard Library
import os
import time
import random

# PIP3 modules
import requests

BASE_URL = "https://banner.roosevelt.edu/ssbprod/bwskzenr.P_CourseFinder"


#============================================

def get_search_page(session: requests.Session, term: str) -> str:
	"""
	Fetch the Course Finder search page for a term.

	Args:
		session: Requests session (keeps cookies).
		term: Term code, for example 202620.

	Returns:
		HTML text for the search page.
	"""
	time.sleep(random.random())
	resp = session.get(BASE_URL, params={"TERM": term}, timeout=30)
	resp.raise_for_status()
	return resp.text


#============================================

def build_post_payload(term: str, subjects: list) -> list:
	"""
	Build a POST payload that mimics clicking FIND COURSES.

	Args:
		term: Term code.
		subjects: List of subject codes (for example ["BIOL", "CHEM"]).

	Returns:
		List of (key, value) tuples suitable for requests.post(data=...),
		including repeated keys for multi-select fields.
	"""
	payload: list = [
		("TERM", term),
		("GGLESTYLSRCH", ""),
	]

	# Subjects is a MULTIPLE select. If none provided, keep All Subjects ("%").
	if subjects:
		for subj in subjects:
			payload.append(("SUBJ", subj))
	else:
		payload.append(("SUBJ", "%"))

	payload.extend([
		("ATTR", "%"),
		("OTERM", "000000"),
		("CAMP", "%"),
		("COURSE", ""),
		("LEVL", "%"),
		("COLL", "%"),
		("INST", "%"),
		("begin_hh", "00"),
		("begin_mi", "0"),
		("end_hh", "00"),
		("end_mi", "0"),
		("PTRM", "%"),
		("DAYS", "NODAY"),
		("FORM_ACTION", "RESULTS"),
	])

	return payload


#============================================

def post_results(session: requests.Session, term: str, payload: list) -> requests.Response:
	"""
	POST the search form and return the results HTML.

	Args:
		session: Requests session (keeps cookies).
		term: Term code.
		payload: POST payload from build_post_payload().

	Returns:
		Response object for the results page.
	"""
	time.sleep(random.random())
	headers = {
		"Origin": "https://banner.roosevelt.edu",
		"Referer": f"{BASE_URL}?TERM={term}",
		"Content-Type": "application/x-www-form-urlencoded",
	}
	resp = session.post(BASE_URL, data=payload, headers=headers, timeout=30)
	return resp


#============================================

def write_error_html(output_path: str, html_text: str) -> None:
	with open(output_path, "w", encoding="utf-8") as handle:
		handle.write(html_text)


#============================================

def _build_session() -> requests.Session:
	"""
	Open a requests session with the Course Finder user agent.

	Returns:
		Configured requests session.
	"""
	session = requests.Session()
	session.headers.update({
		"User-Agent": "Mozilla/5.0 (compatible; course-downloader/1.0; +https://www.roosevelt.edu)"
	})
	return session


#============================================

def download_subject(term: str, subject: str, output_file: str) -> None:
	"""
	Download the Course Finder results page for one subject and term.

	Fetches the search page (to establish the session), posts the FIND COURSES
	form for the single subject, and writes the results HTML to output_file. On
	a server error response, writes the error body to error_500.html and raises.

	Args:
		term: Term code, for example 202620.
		subject: Single subject code to fetch, for example "BIOL".
		output_file: Output HTML file for the results page.

	Raises:
		RuntimeError: If the server responds with status code 400 or higher.
	"""
	session = _build_session()
	# Fetch the search page first so the session carries the needed cookies.
	get_search_page(session, term)

	payload = build_post_payload(term, [subject])
	response = post_results(session, term, payload)
	if response.status_code >= 400:
		error_path = os.path.join(os.getcwd(), "error_500.html")
		write_error_html(error_path, response.text)
		raise RuntimeError(
			f"Server responded with {response.status_code}. Saved {error_path}"
		)

	with open(output_file, "w", encoding="utf-8") as handle:
		handle.write(response.text)

	print(f"Wrote results HTML to {output_file}")
