#!/usr/bin/env python3
"""Write contradiction rows from a JSON file to a CSV file.

Usage:
    python3 write-csv.py --rows-file /tmp/{id}-contradictions.json --output-path /path/to/output.csv
"""
import argparse
import csv
import json

FIELDNAMES = [
    "participant_id",
    "transcript_id",
    "contradiction_type",
    "severity",
    "quote_a_tag",
    "quote_a",
    "quote_b_tag",
    "quote_b",
    "explanation",
]

parser = argparse.ArgumentParser(description="Write contradiction rows to CSV")
parser.add_argument("--rows-file", required=True, help="Path to JSON file containing list of row dicts")
parser.add_argument("--output-path", required=True, help="Path to write the output CSV")
args = parser.parse_args()

with open(args.rows_file, encoding="utf-8") as f:
    rows = json.load(f)

import os
os.makedirs(os.path.dirname(args.output_path), exist_ok=True)

with open(args.output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} row(s) to {args.output_path}")
