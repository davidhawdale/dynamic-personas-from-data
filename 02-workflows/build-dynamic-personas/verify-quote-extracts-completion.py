#!/usr/bin/env python3
"""
Phase 1: Verify Quote Extracts Completion
Checks that every participant in the manifest has extracted quotes in quotes.csv.

Usage:
    python3 02-workflows/build-dynamic-personas/verify-quote-extracts-completion.py

Exit codes:
    0 — PASS (or PASS with warnings)
    1 — FAIL (missing participants, unexpected participants, or file not found)
"""

import csv
import json
import sys
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p0-prepare" / "manifest.json"
PHASE1_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p1-quote-extraction"
QUOTES_PATH = PHASE1_DIR / "quotes.csv"
PARTS_DIR = PHASE1_DIR / "quote-parts"


def main():
    warnings = []
    errors = []

    # ── Check manifest ──────────────────────────────────────────────────────────

    if not MANIFEST_PATH.exists():
        print(f"FAIL  Manifest not found: {MANIFEST_PATH.relative_to(ROOT)}")
        print(f"\nStatus: FAIL")
        sys.exit(1)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    expected_participants = {t["participant_id"] for t in manifest["transcripts"]}
    expected_transcript_ids = {t["id"] for t in manifest["transcripts"]}

    # ── Check quotes.csv ────────────────────────────────────────────────────────

    if not QUOTES_PATH.exists():
        print(f"FAIL  quotes.csv not found: {QUOTES_PATH.relative_to(ROOT)}")
        print(f"      Run merge-quotes.py first.")
        print(f"\nStatus: FAIL")
        sys.exit(1)

    # ── Read participants present in quotes.csv ─────────────────────────────────

    found_participants = set()
    found_transcript_ids = set()
    with open(QUOTES_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            found_participants.add(row["participant_id"])
            found_transcript_ids.add(row["transcript_id"])

    # ── Compare ─────────────────────────────────────────────────────────────────

    missing = expected_participants - found_participants
    unexpected = found_participants - expected_participants

    if missing:
        errors.append(
            f"{len(missing)} participant(s) in manifest but missing from quotes.csv: "
            + ", ".join(sorted(missing))
        )

    if unexpected:
        errors.append(
            f"{len(unexpected)} participant(s) in quotes.csv but not in manifest: "
            + ", ".join(sorted(unexpected))
        )

    # ── Check quote-parts/ files ────────────────────────────────────────────────

    if PARTS_DIR.exists():
        part_stems = {p.stem for p in PARTS_DIR.glob("*.csv")}
        missing_parts = expected_participants - part_stems
        unexpected_parts = part_stems - expected_participants
        if missing_parts:
            warnings.append(
                f"{len(missing_parts)} expected part file(s) missing from quote-parts/: "
                + ", ".join(sorted(missing_parts))
            )
        if unexpected_parts:
            warnings.append(
                f"{len(unexpected_parts)} unexpected part file(s) in quote-parts/: "
                + ", ".join(sorted(unexpected_parts))
            )
    else:
        warnings.append(f"quote-parts/ directory not found — skipping part-file check")

    # ── Report ──────────────────────────────────────────────────────────────────

    print(f"\nPhase 1: Verify Quote Extracts Completion")
    print(f"{'─' * 50}")
    print(f"  Manifest participants : {len(expected_participants)}")
    print(f"  Found in quotes.csv  : {len(found_participants)}")
    print(f"  Missing              : {len(missing)}")
    print(f"  Unexpected           : {len(unexpected)}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN  {w}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\nStatus: FAIL")
        sys.exit(1)

    print(f"\nStatus: {'PASS' if not warnings else 'PASS (with warnings)'}")


if __name__ == "__main__":
    main()
