#!/usr/bin/env python3
"""
Phase 3: Verify Contradictions Completion
Checks that every participant in the manifest has a contradiction part CSV and
that each row follows the Phase 3 contradiction contract.

Usage:
    python3 02-workflows/build-dynamic-personas/verify-contradictions-completion.py

Exit codes:
    0 — PASS
    1 — FAIL (missing participants, schema errors, or invalid row values)
"""

import csv
import json
import sys
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p0-prepare" / "manifest.json"
PHASE3_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p3-check-contradictions"
PARTS_DIR = PHASE3_DIR / "contradiction-parts"

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

ALLOWED_TYPES = {"Direct", "Loyalty gap", "Confidence erosion", "Rationalisation"}
ALLOWED_SEVERITIES = {"High", "Medium", "Low"}


def validate_part(path: Path, expected_participant_id: str) -> tuple[list[dict], list[str]]:
    """Validate one participant part file. Returns (rows, errors)."""
    rows = []
    errors = []

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

    for lineno, row in enumerate(rows, start=2):
        location = f"{path.name}:{lineno}"

        required_non_empty = [
            "participant_id",
            "transcript_id",
            "contradiction_type",
            "severity",
            "quote_a_tag",
            "quote_a",
            "explanation",
        ]
        for field in required_non_empty:
            if not (row.get(field) or "").strip():
                errors.append(f"{location}: required field '{field}' is empty")

        row_participant = (row.get("participant_id") or "").strip()
        if row_participant and row_participant != expected_participant_id:
            errors.append(
                f"{location}: participant_id '{row_participant}' does not match part file "
                f"'{expected_participant_id}'"
            )

        contradiction_type = (row.get("contradiction_type") or "").strip()
        if contradiction_type and contradiction_type not in ALLOWED_TYPES:
            errors.append(
                f"{location}: contradiction_type '{contradiction_type}' is invalid "
                f"(allowed: {sorted(ALLOWED_TYPES)})"
            )

        severity = (row.get("severity") or "").strip()
        if severity and severity not in ALLOWED_SEVERITIES:
            errors.append(
                f"{location}: severity '{severity}' is invalid "
                f"(allowed: {sorted(ALLOWED_SEVERITIES)})"
            )

        quote_b_tag = (row.get("quote_b_tag") or "").strip()
        quote_b = (row.get("quote_b") or "").strip()

        if contradiction_type == "Rationalisation":
            if quote_b_tag or quote_b:
                errors.append(
                    f"{location}: Rationalisation rows must leave quote_b_tag and quote_b empty"
                )
        elif contradiction_type in ALLOWED_TYPES:
            if not quote_b_tag:
                errors.append(
                    f"{location}: {contradiction_type} rows require non-empty quote_b_tag"
                )
            if not quote_b:
                errors.append(f"{location}: {contradiction_type} rows require non-empty quote_b")

    return rows, errors


def main():
    errors = []

    if not MANIFEST_PATH.exists():
        print(f"FAIL  Manifest not found: {MANIFEST_PATH.relative_to(ROOT)}")
        print("\nStatus: FAIL")
        sys.exit(1)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    expected_participants = {t["participant_id"] for t in manifest["transcripts"]}

    if not PARTS_DIR.exists():
        print(f"FAIL  contradiction-parts directory not found: {PARTS_DIR.relative_to(ROOT)}")
        print("\nStatus: FAIL")
        sys.exit(1)

    part_files = sorted(PARTS_DIR.glob("*.csv"))
    part_stems = {p.stem for p in part_files}

    missing = expected_participants - part_stems
    unexpected = part_stems - expected_participants

    if missing:
        errors.append(
            f"{len(missing)} participant(s) in manifest but missing contradiction part files: "
            + ", ".join(sorted(missing))
        )

    if unexpected:
        errors.append(
            f"{len(unexpected)} contradiction part file(s) not found in manifest: "
            + ", ".join(sorted(unexpected))
        )

    total_rows = 0
    participants_with_contradictions = 0

    for part in part_files:
        rows, part_errors = validate_part(part, part.stem)
        total_rows += len(rows)
        if rows:
            participants_with_contradictions += 1
        errors.extend(part_errors)

    print("\nPhase 3: Verify Contradictions Completion")
    print(f"{'─' * 50}")
    print(f"  Manifest participants       : {len(expected_participants)}")
    print(f"  Part files found            : {len(part_files)}")
    print(f"  Missing part files          : {len(missing)}")
    print(f"  Unexpected part files       : {len(unexpected)}")
    print(f"  Participants with any rows  : {participants_with_contradictions}")
    print(f"  Total contradiction rows    : {total_rows}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print("\nStatus: FAIL")
        sys.exit(1)

    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
