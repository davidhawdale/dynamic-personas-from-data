#!/usr/bin/env python3
"""
Phase 5: Extract Archetype Assignments
Parses archetypes.md and writes participant-archetype-assignments.csv.

Usage:
    python3 02-workflows/build-dynamic-personas/extract-archetype-assignments.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P5_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p5-synthesize-archetypes"
ARCHETYPES_PATH = P5_DIR / "archetypes.md"
OUTPUT_PATH = P5_DIR / "participant-archetype-assignments.csv"

OUTPUT_COLUMNS = [
    "participant_id",
    "assignment_type",
    "archetype_number",
    "archetype_name",
    "outlier_reason",
]


def parse_participants_line(line: str) -> list[str]:
    value = line.split(":", 1)[1].strip()
    value = value.strip("{}")
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def main():
    if not ARCHETYPES_PATH.exists():
        print(f"FAIL  Archetypes file not found: {ARCHETYPES_PATH.relative_to(ROOT)}")
        print("\nStatus: FAIL")
        sys.exit(1)

    lines = ARCHETYPES_PATH.read_text(encoding="utf-8").splitlines()
    assignments = []

    current_num = None
    current_name = None
    in_outliers = False

    heading_re = re.compile(r"^## Archetype ([1-5]):\s*(.+?)\s*$")
    outlier_re = re.compile(r"^\s*-\s*Participant\s+([A-Za-z0-9]+)\s*—\s*(.+)\s*$")

    for line in lines:
        m = heading_re.match(line.strip())
        if m:
            in_outliers = False
            current_num = m.group(1)
            current_name = m.group(2).strip()
            continue

        if line.strip().startswith("## Outliers"):
            in_outliers = True
            current_num = None
            current_name = None
            continue

        if line.strip().startswith("Participants:"):
            if current_num is None:
                continue
            for pid in parse_participants_line(line.strip()):
                assignments.append(
                    {
                        "participant_id": pid,
                        "assignment_type": "core",
                        "archetype_number": current_num,
                        "archetype_name": current_name or "",
                        "outlier_reason": "",
                    }
                )
            continue

        if in_outliers:
            m_out = outlier_re.match(line)
            if m_out:
                assignments.append(
                    {
                        "participant_id": m_out.group(1).strip(),
                        "assignment_type": "outlier",
                        "archetype_number": "",
                        "archetype_name": "",
                        "outlier_reason": m_out.group(2).strip(),
                    }
                )

    if not assignments:
        print("FAIL  No assignments parsed from archetypes.md")
        print("\nStatus: FAIL")
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(assignments)

    core_count = sum(1 for a in assignments if a["assignment_type"] == "core")
    outlier_count = len(assignments) - core_count

    print("\nPhase 5: Extract Archetype Assignments")
    print(f"{'─' * 50}")
    print(f"  Input archetypes : {ARCHETYPES_PATH.relative_to(ROOT)}")
    print(f"  Output CSV       : {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"  Total assigned   : {len(assignments)}")
    print(f"  Core assignments : {core_count}")
    print(f"  Outliers         : {outlier_count}")
    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
