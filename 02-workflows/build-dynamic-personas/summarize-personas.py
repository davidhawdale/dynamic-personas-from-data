#!/usr/bin/env python3
"""
Phase 6: Summarize Personas
Prints compact counts for Phase 6 human review gate.

Usage:
    python3 02-workflows/build-dynamic-personas/summarize-personas.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P6_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p6-create-personas"
PERSONAS_DIR = P6_DIR / "personas"
INPUTS_DIR = P6_DIR / "persona-inputs"


def expected_files() -> list[Path]:
    paths = []
    for i in range(1, 6):
        pack = INPUTS_DIR / f"archetype-{i}.json"
        if not pack.exists():
            continue
        try:
            data = json.loads(pack.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out = (data.get("output_file") or "").strip()
        if out:
            paths.append(ROOT / out)
    return sorted(paths)


def main():
    files = expected_files() if PERSONAS_DIR.exists() else []
    print("\nPhase 6: Persona Summary")
    print(f"{'─' * 50}")
    print(f"  Personas dir  : {PERSONAS_DIR.relative_to(ROOT)}")
    print(f"  Persona files : {len(files)}")
    for p in files:
        print(f"  - {p.name}")


if __name__ == "__main__":
    main()
