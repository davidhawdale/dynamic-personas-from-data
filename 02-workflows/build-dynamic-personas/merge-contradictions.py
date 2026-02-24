#!/usr/bin/env python3
"""
Phase 3: Merge Contradictions
Merges per-participant contradiction CSVs from contradiction-parts/ into a single contradictions.csv.

Usage:
    python3 02-workflows/build-dynamic-personas/merge-contradictions.py

Exit codes:
    0 — PASS (or PASS with warnings)
    1 — FAIL (missing inputs or schema errors)
"""

import csv
import json
import sys
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
PARTS_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p3-check-contradictions" / "contradiction-parts"
OUTPUT_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p3-check-contradictions" / "contradictions.csv"
MANIFEST_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p0-prepare" / "manifest.json"

EXPECTED_COLUMNS = [
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


def main():
    warnings = []
    errors = []

    # ── Load manifest ────────────────────────────────────────────────────────────

    if not MANIFEST_PATH.exists():
        print(f"FAIL  Manifest not found: {MANIFEST_PATH.relative_to(ROOT)}")
        sys.exit(1)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    expected_participants = {t["participant_id"] for t in manifest["transcripts"]}

    # ── Check parts directory ───────────────────────────────────────────────────

    if not PARTS_DIR.exists():
        print(f"FAIL  Parts directory not found: {PARTS_DIR.relative_to(ROOT)}")
        sys.exit(1)

    part_files = sorted(PARTS_DIR.glob("*.csv"))
    if not part_files:
        print(f"FAIL  No CSV files found in {PARTS_DIR.relative_to(ROOT)}")
        sys.exit(1)

    part_stems = {p.stem for p in part_files}
    missing_parts = expected_participants - part_stems
    unexpected_parts = part_stems - expected_participants
    if missing_parts:
        errors.append(
            f"{len(missing_parts)} participant(s) in manifest but missing contradiction parts: "
            + ", ".join(sorted(missing_parts))
        )
    if unexpected_parts:
        errors.append(
            f"{len(unexpected_parts)} contradiction part file(s) not found in manifest: "
            + ", ".join(sorted(unexpected_parts))
        )

    # ── Load all parts ──────────────────────────────────────────────────────────

    all_rows = []
    empty_parts = []
    for part in part_files:
        rows, errs = load_part(part)
        if errs:
            errors.extend(errs)
        else:
            if not rows:
                empty_parts.append(part.name)
            all_rows.extend(rows)

    if errors:
        print(f"\nPhase 3: Merge Contradictions")
        print(f"{'─' * 50}")
        print(f"  Manifest participants : {len(expected_participants)}")
        print(f"  Parts dir : {PARTS_DIR.relative_to(ROOT)}")
        print(f"  Part files: {len(part_files)}")
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\nStatus: FAIL — contradictions.csv not written")
        sys.exit(1)

    if empty_parts:
        warnings.append(f"{len(empty_parts)} participant(s) had no contradictions: {', '.join(empty_parts)}")

    # ── Sort by participant_id ──────────────────────────────────────────────────

    all_rows.sort(
        key=lambda r: (
            r["participant_id"],
            r["transcript_id"],
            r["quote_a_tag"],
            r["quote_b_tag"],
        )
    )

    # ── Write output ────────────────────────────────────────────────────────────

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    # ── Report ──────────────────────────────────────────────────────────────────

    participants_with = len({r["participant_id"] for r in all_rows})

    print(f"\nPhase 3: Merge Contradictions")
    print(f"{'─' * 50}")
    print(f"  Manifest participants : {len(expected_participants)}")
    print(f"  Parts dir             : {PARTS_DIR.relative_to(ROOT)}")
    print(f"  Part files            : {len(part_files)}")
    print(f"  Total contradictions  : {len(all_rows)}")
    print(f"  Participants with any : {participants_with}")
    print(f"  Output                : {OUTPUT_PATH.relative_to(ROOT)}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN  {w}")

    print(f"\nStatus: {'PASS' if not warnings else 'PASS (with warnings)'}")


if __name__ == "__main__":
    main()
