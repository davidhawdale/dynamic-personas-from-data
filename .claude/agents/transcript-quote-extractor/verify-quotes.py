#!/usr/bin/env python3
"""Verify that every quote in the output CSV is verbatim in the source transcript.

Usage:
    python3 verify-quotes.py --transcript-path /path/to/transcript.md --output-path /path/to/quotes.csv

Exits 0 if all quotes pass. Exits 1 and prints failures if any quotes fail.
"""
import argparse
import csv
import re
import sys

def norm(text):
    for a, b in [("\u2018", "'"), ("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"')]:
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip().lower()

parser = argparse.ArgumentParser(description="Verbatim quote verification")
parser.add_argument("--transcript-path", required=True, help="Path to source transcript file")
parser.add_argument("--output-path", required=True, help="Path to quotes CSV file")
args = parser.parse_args()

transcript_text = norm(open(args.transcript_path, encoding="utf-8").read())

with open(args.output_path, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

failures = []
for row in rows:
    quote = norm(row["quote"])
    for seg in [s.strip() for s in quote.split("...") if s.strip()]:
        if seg not in transcript_text:
            failures.append((row["tag"], seg[:80]))
            break

if failures:
    print("VERBATIM CHECK FAILED — fix these quotes before finishing:")
    for tag, seg in failures:
        print(f"  [{tag}] segment not found: {seg!r}")
    sys.exit(1)
else:
    print(f"Verbatim check: all {len(rows)} quotes PASS")
