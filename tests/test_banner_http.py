"""
Tests for transient Course Finder HTTP recovery.

The cases replace the live fetch seam, so they stay offline and deterministic
while driving download_subject's retry and permanent-error behavior.
"""

# Standard Library
import os

# PIP3 modules
import pytest
import requests

# local repo modules
import course_scheduling.banner_http


#============================================
# helpers

def make_response(status_code: int, text: str) -> requests.Response:
	"""
	Build a requests response with a status and loaded text body.

	Args:
		status_code: HTTP status code.
		text: Response body.

	Returns:
		A response suitable for the download retry seam.
	"""
	response = requests.Response()
	response.status_code = status_code
	response._content = text.encode("utf-8")
	response.encoding = "utf-8"
	return response


#============================================
# retry behavior

def test_transient_server_error_recovers(monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
	"""A transient server error retries and writes the successful response."""
	responses = iter([
		make_response(500, "temporary failure"),
		make_response(200, "course results"),
	])

	def fake_fetch(term: str, subject: str) -> requests.Response:
		"""Return the next deterministic Course Finder response."""
		response = next(responses)
		return response

	def skip_wait(subject: str, attempt_number: int, delay: int, reason: str) -> None:
		"""Keep the retry test fast without changing retry control flow."""
		return

	monkeypatch.setattr(course_scheduling.banner_http, "_fetch_subject_response", fake_fetch)
	monkeypatch.setattr(course_scheduling.banner_http, "_wait_before_retry", skip_wait)
	output_file = os.path.join(tmp_path, "results.html")

	course_scheduling.banner_http.download_subject("202710", "BCHM", output_file)

	with open(output_file, encoding="utf-8") as handle:
		output_text = handle.read()
	assert output_text == "course results"


def test_permanent_client_error_does_not_retry(
		monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
	"""A permanent client error fails immediately instead of retrying."""
	responses = iter([make_response(400, "bad request")])

	def fake_fetch(term: str, subject: str) -> requests.Response:
		"""Return one response; any unintended retry raises StopIteration."""
		response = next(responses)
		return response

	monkeypatch.setattr(course_scheduling.banner_http, "_fetch_subject_response", fake_fetch)
	monkeypatch.setattr(course_scheduling.banner_http.os, "getcwd", lambda: str(tmp_path))
	output_file = os.path.join(tmp_path, "results.html")

	with pytest.raises(RuntimeError, match="BCHM responded with 400"):
		course_scheduling.banner_http.download_subject("202710", "BCHM", output_file)
