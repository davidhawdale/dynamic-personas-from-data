#!/usr/bin/env python3
"""
Phase 6: Verify Personas
Validates persona file structure and quote attribution against archetype assignments.

Usage:
    python3 02-workflows/build-dynamic-personas/verify-personas.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P5_ASSIGNMENTS = ROOT / "04-process" / "build-dynamic-personas" / "p5-synthesize-archetypes" / "participant-archetype-assignments.csv"
P6_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p6-create-personas"
PERSONAS_DIR = P6_DIR / "personas"
INPUTS_DIR = P6_DIR / "persona-inputs"

REQUIRED_HEADINGS = [
    "## Key Characteristics",
    "## Demographics",
    "## Key Needs and Goals",
    "## Behaviours",
    "## Pain Points",
    "## Key Quotes",
    "## Relevant Experience, Digital Fluency and Consumer Habits",
    "## Personality Traits and Mindset",
    "## Backstory",
]

QUOTE_RE = re.compile(r'^>\s*"(.*)"\s*$')
QUOTE_PID_RE = re.compile(r"^>\s*—\s*Participant\s+([A-Za-z0-9]+)\s*$")


def load_expected_participants_by_archetype() -> tuple[dict[str, set[str]], list[str]]:
    errors = []
    by_arch: dict[str, set[str]] = {str(i): set() for i in range(1, 6)}
    if not P5_ASSIGNMENTS.exists():
        return by_arch, [f"Missing assignments file: {P5_ASSIGNMENTS.relative_to(ROOT)}"]

    with open(P5_ASSIGNMENTS, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        if row.get("assignment_type") != "core":
            continue
        n = (row.get("archetype_number") or "").strip()
        pid = (row.get("participant_id") or "").strip()
        if n in by_arch and pid:
            by_arch[n].add(pid)
        else:
            errors.append(f"Invalid core assignment row: {row}")
    return by_arch, errors


def split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections = {}
    current = None
    for line in lines:
        if line.startswith("## "):
            current = line.strip()
            sections[current] = []
        elif current:
            sections[current].append(line)
    return sections


def section_is_nonempty(lines: list[str]) -> bool:
    for line in lines:
        if line.strip() and not line.strip().startswith("#"):
            return True
    return False


def verify_file(path: Path, expected_participants: set[str]) -> list[str]:
    errors = []
    lines = path.read_text(encoding="utf-8").splitlines()
    text = "\n".join(lines)

    for h in REQUIRED_HEADINGS:
        if h not in text:
            errors.append(f"{path.name}: missing heading '{h}'")

    sections = split_sections(lines)
    for h in REQUIRED_HEADINGS:
        if h in sections and not section_is_nonempty(sections[h]):
            errors.append(f"{path.name}: heading '{h}' has no content")

    # Key Quotes must include exactly 2 quote blocks.
    key_quotes = sections.get("## Key Quotes", [])
    quote_blocks = []
    i = 0
    while i < len(key_quotes):
        q = QUOTE_RE.match(key_quotes[i].strip())
        if q and i + 1 < len(key_quotes):
            qp = QUOTE_PID_RE.match(key_quotes[i + 1].strip())
            if qp:
                quote_blocks.append((q.group(1), qp.group(1)))
                i += 2
                continue
        i += 1

    if len(quote_blocks) != 2:
        errors.append(f"{path.name}: ## Key Quotes must contain exactly 2 quote blocks; found {len(quote_blocks)}")
    else:
        for _, pid in quote_blocks:
            if pid not in expected_participants:
                errors.append(
                    f"{path.name}: quote participant '{pid}' is not assigned to this archetype"
                )

    return errors


def load_expected_persona_paths() -> tuple[dict[str, Path], list[str]]:
    errors = []
    expected: dict[str, Path] = {}
    if not INPUTS_DIR.exists():
        return expected, [f"Missing persona-inputs directory: {INPUTS_DIR.relative_to(ROOT)}"]

    for i in range(1, 6):
        pack = INPUTS_DIR / f"archetype-{i}.json"
        if not pack.exists():
            errors.append(f"Missing persona input pack: {pack.relative_to(ROOT)}")
            continue
        try:
            data = json.loads(pack.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            errors.append(f"Could not parse {pack.relative_to(ROOT)}: {e}")
            continue

        output_file = (data.get("output_file") or "").strip()
        if not output_file:
            errors.append(f"{pack.name}: missing output_file")
            continue

        output_path = ROOT / output_file
        if output_path.suffix != ".md":
            errors.append(f"{pack.name}: output_file must be a .md path")
            continue
        if PERSONAS_DIR not in output_path.parents:
            errors.append(f"{pack.name}: output_file must be under {PERSONAS_DIR.relative_to(ROOT)}")
            continue
        expected[str(i)] = output_path

    if len({p.name for p in expected.values()}) != len(expected):
        errors.append("Persona output_file names must be unique across archetypes")
    return expected, errors


def main():
    errors = []
    by_arch, assignment_errors = load_expected_participants_by_archetype()
    errors.extend(assignment_errors)
    expected_paths, path_errors = load_expected_persona_paths()
    errors.extend(path_errors)

    if not PERSONAS_DIR.exists():
        errors.append(f"Missing personas directory: {PERSONAS_DIR.relative_to(ROOT)}")

    files = []
    if not errors:
        files = sorted(PERSONAS_DIR.glob("*.md"))
        if len(files) != 5:
            errors.append(f"Expected 5 persona files; found {len(files)}")

    expected_names = {p.name for p in expected_paths.values()}
    found_names = {p.name for p in files}
    missing_names = sorted(expected_names - found_names)
    extra_names = sorted(found_names - expected_names)
    if missing_names:
        errors.append("Missing persona files: " + ", ".join(missing_names))
    if extra_names:
        errors.append("Unexpected persona files: " + ", ".join(extra_names))

    if not errors and len(expected_paths) == 5:
        for i in range(1, 6):
            path = expected_paths[str(i)]
            errors.extend(verify_file(path, by_arch[str(i)]))

    print("\nPhase 6: Verify Personas")
    print(f"{'─' * 50}")
    print(f"  Personas dir: {PERSONAS_DIR.relative_to(ROOT)}")
    print(f"  Files found : {len(files)}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print("\nStatus: FAIL")
        sys.exit(1)

    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
