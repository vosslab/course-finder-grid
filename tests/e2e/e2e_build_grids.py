"""End-to-end test for the primary build_grids_from_html.py workflow.

This is a LIVE NETWORK e2e test that downloads course data from Banner.
It must NOT be collected by pytest (tests/conftest.py excludes tests/e2e/).

How to run:
	source source_me.sh && python3 tests/e2e/e2e_build_grids.py [TERM]

TERM defaults to "202710". Pass a different term code as the first argument
when 202710 ages out, for example:
	source source_me.sh && python3 tests/e2e/e2e_build_grids.py 202810
"""

# Standard Library
import os
import sys
import subprocess

# PIP3 modules
import openpyxl


#============================================
def get_repo_root() -> str:
	"""Resolve the repository root via git rev-parse.

	Returns:
		str: Absolute path to the repository root.
	"""
	output = subprocess.check_output(
		["git", "rev-parse", "--show-toplevel"],
		text=True,
	)
	repo_root = output.strip()
	return repo_root


#============================================
def run_build_command(repo_root: str, term_code: str) -> tuple[int, str]:
	"""Run build_grids_from_html.py and capture stdout.

	Args:
		repo_root: Absolute path to the repository root.
		term_code: Banner term code to pass via -t flag.

	Returns:
		tuple[int, str]: (return_code, stdout_text) from the subprocess.
	"""
	command = [sys.executable, "./build_grids_from_html.py", "-t", term_code]
	result = subprocess.run(
		command,
		capture_output=True,
		text=True,
		cwd=repo_root,
	)
	return result.returncode, result.stdout


#============================================
def extract_final_path(stdout_text: str) -> str:
	"""Extract the final non-empty line from stdout.

	Args:
		stdout_text: Full stdout captured from the build command.

	Returns:
		str: The last non-empty line stripped of whitespace.
	"""
	lines = [line.strip() for line in stdout_text.splitlines() if line.strip()]
	assert lines, "stdout was empty; expected at least one output line"
	final_line = lines[-1]
	return final_line


#============================================
def assert_workbook_tabs(xlsx_path: str, term_code: str) -> None:
	"""Load the merged workbook and assert tab set is exactly the 9 expected tabs.

	Tabs must include all 9 grid stems (built from term_code) and must
	not include any "common_hour" or "timeblock" tab (those are standalone files).

	Args:
		xlsx_path: Absolute path to the merged xlsx workbook.
		term_code: Banner term code used to build expected tab names.
	"""
	# Build the exact expected tab names from the term_code.
	expected_tabs = {
		f"lower_undergrad_{term_code}-grid",
		f"undergrad_level_{term_code}-grid",
		f"300_level_undergrad_{term_code}-grid",
		f"graduate_level_{term_code}-grid",
		f"schaumburg_{term_code}-grid",
		f"lab_chicago_{term_code}-grid",
		f"lab_schaumburg_{term_code}-grid",
		f"raw_table_{term_code}-grid",
		f"all_courses_in_dept_{term_code}-grid",
	}
	wb = openpyxl.load_workbook(xlsx_path)
	actual_tabs = set(wb.sheetnames)
	# Exactly 9 tabs required.
	assert len(actual_tabs) == 9, (
		f"Expected 9 tabs, got {len(actual_tabs)}: {sorted(actual_tabs)}"
	)
	# Tab names must match the expected set exactly.
	assert actual_tabs == expected_tabs, (
		f"Tab mismatch.\n  Expected: {sorted(expected_tabs)}\n  Got:      {sorted(actual_tabs)}"
	)
	# No merged "common_hour" or "timeblock" tabs should be present.
	for tab in actual_tabs:
		assert "common_hour" not in tab, (
			f"Tab '{tab}' contains 'common_hour'; it must be a standalone file, not a merged tab."
		)
		assert "timeblock" not in tab, (
			f"Tab '{tab}' contains 'timeblock'; it must be a standalone file, not a merged tab."
		)


#============================================
def assert_standalone_analysis_files(output_dir: str, term_code: str) -> None:
	"""Assert the two standalone analysis xlsx files exist in the output dir.

	Args:
		output_dir: Absolute path to the output/ directory.
		term_code: Banner term code used to build expected filenames.
	"""
	common_hour_path = os.path.join(output_dir, f"all_courses_in_dept_{term_code}-common_hour.xlsx")
	timeblock_path = os.path.join(output_dir, f"all_courses_in_dept_{term_code}-timeblock.xlsx")
	assert os.path.isfile(common_hour_path), (
		f"Missing standalone analysis file: {common_hour_path}"
	)
	assert os.path.isfile(timeblock_path), (
		f"Missing standalone analysis file: {timeblock_path}"
	)


#============================================
def main() -> None:
	"""Run the full e2e check for build_grids_from_html.py."""
	# Allow overriding the term code from the command line so this test
	# does not rot when 202710 ages out of Banner.
	term_code = sys.argv[1] if len(sys.argv) > 1 else "202710"
	repo_root = get_repo_root()
	output_dir = os.path.join(repo_root, "output")

	print(f"e2e_build_grids: term={term_code} repo={repo_root}")

	# Step 1: Run the real build command against live Banner data.
	return_code, stdout_text = run_build_command(repo_root, term_code)

	# Step 2: Assert exit code 0.
	assert return_code == 0, (
		f"build_grids_from_html.py exited {return_code}; expected 0.\nStdout:\n{stdout_text}"
	)

	# Step 3: The final non-empty stdout line must end with .xlsx and exist on disk.
	xlsx_path = extract_final_path(stdout_text)
	assert xlsx_path.endswith(".xlsx"), (
		f"Final stdout line does not end with .xlsx: {xlsx_path!r}"
	)
	assert os.path.isfile(xlsx_path), (
		f"Final stdout line is a path that does not exist on disk: {xlsx_path}"
	)

	# Step 4: Load the merged workbook and assert exactly 9 correct tabs.
	assert_workbook_tabs(xlsx_path, term_code)

	# Step 5: Assert the two standalone analysis files exist in output/.
	assert_standalone_analysis_files(output_dir, term_code)

	print(f"PASS: e2e_build_grids term={term_code} all checks passed")


if __name__ == '__main__':
	main()
