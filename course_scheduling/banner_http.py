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
import logging

# PIP3 modules
import requests

BASE_URL = "https://banner.roosevelt.edu/ssbprod/bwskzenr.P_CourseFinder"
RETRYABLE_STATUS_CODES = frozenset((408, 429, 500, 502, 503, 504))
RETRY_DELAYS = (5, 15)


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

def _fetch_subject_response(term: str, subject: str) -> requests.Response:
	"""
	Fetch one subject with a fresh HTTP session.

	Args:
		term: Term code, for example 202620.
		subject: Single subject code, for example "BIOL".

	Returns:
		Response from posting the Course Finder form.
	"""
	session = _build_session()
	get_search_page(session, term)
	payload = build_post_payload(term, [subject])
	response = post_results(session, term, payload)
	return response


#============================================

def _should_retry_exception(exc: requests.RequestException) -> bool:
	"""
	Return whether a requests exception represents a transient failure.

	Args:
		exc: Exception raised during the Course Finder GET or POST.

	Returns:
		True for connection failures, timeouts, and retryable HTTP statuses.
	"""
	if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
		return True
	if not isinstance(exc, requests.HTTPError):
		return False
	if exc.response is None:
		return False
	retryable = exc.response.status_code in RETRYABLE_STATUS_CODES
	return retryable


#============================================

def _wait_before_retry(subject: str, attempt_number: int, delay: int, reason: str) -> None:
	"""
	Log a transient failure and wait before opening a fresh session.

	Args:
		subject: Subject code being downloaded.
		attempt_number: Failed attempt number, starting at one.
		delay: Backoff delay in seconds.
		reason: Short failure description for the log.
	"""
	logging.warning(
		"Course server request for %s failed on attempt %d (%s); retrying in %d seconds",
		subject,
		attempt_number,
		reason,
		delay,
	)
	time.sleep(delay)


#============================================

def download_subject(term: str, subject: str, output_file: str) -> None:
	"""
	Download the Course Finder results page for one subject and term.

	Fetches the search page (to establish the session), posts the FIND COURSES
	form for the single subject, and writes the results HTML to output_file.
	Transient network and server failures are retried with a fresh session and
	bounded backoff. On a final server error response, writes the error body to
	error_500.html and raises.

	Args:
		term: Term code, for example 202620.
		subject: Single subject code to fetch, for example "BIOL".
		output_file: Output HTML file for the results page.

	Raises:
		RuntimeError: If the server responds with status code 400 or higher.
		requests.RequestException: If a network failure remains after retries.
	"""
	for attempt_index in range(len(RETRY_DELAYS) + 1):
		try:
			response = _fetch_subject_response(term, subject)
		except requests.RequestException as exc:
			if attempt_index >= len(RETRY_DELAYS) or not _should_retry_exception(exc):
				logging.error(
					"Course server request for %s failed: %s",
					subject,
					exc,
				)
				raise
			delay = RETRY_DELAYS[attempt_index]
			_wait_before_retry(subject, attempt_index + 1, delay, exc.__class__.__name__)
			continue

		if response.status_code in RETRYABLE_STATUS_CODES and attempt_index < len(RETRY_DELAYS):
			delay = RETRY_DELAYS[attempt_index]
			reason = f"HTTP {response.status_code}"
			_wait_before_retry(subject, attempt_index + 1, delay, reason)
			continue

		if response.status_code >= 400:
			error_path = os.path.join(os.getcwd(), "error_500.html")
			write_error_html(error_path, response.text)
			logging.error(
				"Course server request for %s failed with HTTP %d; saved response to %s",
				subject,
				response.status_code,
				error_path,
			)
			error_message = f"Course server request for {subject} responded with "
			error_message += f"{response.status_code}. Saved {error_path}"
			raise RuntimeError(error_message)

		with open(output_file, "w", encoding="utf-8") as handle:
			handle.write(response.text)

		print(f"Wrote results HTML to {output_file}")
		return
