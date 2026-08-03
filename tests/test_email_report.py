"""Tests for user-visible course report email composition."""

# Standard Library
import datetime

# local repo modules
import course_scheduling.email_report


#============================================

def test_server_error_is_disclosed_in_partial_report() -> None:
	"""The email clearly identifies BCHM as unavailable after a server error."""
	body = course_scheduling.email_report.build_email_body(
		datetime.date(2026, 7, 29),
		datetime.date(2026, 7, 28),
		["BIOL"],
		4,
		"BIOL 101: section now full\n",
		["BCHM"],
	)
	assert "BCHM data not available due to server error." in body
