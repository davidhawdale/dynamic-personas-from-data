#!/usr/bin/env python3
"""Write quote rows from a JSON file to a CSV file.

Usage:
    python3 write-csv.py --rows-file /tmp/{id}-rows.json --output-path /path/to/output.csv
"""
import argparse
import csv
import json

FIELDNAMES = [
    "participant_id",
    "transcript_id",
    "question_ref",
    "tag",
    "severity",
    "sentiment",
    "quote",
    "source_line_start",
    "source_line_end",
]

parser = argparse.ArgumentParser(description="Write quote rows to CSV")
parser.add_argument("--rows-file", required=True, help="Path to JSON file containing list of row dicts")
parser.add_argument("--output-path", required=True, help="Path to write the output CSV")
args = parser.parse_args()

with open(args.rows_file, encoding="utf-8") as f:
    rows = json.load(f)

with open(args.output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {args.output_path}")
