#!/usr/bin/env python3
"""
Phase 6: Sync Persona Filenames
Renames persona markdown files to match their H1 title and updates input packs.

Usage:
    python3 02-workflows/build-dynamic-personas/sync-persona-filenames.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P6_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p6-create-personas"
INPUTS_DIR = P6_DIR / "persona-inputs"
PERSONAS_DIR = P6_DIR / "personas"

H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")


def slugify(text: str) -> str:
    value = unicodedata.normalize("NFKD", text)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    value = re.sub(r"-{2,}", "-", value)
    return value or "persona"


def read_h1(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        m = H1_RE.match(line)
        if m:
            return m.group(1).strip()
    return ""


def main():
    errors = []
    if not INPUTS_DIR.exists():
        errors.append(f"Missing persona-inputs dir: {INPUTS_DIR.relative_to(ROOT)}")
    if not PERSONAS_DIR.exists():
        errors.append(f"Missing personas dir: {PERSONAS_DIR.relative_to(ROOT)}")
    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        print("\nStatus: FAIL")
        sys.exit(1)

    renames = []
    for i in range(1, 6):
        pack = INPUTS_DIR / f"archetype-{i}.json"
        if not pack.exists():
            errors.append(f"Missing input pack: {pack.relative_to(ROOT)}")
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

        old_path = ROOT / output_file
        if not old_path.exists():
            fallback = PERSONAS_DIR / f"archetype-{i}.md"
            if fallback.exists():
                old_path = fallback
            else:
                errors.append(f"{pack.name}: output file missing: {output_file}")
                continue

        h1 = read_h1(old_path)
        if not h1:
            errors.append(f"{old_path.relative_to(ROOT)}: missing H1 title")
            continue

        new_name = f"{slugify(h1)}.md"
        new_path = PERSONAS_DIR / new_name
        if new_path != old_path and new_path.exists():
            errors.append(
                f"Name collision: {new_path.relative_to(ROOT)} already exists "
                f"(from H1 '{h1}' in {old_path.name})"
            )
            continue

        renames.append((pack, data, old_path, new_path))

    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        print("\nStatus: FAIL")
        sys.exit(1)

    for pack, data, old_path, new_path in renames:
        if old_path != new_path:
            old_path.rename(new_path)
        data["output_file"] = str(new_path.relative_to(ROOT))
        pack.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\nPhase 6: Sync Persona Filenames")
    print(f"{'─' * 50}")
    print(f"  Inputs dir  : {INPUTS_DIR.relative_to(ROOT)}")
    print(f"  Personas dir: {PERSONAS_DIR.relative_to(ROOT)}")
    print("  Applied:")
    for _, data, _, new_path in renames:
        print(f"  - archetype-{data.get('archetype_number')}: {new_path.name}")
    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
