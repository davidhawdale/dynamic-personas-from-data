#!/usr/bin/env python3
"""
Phase 7/8: Verify Roleplay Response

Usage:
  python3 02-workflows/build-dynamic-personas/verify-roleplay-response.py --file <response.md>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACK = ROOT / "04-process" / "build-dynamic-personas" / "p7-role-play" / "session-pack.json"

H_TEAM = "## Team Question"
H_RESP = "## Persona Responses"
H_SYN = "## Moderator Synthesis"
H_EVID = "## Evidence Index Used"

CONF_RE = re.compile(r"\bconfidence:\s*(High|Medium|Low)\b", re.IGNORECASE)
PID_RE = re.compile(r"\bparticipant_id:\s*([A-Za-z0-9]+)\b")
REF_RE = re.compile(r"\bquote_ref:\s*([A-Za-z0-9]+)\b")


def split_sections(text: str) -> dict[str, str]:
    markers = [H_TEAM, H_RESP, H_SYN, H_EVID]
    out: dict[str, str] = {}
    for i, marker in enumerate(markers):
        start = text.find(marker)
        if start < 0:
            continue
        body_start = start + len(marker)
        end = len(text)
        for j in range(i + 1, len(markers)):
            nxt = text.find(markers[j], body_start)
            if nxt >= 0:
                end = min(end, nxt)
        out[marker] = text[body_start:end].strip()
    return out


def parse_persona_blocks(responses_body: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    chunks = re.split(r"(?m)^###\s+", responses_body)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        name = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        blocks[name] = body
    return blocks


def verify_response_text(text: str, expected_names: list[str]) -> list[str]:
    errors: list[str] = []
    sections = split_sections(text)

    for h in [H_TEAM, H_RESP, H_SYN, H_EVID]:
        if h not in sections:
            errors.append(f"Missing required heading: {h}")

    if errors:
        return errors

    persona_blocks = parse_persona_blocks(sections[H_RESP])

    if len(persona_blocks) != 5:
        errors.append(f"Expected exactly 5 persona response blocks; found {len(persona_blocks)}")

    missing = sorted(set(expected_names) - set(persona_blocks.keys()))
    extra = sorted(set(persona_blocks.keys()) - set(expected_names))
    if missing:
        errors.append("Missing persona blocks: " + ", ".join(missing))
    if extra:
        errors.append("Unexpected persona blocks: " + ", ".join(extra))

    for name in expected_names:
        body = persona_blocks.get(name, "")
        if not body:
            continue
        if "Response:" not in body:
            errors.append(f"{name}: missing 'Response:' line")
        if "Evidence:" not in body:
            errors.append(f"{name}: missing 'Evidence:' block")
        if not PID_RE.search(body):
            errors.append(f"{name}: missing participant_id evidence")
        if not REF_RE.search(body):
            errors.append(f"{name}: missing quote_ref evidence")
        if not CONF_RE.search(body):
            errors.append(f"{name}: missing confidence marker")

    syn = sections[H_SYN]
    for label in ["Agreements:", "Disagreements:", "Implications:", "Open Questions:"]:
        if label not in syn:
            errors.append(f"Moderator synthesis missing '{label}'")

    evid = sections[H_EVID]
    if "participant_id:" not in evid:
        errors.append("Evidence index missing participant_id entries")

    return errors


def expected_persona_names_from_pack(pack_path: Path) -> list[str]:
    import json

    data = json.loads(pack_path.read_text(encoding="utf-8"))
    personas = data.get("personas", [])
    return [p.get("persona_name", "").strip() for p in personas if p.get("persona_name")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to markdown response file")
    parser.add_argument("--pack", default=str(DEFAULT_PACK), help="Path to session-pack.json")
    args = parser.parse_args()

    response_file = ROOT / args.file if not Path(args.file).is_absolute() else Path(args.file)
    pack_file = ROOT / args.pack if not Path(args.pack).is_absolute() else Path(args.pack)

    errs: list[str] = []
    if not response_file.exists():
        errs.append(f"Missing response file: {response_file}")
    if not pack_file.exists():
        errs.append(f"Missing pack file: {pack_file}")

    if errs:
        for e in errs:
            print(f"FAIL  {e}")
        print("\nStatus: FAIL")
        raise SystemExit(1)

    expected_names = expected_persona_names_from_pack(pack_file)
    text = response_file.read_text(encoding="utf-8")
    errors = verify_response_text(text, expected_names)

    print("\nPhase 7/8: Verify Roleplay Response")
    print("─" * 50)
    print(f"  Response file  : {response_file.relative_to(ROOT)}")
    print(f"  Personas expect: {len(expected_names)}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print("\nStatus: FAIL")
        raise SystemExit(1)

    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
