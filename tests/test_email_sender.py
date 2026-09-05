"""Tests for the CourseFinderMailer request boundary."""

# Standard Library
import pathlib

# PIP3 modules
import pytest

# local repo modules
import course_scheduling.email_sender


#============================================
def test_mail_request_rejects_recipient_outside_allowlist() -> None:
	"""The helper request boundary cannot target an arbitrary address."""
	with pytest.raises(ValueError, match="unapproved recipient"):
		course_scheduling.email_sender.build_mail_request(
			("attacker@example.com",),
			"subject",
			"body",
			None,
		)


#============================================
def test_mail_result_accepts_success_without_optional_error(
	tmp_path: pathlib.Path,
) -> None:
	"""A successful send does not require optional error detail."""
	result_path = tmp_path / "request.json.result.json"
	result_path.write_text('{"status":"sent"}', encoding="utf-8")

	course_scheduling.email_sender._read_mail_result(result_path)
