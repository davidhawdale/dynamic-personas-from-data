#!/usr/bin/env python3
"""
Phase 7/8: Verify Roleplay Pack

Usage:
  python3 02-workflows/build-dynamic-personas/verify-roleplay-pack.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P7_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p7-role-play"
P6_PERSONAS_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p6-create-personas" / "personas"
PACK = P7_DIR / "session-pack.json"
PROMPT = P7_DIR / "panel-system-prompt.md"
RUNBOOK = P7_DIR / "session-runbook.md"


def fail(msg: str) -> None:
    print(f"FAIL  {msg}")


def main() -> None:
    errors: list[str] = []
    for p in [PACK, PROMPT, RUNBOOK]:
        if not p.exists():
            errors.append(f"Missing required file: {p.relative_to(ROOT)}")

    data = {}
    if not errors:
        try:
            data = json.loads(PACK.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {PACK.relative_to(ROOT)}: {e}")

    personas = data.get("personas", []) if isinstance(data, dict) else []
    if len(personas) != 5:
        errors.append(f"Expected exactly 5 personas; found {len(personas)}")

    seen_names: set[str] = set()
    seen_slugs: set[str] = set()
    persona_files_found = set()

    for idx, persona in enumerate(personas, start=1):
        name = (persona.get("persona_name") or "").strip()
        slug = (persona.get("persona_slug") or "").strip()
        persona_file = (persona.get("persona_file") or "").strip()
        participants = persona.get("participants") or []
        evidence = persona.get("evidence_refs") or []
        contradictions = persona.get("contradictions")

        if not name:
            errors.append(f"Persona {idx} missing persona_name")
        if not slug:
            errors.append(f"Persona {idx} missing persona_slug")
        if not persona_file:
            errors.append(f"Persona {idx} missing persona_file")
        if name in seen_names:
            errors.append(f"Duplicate persona_name: {name}")
        if slug in seen_slugs:
            errors.append(f"Duplicate persona_slug: {slug}")
        seen_names.add(name)
        seen_slugs.add(slug)

        if persona_file:
            full = ROOT / persona_file
            if not full.exists():
                errors.append(f"{name or f'Persona {idx}'} persona_file does not exist: {persona_file}")
            else:
                persona_files_found.add(full.resolve())

        if not participants:
            errors.append(f"{name or f'Persona {idx}'} has no participants")

        if len(evidence) < 2:
            errors.append(f"{name or f'Persona {idx}'} requires at least 2 evidence refs")

        for ref in evidence:
            if not ref.get("ref_id") or not ref.get("participant_id") or not ref.get("quote"):
                errors.append(f"{name or f'Persona {idx}'} has malformed evidence ref: {ref}")

        if contradictions is None:
            errors.append(f"{name or f'Persona {idx}'} missing contradictions field")

    on_disk_personas = {p.resolve() for p in P6_PERSONAS_DIR.glob("*.md")} if P6_PERSONAS_DIR.exists() else set()
    if len(on_disk_personas) != 5:
        errors.append(f"Expected 5 persona markdown files in {P6_PERSONAS_DIR.relative_to(ROOT)}; found {len(on_disk_personas)}")
    if on_disk_personas and persona_files_found and on_disk_personas != persona_files_found:
        errors.append("session-pack persona_file set does not match current p6 personas/*.md set")

    print("\nPhase 7/8: Verify Roleplay Pack")
    print("─" * 50)
    print(f"  Pack file      : {PACK.relative_to(ROOT)}")
    print(f"  Personas found : {len(personas)}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            fail(e)
        print("\nStatus: FAIL")
        raise SystemExit(1)

    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
