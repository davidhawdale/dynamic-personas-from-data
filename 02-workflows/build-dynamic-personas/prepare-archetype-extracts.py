#!/usr/bin/env python3
"""
Phase 5: Prepare Archetype Extracts
Builds per-participant markdown extract files from consolidated quotes for the
archetype-writer agent.

Usage:
    python3 02-workflows/build-dynamic-personas/prepare-archetype-extracts.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p0-prepare" / "manifest.json"
INPUT_QUOTES_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p4-consolidate-tags" / "consolidated-quotes.csv"
P5_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p5-synthesize-archetypes"
EXTRACTS_DIR = P5_DIR / "extracts"
EXPECTED_PARTICIPANTS_PATH = P5_DIR / "expected-participants.json"

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
    "consolidated_tag",
]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def main():
    errors = []

    if not MANIFEST_PATH.exists():
        errors.append(f"Manifest not found: {MANIFEST_PATH.relative_to(ROOT)}")
    if not INPUT_QUOTES_PATH.exists():
        errors.append(f"Consolidated quotes not found: {INPUT_QUOTES_PATH.relative_to(ROOT)}")
    if errors:
        for err in errors:
            print(f"FAIL  {err}")
        print("\nStatus: FAIL")
        sys.exit(1)

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    expected_participants = sorted({t["participant_id"] for t in manifest["transcripts"]})

    with open(INPUT_QUOTES_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if list(reader.fieldnames or []) != EXPECTED_COLUMNS:
            print(
                f"FAIL  consolidated-quotes.csv columns were {reader.fieldnames}; "
                f"expected {EXPECTED_COLUMNS}"
            )
            print("\nStatus: FAIL")
            sys.exit(1)
        rows = list(reader)

    by_participant = defaultdict(list)
    for row in rows:
        by_participant[row["participant_id"]].append(row)

    missing_rows = [pid for pid in expected_participants if pid not in by_participant]
    if missing_rows:
        print(
            "FAIL  Some expected participants had no consolidated rows: "
            + ", ".join(missing_rows[:20])
            + ("..." if len(missing_rows) > 20 else "")
        )
        print("\nStatus: FAIL")
        sys.exit(1)

    EXTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    for pid in expected_participants:
        participant_rows = by_participant[pid]
        transcript_ids = sorted({r["transcript_id"] for r in participant_rows})
        grouped = defaultdict(list)
        for row in participant_rows:
            grouped[row["consolidated_tag"]].append(row)

        lines = [
            f"# Participant {pid}",
            "",
            f"- Participant ID: `{pid}`",
            f"- Transcript IDs: `{', '.join(transcript_ids)}`",
            f"- Quote count: {len(participant_rows)}",
            "",
        ]

        for consolidated_tag in sorted(grouped.keys(), key=lambda s: s.lower()):
            lines.append(f"## {consolidated_tag}")
            lines.append("")
            for i, row in enumerate(
                sorted(grouped[consolidated_tag], key=lambda r: (r["question_ref"], r["tag"])),
                start=1,
            ):
                lines.append(f"### Quote {i}")
                lines.append(f"- Original tag: {row['tag']}")
                lines.append(f"- Question ref: {row['question_ref']}")
                lines.append(f"- Severity: {row['severity']}")
                lines.append(f"- Sentiment: {row['sentiment']}")
                lines.append(
                    f"- Transcript lines: {row['source_line_start']}-{row['source_line_end']}"
                )
                lines.append("")
                lines.append(f"> {row['quote']}")
                lines.append("")

        output_path = EXTRACTS_DIR / f"{pid}.md"
        output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    EXPECTED_PARTICIPANTS_PATH.write_text(
        json.dumps({"expected_participants": expected_participants}, indent=2) + "\n",
        encoding="utf-8",
    )

    print("\nPhase 5: Prepare Archetype Extracts")
    print(f"{'─' * 50}")
    print(f"  Input quotes      : {INPUT_QUOTES_PATH.relative_to(ROOT)}")
    print(f"  Participants      : {len(expected_participants)}")
    print(f"  Output extracts   : {EXTRACTS_DIR.relative_to(ROOT)}")
    print(f"  Expected IDs file : {EXPECTED_PARTICIPANTS_PATH.relative_to(ROOT)}")
    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
