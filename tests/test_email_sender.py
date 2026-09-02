"""Tests for the daemon startup Mail.app test message."""

# local repo modules
import course_scheduling.email_sender


#============================================
def test_startup_test_email_targets_only_daemon_operator() -> None:
	"""The startup check emails only Neil and never the normal recipient list."""
	script_text = course_scheduling.email_sender.compose_startup_test_applescript()

	assert 'address:"nvoss@roosevelt.edu"' in script_text
	assert "rseiser@roosevelt.edu" not in script_text
