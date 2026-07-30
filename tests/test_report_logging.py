"""
Tests for persistent email-report failure logging.

These tests write only under tmp_path and exercise traceback persistence and
size-based rotation without running the daemon or any network code.
"""

# Standard Library
import os
import logging

# PIP3 modules
import pytest

# local repo modules
import course_scheduling.report_logging


#============================================
# helpers

def owned_handlers() -> list:
	"""
	Return report handlers currently attached to the root logger.

	Returns:
		List of handlers owned by report_logging.
	"""
	handler_names = {
		course_scheduling.report_logging.FILE_HANDLER_NAME,
		course_scheduling.report_logging.STREAM_HANDLER_NAME,
	}
	logger = logging.getLogger()
	handlers = [
		handler for handler in logger.handlers
		if handler.get_name() in handler_names
	]
	return handlers


def close_owned_handlers() -> None:
	"""Remove and close report handlers so tests do not leak global logging state."""
	logger = logging.getLogger()
	for handler in owned_handlers():
		logger.removeHandler(handler)
		handler.close()


def flush_owned_handlers() -> None:
	"""Flush report handlers before reading their temporary files."""
	for handler in owned_handlers():
		handler.flush()


def configure_temp_log(monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> str:
	"""
	Point report logging at a temporary file and configure it.

	Args:
		monkeypatch: Pytest monkeypatch helper.
		tmp_path: Temporary test directory.

	Returns:
		Path to the temporary report log.
	"""
	close_owned_handlers()
	log_dir = os.path.join(tmp_path, "logs")
	log_file = os.path.join(log_dir, "email_schedule_report.log")
	monkeypatch.setattr(course_scheduling.report_logging, "LOG_DIR", log_dir)
	monkeypatch.setattr(course_scheduling.report_logging, "LOG_FILE", log_file)
	course_scheduling.report_logging.setup_logging()
	return log_file


#============================================
# persistent failures and rotation

def test_process_failure_persists_context_and_traceback(
		monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
	"""An active exception is written with process context and its traceback."""
	log_file = configure_temp_log(monkeypatch, tmp_path)

	try:
		raise ValueError("simulated report failure")
	except ValueError:
		course_scheduling.report_logging.log_process_failure(
			"prime", "202710", ["BIOL", "BCHM"]
		)

	flush_owned_handlers()
	with open(log_file, encoding="utf-8") as handle:
		log_text = handle.read()
	close_owned_handlers()

	assert "mode=prime term=202710 subjects=BIOL,BCHM" in log_text
	assert "ValueError: simulated report failure" in log_text


def test_report_log_rotates_by_size(
		monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
	"""Oversized report logs rotate to a numbered backup."""
	monkeypatch.setattr(course_scheduling.report_logging, "LOG_MAX_BYTES", 200)
	log_file = configure_temp_log(monkeypatch, tmp_path)

	logging.error("first oversized record %s", "x" * 300)
	logging.error("second oversized record %s", "y" * 300)
	flush_owned_handlers()
	backup_file = f"{log_file}.1"
	close_owned_handlers()

	assert os.path.isfile(backup_file)


def test_supervisor_event_uses_shared_rotating_log(
		monkeypatch: pytest.MonkeyPatch, tmp_path: str) -> None:
	"""A shell-supervisor restart notice is persisted by the shared logger."""
	log_file = configure_temp_log(monkeypatch, tmp_path)

	course_scheduling.report_logging.log_supervisor_event(
		"Email scheduler exited with status 42; restarting in 60 seconds"
	)
	flush_owned_handlers()
	with open(log_file, encoding="utf-8") as handle:
		log_text = handle.read()
	close_owned_handlers()

	assert "WARNING Email scheduler exited with status 42" in log_text
