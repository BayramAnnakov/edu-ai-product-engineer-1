# csv_tool.py
import csv
from agents import function_tool

# Global variable to hold current CSV file path (set by runner)
CSV_FILE_PATH = None  # Initialize as None to make it clear it needs to be set

@function_tool
def preview_csv(file_path: str, num_rows: int) -> str:
    """
    Reads the first few lines of the CSV file and returns a summary of the columns and sample rows.
    """
    # Determine which file to use
    path = file_path or CSV_FILE_PATH
    if not path:
        return "No CSV file specified."

    try:
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for _, row in zip(range(num_rows + 1), reader)]
    except Exception as e:
        return f"Error reading CSV: {e}"

    if not rows:
        return "CSV file is empty."
    # The first row is assumed to be header
    header = rows[0]
    sample_rows = rows[1:]
    # Format a preview string
    preview_lines = [f"Columns: {', '.join(header)}"]
    for i, row in enumerate(sample_rows, start=1):
        preview_lines.append(f"Row {i}: " + ", ".join(row))
    if len(sample_rows) == 0:
        preview_lines.append("(No data rows to display)")
    return "\n".join(preview_lines)
