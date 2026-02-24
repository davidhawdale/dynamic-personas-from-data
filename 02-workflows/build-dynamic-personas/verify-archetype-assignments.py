#!/usr/bin/env python3
"""
Phase 5: Verify Archetype Assignments
Validates archetypes.md structure and participant assignment coverage.

Usage:
    python3 02-workflows/build-dynamic-personas/verify-archetype-assignments.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P5_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p5-synthesize-archetypes"
EXPECTED_IDS_PATH = P5_DIR / "expected-participants.json"
ARCHETYPES_PATH = P5_DIR / "archetypes.md"
ASSIGNMENTS_PATH = P5_DIR / "participant-archetype-assignments.csv"

ASSIGNMENT_COLUMNS = [
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


def verify_archetypes_md(expected_ids: set[str]) -> tuple[list[str], dict[str, set[str]]]:
    errors = []
    archetype_participants: dict[str, set[str]] = defaultdict(set)

    if not ARCHETYPES_PATH.exists():
        return [f"Archetypes file not found: {ARCHETYPES_PATH.relative_to(ROOT)}"], archetype_participants

    lines = ARCHETYPES_PATH.read_text(encoding="utf-8").splitlines()
    heading_re = re.compile(r"^## Archetype ([1-5]):\s*(.+?)\s*$")
    quote_participant_re = re.compile(r"^>\s*—\s*Participant\s+([A-Za-z0-9]+)\s*$")

    archetype_sections = []
    current_num = None
    in_outliers = False
    quote_counts = Counter()
    quote_participants: dict[str, list[str]] = defaultdict(list)

    for line in lines:
        m = heading_re.match(line.strip())
        if m:
            current_num = m.group(1)
            in_outliers = False
            archetype_sections.append(current_num)
            continue

        if line.strip().startswith("## Outliers"):
            in_outliers = True
            current_num = None
            continue

        if in_outliers:
            continue

        if current_num and line.strip().startswith("Participants:"):
            participants = parse_participants_line(line.strip())
            for pid in participants:
                archetype_participants[current_num].add(pid)
            continue

        if current_num:
            m_quote = quote_participant_re.match(line.strip())
            if m_quote:
                pid = m_quote.group(1).strip()
                quote_counts[current_num] += 1
                quote_participants[current_num].append(pid)
                if pid not in expected_ids:
                    errors.append(
                        f"Archetype {current_num} quote participant '{pid}' not found in expected participants"
                    )

    if len(archetype_sections) != 5 or sorted(archetype_sections) != ["1", "2", "3", "4", "5"]:
        errors.append(
            f"archetypes.md must contain exactly five core archetypes numbered 1-5; found {sorted(set(archetype_sections))}"
        )

    for num in ["1", "2", "3", "4", "5"]:
        participants = archetype_participants.get(num, set())
        if not participants:
            errors.append(f"Archetype {num} has no Participants line or empty participant list")

        if quote_counts.get(num, 0) != 3:
            errors.append(
                f"Archetype {num} must have exactly 3 evidence quote participant lines; found {quote_counts.get(num, 0)}"
            )

        q_participants = quote_participants.get(num, [])
        if len(set(q_participants)) != len(q_participants):
            errors.append(f"Archetype {num} evidence quotes must come from distinct participants")

        for q_pid in q_participants:
            if q_pid not in participants:
                errors.append(
                    f"Archetype {num} quote participant '{q_pid}' is not listed in its Participants line"
                )

    return errors, archetype_participants


def main():
    errors = []

    if not EXPECTED_IDS_PATH.exists():
        errors.append(f"Missing expected participants file: {EXPECTED_IDS_PATH.relative_to(ROOT)}")
    if not ASSIGNMENTS_PATH.exists():
        errors.append(f"Missing assignments CSV: {ASSIGNMENTS_PATH.relative_to(ROOT)}")
    if errors:
        for err in errors:
            print(f"FAIL  {err}")
        print("\nStatus: FAIL")
        sys.exit(1)

    expected_payload = json.loads(EXPECTED_IDS_PATH.read_text(encoding="utf-8"))
    expected_ids = set(expected_payload.get("expected_participants", []))
    if not expected_ids:
        print("FAIL  expected-participants.json has no expected_participants entries")
        print("\nStatus: FAIL")
        sys.exit(1)

    with open(ASSIGNMENTS_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if list(reader.fieldnames or []) != ASSIGNMENT_COLUMNS:
            print(
                f"FAIL  assignment CSV columns were {reader.fieldnames}; expected {ASSIGNMENT_COLUMNS}"
            )
            print("\nStatus: FAIL")
            sys.exit(1)
        rows = list(reader)

    assigned_ids = [r["participant_id"].strip() for r in rows if r["participant_id"].strip()]
    assigned_set = set(assigned_ids)

    duplicates = sorted([pid for pid, c in Counter(assigned_ids).items() if c > 1])
    if duplicates:
        errors.append("Duplicate participant assignments: " + ", ".join(duplicates))

    missing = sorted(expected_ids - assigned_set)
    unexpected = sorted(assigned_set - expected_ids)
    if missing:
        errors.append(
            f"{len(missing)} expected participant(s) missing from assignments: "
            + ", ".join(missing[:20])
            + ("..." if len(missing) > 20 else "")
        )
    if unexpected:
        errors.append(
            f"{len(unexpected)} unexpected participant(s) in assignments: "
            + ", ".join(unexpected[:20])
            + ("..." if len(unexpected) > 20 else "")
        )

    for r in rows:
        atype = r["assignment_type"].strip()
        if atype not in {"core", "outlier"}:
            errors.append(
                f"Invalid assignment_type '{atype}' for participant '{r['participant_id']}'"
            )
        if atype == "core":
            if r["archetype_number"].strip() not in {"1", "2", "3", "4", "5"}:
                errors.append(
                    f"Core assignment for participant '{r['participant_id']}' must have archetype_number 1-5"
                )
            if not r["archetype_name"].strip():
                errors.append(
                    f"Core assignment for participant '{r['participant_id']}' missing archetype_name"
                )
        if atype == "outlier" and not r["outlier_reason"].strip():
            errors.append(f"Outlier participant '{r['participant_id']}' missing outlier_reason")

    md_errors, _ = verify_archetypes_md(expected_ids)
    errors.extend(md_errors)

    print("\nPhase 5: Verify Archetype Assignments")
    print(f"{'─' * 50}")
    print(f"  Expected IDs file : {EXPECTED_IDS_PATH.relative_to(ROOT)}")
    print(f"  Archetypes file   : {ARCHETYPES_PATH.relative_to(ROOT)}")
    print(f"  Assignments CSV   : {ASSIGNMENTS_PATH.relative_to(ROOT)}")
    print(f"  Expected count    : {len(expected_ids)}")
    print(f"  Assigned count    : {len(assigned_set)}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for err in errors:
            print(f"  FAIL  {err}")
        print("\nStatus: FAIL")
        sys.exit(1)

    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
