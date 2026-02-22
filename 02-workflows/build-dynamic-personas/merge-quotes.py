#!/usr/bin/env python3
"""
Phase 1: Merge Quotes
Merges per-participant quote CSVs from quote-parts/ into a single quotes.csv.

Usage:
    python3 02-workflows/build-dynamic-personas/merge-quotes.py

Exit codes:
    0 — PASS (or PASS with warnings)
    1 — FAIL (missing inputs or schema errors)
"""

import csv
import sys
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
PARTS_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p1-quote-extraction" / "quote-parts"
OUTPUT_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p1-quote-extraction" / "quotes.csv"

EXPECTED_COLUMNS = [
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


def load_part(path: Path) -> tuple[list[dict], list[str]]:
    """Load and validate a single part CSV. Returns (rows, errors)."""
    errors = []
    rows = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if list(reader.fieldnames or []) != EXPECTED_COLUMNS:
                errors.append(
                    f"{path.name}: unexpected columns {reader.fieldnames} "
                    f"(expected {EXPECTED_COLUMNS})"
                )
                return rows, errors
            rows = list(reader)
    except Exception as e:
        errors.append(f"{path.name}: could not read — {e}")
    return rows, errors


def dedup_key(row: dict) -> tuple:
    return (row["participant_id"], row["question_ref"], row["quote"])


def main():
    warnings = []
    errors = []

    # ── Check parts directory ───────────────────────────────────────────────────

    if not PARTS_DIR.exists():
        print(f"FAIL  Parts directory not found: {PARTS_DIR.relative_to(ROOT)}")
        sys.exit(1)

    part_files = sorted(PARTS_DIR.glob("*.csv"))
    if not part_files:
        print(f"FAIL  No CSV files found in {PARTS_DIR.relative_to(ROOT)}")
        sys.exit(1)

    # ── Load all parts ──────────────────────────────────────────────────────────

    all_rows = []
    for part in part_files:
        rows, errs = load_part(part)
        if errs:
            errors.extend(errs)
        else:
            all_rows.extend(rows)

    if errors:
        print(f"\nPhase 1: Merge Quotes")
        print(f"{'─' * 50}")
        print(f"  Parts dir : {PARTS_DIR.relative_to(ROOT)}")
        print(f"  Part files: {len(part_files)}")
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\nStatus: FAIL — quotes.csv not written")
        sys.exit(1)

    # ── Deduplicate ─────────────────────────────────────────────────────────────

    seen = set()
    deduped = []
    dropped = 0
    for row in all_rows:
        key = dedup_key(row)
        if key in seen:
            dropped += 1
        else:
            seen.add(key)
            deduped.append(row)

    if dropped:
        warnings.append(f"Dropped {dropped} exact duplicate row(s)")

    # ── Sort ────────────────────────────────────────────────────────────────────

    def sort_key(row):
        try:
            line = int(row["source_line_start"])
        except (ValueError, KeyError):
            line = 0
        return (row["participant_id"], line, row["question_ref"])

    deduped.sort(key=sort_key)

    # ── Write output ────────────────────────────────────────────────────────────

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerows(deduped)

    # ── Report ──────────────────────────────────────────────────────────────────

    print(f"\nPhase 1: Merge Quotes")
    print(f"{'─' * 50}")
    print(f"  Parts dir  : {PARTS_DIR.relative_to(ROOT)}")
    print(f"  Part files : {len(part_files)}")
    print(f"  Total rows : {len(all_rows)}")
    print(f"  After dedup: {len(deduped)}")
    print(f"  Output     : {OUTPUT_PATH.relative_to(ROOT)}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN  {w}")

    print(f"\nStatus: {'PASS' if not warnings else 'PASS (with warnings)'}")


if __name__ == "__main__":
    main()
