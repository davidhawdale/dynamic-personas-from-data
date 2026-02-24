#!/usr/bin/env python3
"""
Phase 6: Prepare Persona Inputs
Parses archetypes.md and writes one JSON input pack per archetype.

Usage:
    python3 02-workflows/build-dynamic-personas/prepare-persona-inputs.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P5_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p5-synthesize-archetypes"
ARCHETYPES_PATH = P5_DIR / "archetypes.md"
EXTRACTS_DIR = P5_DIR / "extracts"

P6_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p6-create-personas"
INPUTS_DIR = P6_DIR / "persona-inputs"
PERSONAS_DIR = P6_DIR / "personas"

TEMPLATE_PATH = ROOT / "10-resources" / "templates" / "persona-template.md"


def parse_participants(line: str) -> list[str]:
    value = line.split(":", 1)[1].strip()
    value = value.strip("{}")
    return [p.strip() for p in value.split(",") if p.strip()]


def parse_archetypes(markdown: str) -> tuple[list[dict], list[str]]:
    errors = []
    lines = markdown.splitlines()

    archetypes = []
    current = None
    mode = None
    heading_re = re.compile(r"^## Archetype ([1-5]):\s*(.+?)\s*$")
    quote_line_re = re.compile(r'^>\s*"(.*)"\s*$')
    quote_pid_re = re.compile(r"^>\s*—\s*Participant\s+([A-Za-z0-9]+)\s*$")

    i = 0
    while i < len(lines):
        line = lines[i]
        h = heading_re.match(line.strip())
        if h:
            if current:
                archetypes.append(current)
            current = {
                "archetype_number": h.group(1),
                "archetype_name": h.group(2).strip(),
                "pattern": "",
                "differentiators": [],
                "participants": [],
                "evidence_quotes": [],
            }
            mode = None
            i += 1
            continue

        if current is None:
            i += 1
            continue

        stripped = line.strip()
        if stripped.startswith("Pattern:"):
            current["pattern"] = stripped.split(":", 1)[1].strip()
            i += 1
            continue

        if stripped == "Differentiators:":
            mode = "differentiators"
            i += 1
            continue

        if stripped.startswith("Participants:"):
            current["participants"] = parse_participants(stripped)
            mode = None
            i += 1
            continue

        if stripped == "Evidence Quotes:":
            mode = "quotes"
            i += 1
            continue

        if mode == "differentiators" and stripped.startswith("- "):
            current["differentiators"].append(stripped[2:].strip())
            i += 1
            continue

        if mode == "quotes":
            q1 = quote_line_re.match(stripped)
            if q1 and i + 1 < len(lines):
                q2 = quote_pid_re.match(lines[i + 1].strip())
                if q2:
                    current["evidence_quotes"].append(
                        {"quote": q1.group(1), "participant_id": q2.group(1)}
                    )
                    i += 2
                    continue

        i += 1

    if current:
        archetypes.append(current)

    if len(archetypes) != 5:
        errors.append(f"Expected 5 archetypes; found {len(archetypes)}")

    expected_nums = {"1", "2", "3", "4", "5"}
    found_nums = {a["archetype_number"] for a in archetypes}
    if found_nums != expected_nums:
        errors.append(f"Expected archetype numbers {sorted(expected_nums)}; found {sorted(found_nums)}")

    for a in archetypes:
        if not a["pattern"]:
            errors.append(f"Archetype {a['archetype_number']} missing pattern")
        if len(a["differentiators"]) < 2:
            errors.append(f"Archetype {a['archetype_number']} needs at least 2 differentiators")
        if not a["participants"]:
            errors.append(f"Archetype {a['archetype_number']} missing participants")
        if len(a["evidence_quotes"]) != 3:
            errors.append(
                f"Archetype {a['archetype_number']} must have exactly 3 evidence quotes; found {len(a['evidence_quotes'])}"
            )

    return archetypes, errors


def main():
    errors = []
    if not ARCHETYPES_PATH.exists():
        errors.append(f"Missing archetypes file: {ARCHETYPES_PATH.relative_to(ROOT)}")
    if not EXTRACTS_DIR.exists():
        errors.append(f"Missing extracts folder: {EXTRACTS_DIR.relative_to(ROOT)}")
    if not TEMPLATE_PATH.exists():
        errors.append(f"Missing persona template: {TEMPLATE_PATH.relative_to(ROOT)}")
    if errors:
        for err in errors:
            print(f"FAIL  {err}")
        print("\nStatus: FAIL")
        sys.exit(1)

    archetypes, parse_errors = parse_archetypes(ARCHETYPES_PATH.read_text(encoding="utf-8"))
    if parse_errors:
        for err in parse_errors:
            print(f"FAIL  {err}")
        print("\nStatus: FAIL")
        sys.exit(1)

    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    PERSONAS_DIR.mkdir(parents=True, exist_ok=True)

    for a in archetypes:
        extract_paths = []
        missing_extracts = []
        for pid in a["participants"]:
            extract_path = EXTRACTS_DIR / f"{pid}.md"
            if not extract_path.exists():
                missing_extracts.append(pid)
            extract_paths.append(str(extract_path.relative_to(ROOT)))
        if missing_extracts:
            print(
                f"FAIL  Archetype {a['archetype_number']} missing extracts for: "
                + ", ".join(missing_extracts)
            )
            print("\nStatus: FAIL")
            sys.exit(1)

        out = INPUTS_DIR / f"archetype-{a['archetype_number']}.json"
        default_output = PERSONAS_DIR / f"archetype-{a['archetype_number']}.md"
        output_file = str(default_output.relative_to(ROOT))
        if out.exists():
            try:
                existing = json.loads(out.read_text(encoding="utf-8"))
                existing_output = (existing.get("output_file") or "").strip()
                if existing_output:
                    existing_path = ROOT / existing_output
                    if existing_path.suffix == ".md" and PERSONAS_DIR in existing_path.parents:
                        output_file = existing_output
            except (OSError, json.JSONDecodeError):
                pass

        payload = {
            "archetype_number": a["archetype_number"],
            "archetype_name": a["archetype_name"],
            "pattern": a["pattern"],
            "differentiators": a["differentiators"],
            "participants": a["participants"],
            "evidence_quotes": a["evidence_quotes"],
            "participant_extract_files": extract_paths,
            "template_file": str(TEMPLATE_PATH.relative_to(ROOT)),
            "output_file": output_file,
        }

        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\nPhase 6: Prepare Persona Inputs")
    print(f"{'─' * 50}")
    print(f"  Archetypes file : {ARCHETYPES_PATH.relative_to(ROOT)}")
    print(f"  Input packs     : {INPUTS_DIR.relative_to(ROOT)}")
    print(f"  Persona outputs : {PERSONAS_DIR.relative_to(ROOT)}")
    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
