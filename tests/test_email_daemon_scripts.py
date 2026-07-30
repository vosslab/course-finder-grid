"""
Behavior tests for the detached email-daemon launcher and supervisor.

The command mocks keep these tests offline while executing the real shell
scripts and verifying their process-boundary behavior.
"""

# Standard Library
import os
import shutil
import subprocess

# PIP3 modules
import pytest

REPO_ROOT = subprocess.run(
	["git", "rev-parse", "--show-toplevel"],
	check=True,
	capture_output=True,
	text=True,
).stdout.strip()


#============================================
# helpers

def write_executable(path: str, body: str) -> None:
	"""
	Write an executable shell-command mock.

	Args:
		path: Destination path.
		body: Complete shell script text.
	"""
	with open(path, "w", encoding="utf-8") as handle:
		handle.write(body)
	os.chmod(path, 0o755)


def mock_environment(tmp_path: str) -> tuple:
	"""
	Create an environment whose command path starts with a temporary mock bin.

	Args:
		tmp_path: Pytest temporary directory.

	Returns:
		Environment mapping and mock-bin path.
	"""
	bin_dir = os.path.join(tmp_path, "bin")
	os.makedirs(bin_dir)
	env = os.environ.copy()
	env["PATH"] = f"{bin_dir}:{env['PATH']}"
	return env, bin_dir


#============================================
# detached launcher

def test_launcher_does_not_run_python_in_foreground(tmp_path: str) -> None:
	"""The launcher creates a detached tmux session without invoking Python."""
	env, bin_dir = mock_environment(tmp_path)
	test_root = os.path.join(tmp_path, "repo")
	os.makedirs(test_root)
	launcher_path = os.path.join(test_root, "run_email_tmux.sh")
	shutil.copyfile(os.path.join(REPO_ROOT, "run_email_tmux.sh"), launcher_path)
	os.chmod(launcher_path, 0o755)

	python_marker = os.path.join(tmp_path, "python_called")
	tmux_state = os.path.join(tmp_path, "tmux_state")
	tmux_command = os.path.join(tmp_path, "tmux_command")
	env["DAEMON_TEST_REPO_ROOT"] = test_root
	env["DAEMON_TEST_PYTHON_MARKER"] = python_marker
	env["DAEMON_TEST_TMUX_STATE"] = tmux_state
	env["DAEMON_TEST_TMUX_COMMAND"] = tmux_command

	write_executable(
		os.path.join(bin_dir, "git"),
		"#!/bin/bash\n"
		"echo \"$DAEMON_TEST_REPO_ROOT\"\n",
	)
	write_executable(
		os.path.join(bin_dir, "python3"),
		"#!/bin/bash\n"
		"touch \"$DAEMON_TEST_PYTHON_MARKER\"\n"
		"exit 99\n",
	)
	write_executable(
		os.path.join(bin_dir, "sleep"),
		"#!/bin/bash\n"
		"exit 0\n",
	)
	write_executable(
		os.path.join(bin_dir, "tmux"),
		"#!/bin/bash\n"
		"if [ \"$1\" = \"has-session\" ]; then\n"
		"\t[ -f \"$DAEMON_TEST_TMUX_STATE\" ]\n"
		"\texit\n"
		"fi\n"
		"if [ \"$1\" = \"new-session\" ]; then\n"
		"\ttouch \"$DAEMON_TEST_TMUX_STATE\"\n"
		"\tprintf '%s\\n' \"$*\" > \"$DAEMON_TEST_TMUX_COMMAND\"\n"
		"\texit 0\n"
		"fi\n"
		"exit 98\n",
	)

	result = subprocess.run(
		[launcher_path],
		check=False,
		capture_output=True,
		text=True,
		env=env,
	)

	assert result.returncode == 0
	assert not os.path.exists(python_marker)
	with open(tmux_command, encoding="utf-8") as handle:
		command_text = handle.read()
	assert "new-session -d -s course_email" in command_text
	assert "exec ./tools/run_email_scheduler.sh" in command_text


#============================================
# failure containment

def test_supervisor_survives_refresh_and_scheduler_failures(
		tmp_path: str) -> None:
	"""Refresh and loop failures are logged, and the scheduler is restarted."""
	env, bin_dir = mock_environment(tmp_path)
	events_file = os.path.join(tmp_path, "events")
	loop_state = os.path.join(tmp_path, "loop_state")
	env["DAEMON_TEST_EVENTS"] = events_file
	env["DAEMON_TEST_LOOP_STATE"] = loop_state

	write_executable(
		os.path.join(bin_dir, "python3"),
		"#!/bin/bash\n"
		"if [[ \" $* \" == *\" --refresh-baseline \"* ]]; then\n"
		"\techo baseline-refresh >> \"$DAEMON_TEST_EVENTS\"\n"
		"\texit 23\n"
		"fi\n"
		"if [ \"$1\" = \"-m\" ]; then\n"
		"\techo \"log:$3\" >> \"$DAEMON_TEST_EVENTS\"\n"
		"\texit 0\n"
		"fi\n"
		"if [ ! -f \"$DAEMON_TEST_LOOP_STATE\" ]; then\n"
		"\ttouch \"$DAEMON_TEST_LOOP_STATE\"\n"
		"\techo loop-42 >> \"$DAEMON_TEST_EVENTS\"\n"
		"\texit 42\n"
		"fi\n"
		"echo loop-143 >> \"$DAEMON_TEST_EVENTS\"\n"
		"exit 143\n",
	)
	write_executable(
		os.path.join(bin_dir, "sleep"),
		"#!/bin/bash\n"
		"echo \"sleep-$1\" >> \"$DAEMON_TEST_EVENTS\"\n",
	)

	result = subprocess.run(
		["bash", "tools/run_email_scheduler.sh", "202710"],
		check=False,
		capture_output=True,
		text=True,
		cwd=REPO_ROOT,
		env=env,
	)

	assert result.returncode == 143
	with open(events_file, encoding="utf-8") as handle:
		events = handle.read()
	assert "baseline-refresh" in events
	assert "log:Baseline refresh exited with status 23" in events
	assert "loop-42" in events
	assert "log:Email scheduler exited with status 42" in events
	assert "sleep-60" in events
	assert "loop-143" in events
