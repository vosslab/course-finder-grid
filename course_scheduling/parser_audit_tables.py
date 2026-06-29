"""
Parser audit table writers for the HTML schedule grid.

Provides csv/xlsx writers for the raw parsed table and the lab-filter debug
rows. These outputs support debugging and auditing of the parse-and-filter
stage.
"""

# Standard Library
import csv

# PIP3 modules
import openpyxl


#============================================

def ordered_columns(rows: list) -> list:
	"""
	Collect the union of row keys in first-seen order.

	Mirrors the column ordering that a DataFrame built from a list of dicts
	would produce, so audit output column order stays stable.

	Args:
		rows: List of dict rows.

	Returns:
		List of column names in first-seen order.
	"""
	columns = []
	seen = set()
	for row in rows:
		for key in row.keys():
			if key not in seen:
				seen.add(key)
				columns.append(key)
	return columns


#============================================

def write_rows_to_csv(rows: list, columns: list, output_path: str) -> None:
	"""
	Write dict rows to a CSV file with the given column order (no index column).
	"""
	with open(output_path, "w", newline="") as csv_file:
		writer = csv.writer(csv_file)
		writer.writerow(columns)
		for row in rows:
			# Missing cells become empty strings, matching prior DataFrame output
			writer.writerow([row.get(column, "") for column in columns])


#============================================

def write_rows_to_xlsx(rows: list, columns: list, output_path: str, sheet_name: str) -> None:
	"""
	Write dict rows to an xlsx sheet with the given column order (no index column).
	"""
	workbook = openpyxl.Workbook()
	worksheet = workbook.active
	worksheet.title = sheet_name
	# Header row holds the column names
	worksheet.append(columns)
	for row in rows:
		# Missing cells are left empty, matching prior DataFrame output
		worksheet.append([row.get(column) for column in columns])
	workbook.save(output_path)


#============================================

def write_raw_table(raw_rows: list, output_path: str) -> None:
	"""
	Write raw parser rows to xlsx/csv for debugging and auditing.
	"""
	columns = ordered_columns(raw_rows)
	if output_path.lower().endswith(".csv"):
		write_rows_to_csv(raw_rows, columns, output_path)
	else:
		write_rows_to_xlsx(raw_rows, columns, output_path, "raw_data")
	print(f"Raw table saved to:\n\t{output_path}")


#============================================

def write_lab_debug_rows(lab_debug_rows: list, output_path: str) -> None:
	"""
	Write lab-only debug decisions to CSV.
	"""
	columns = ordered_columns(lab_debug_rows)
	write_rows_to_csv(lab_debug_rows, columns, output_path)
	print(f"Lab debug CSV saved to:\n\t{output_path}")
