"""
Shared logging configuration for the email report processes.

This module uses only the Python standard library so the long-lived scheduler
can configure persistent logging without importing AppleScript or PyObjC.
"""

# Standard Library
import os
import sys
import logging
import logging.handlers

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PACKAGE_DIR)
LOG_DIR = os.path.join(REPO_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "email_schedule_report.log")
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3
FILE_HANDLER_NAME = "course_schedule_file"
STREAM_HANDLER_NAME = "course_schedule_stream"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"


#============================================

def _has_handler(logger: logging.Logger, handler_name: str) -> bool:
	"""
	Return whether the logger already owns a named report handler.

	Args:
		logger: Logger whose handlers should be inspected.
		handler_name: Stable handler name.

	Returns:
		True when a matching handler is already configured.
	"""
	for handler in logger.handlers:
		if handler.get_name() == handler_name:
			return True
	return False


#============================================

def setup_logging() -> None:
	"""
	Configure persistent rotating-file and terminal logging once per process.
	"""
	os.makedirs(LOG_DIR, exist_ok=True)
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	formatter = logging.Formatter(LOG_FORMAT)

	if not _has_handler(logger, FILE_HANDLER_NAME):
		file_handler = logging.handlers.RotatingFileHandler(
			LOG_FILE,
			mode="a",
			maxBytes=LOG_MAX_BYTES,
			backupCount=LOG_BACKUP_COUNT,
			encoding="utf-8",
		)
		file_handler.set_name(FILE_HANDLER_NAME)
		file_handler.setFormatter(formatter)
		logger.addHandler(file_handler)

	if not _has_handler(logger, STREAM_HANDLER_NAME):
		stream_handler = logging.StreamHandler()
		stream_handler.set_name(STREAM_HANDLER_NAME)
		stream_handler.setFormatter(formatter)
		logger.addHandler(stream_handler)


#============================================

def log_process_failure(mode: str, term_code: str, subjects: list) -> None:
	"""
	Log the active exception with report-process context and traceback.

	Args:
		mode: Process mode such as baseline-refresh, loop, dry-run, or send.
		term_code: Banner term code.
		subjects: Subject codes handled by the process.
	"""
	logging.exception(
		"Course schedule process failed: mode=%s term=%s subjects=%s",
		mode,
		term_code,
		",".join(subjects),
	)


#============================================

def log_supervisor_event(message: str) -> None:
	"""
	Write one shell-supervisor event through the shared rotating handlers.

	Args:
		message: Supervisor event text without a timestamp or severity prefix.
	"""
	setup_logging()
	logging.warning("%s", message)


#============================================

def main() -> None:
	"""
	Write the supervisor event supplied by the module command line.
	"""
	if len(sys.argv) != 2:
		raise RuntimeError(
			"Usage: python3 -m course_scheduling.report_logging MESSAGE"
		)
	log_supervisor_event(sys.argv[1])


if __name__ == '__main__':
	main()
