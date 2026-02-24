#!/usr/bin/env python3
"""
Phase 7: Prepare Roleplay Pack
Builds deterministic roleplay artifacts from Phase 6 persona outputs.

Usage:
  python3 02-workflows/build-dynamic-personas/prepare-roleplay-pack.py

Exit codes:
  0 PASS
  1 FAIL
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P6_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p6-create-personas"
P6_PERSONA_INPUTS = P6_DIR / "persona-inputs"
P7_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p7-role-play"
P7_SESSIONS = P7_DIR / "sessions"
P4_QUOTES = ROOT / "04-process" / "build-dynamic-personas" / "p4-consolidate-tags" / "consolidated-quotes.csv"
P3_CONTRADICTIONS = ROOT / "04-process" / "build-dynamic-personas" / "p3-check-contradictions" / "contradictions.csv"
PRODUCT_VISION = ROOT / "00-brief" / "product-vision.md"
RESEARCH_BRIEF = ROOT / "03-inputs" / "research-brief.md"

H1_RE = re.compile(r"^#\s+(.+?)\s*$")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def persona_name(path: Path) -> str:
    for line in read_text(path).splitlines():
        m = H1_RE.match(line.strip())
        if m:
            return m.group(1).strip()
    return path.stem.replace("-", " ").title()


def load_persona_input(path: Path) -> dict:
    return json.loads(read_text(path))


def load_quotes_index() -> dict[str, list[dict]]:
    by_participant: dict[str, list[dict]] = {}
    with open(P4_QUOTES, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("participant_id") or "").strip()
            if not pid:
                continue
            by_participant.setdefault(pid, []).append(
                {
                    "tag": (row.get("tag") or "").strip(),
                    "quote": (row.get("quote") or "").strip(),
                    "transcript_id": (row.get("transcript_id") or "").strip(),
                    "consolidated_tag": (row.get("consolidated_tag") or "").strip(),
                }
            )
    return by_participant


def load_contradictions() -> dict[str, list[dict]]:
    by_participant: dict[str, list[dict]] = {}
    with open(P3_CONTRADICTIONS, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("participant_id") or "").strip()
            if not pid:
                continue
            by_participant.setdefault(pid, []).append(
                {
                    "type": (row.get("contradiction_type") or "").strip(),
                    "severity": (row.get("severity") or "").strip(),
                    "quote_a_tag": (row.get("quote_a_tag") or "").strip(),
                    "quote_b_tag": (row.get("quote_b_tag") or "").strip(),
                    "explanation": (row.get("explanation") or "").strip(),
                }
            )
    return by_participant


def compact_text(path: Path, max_chars: int = 1800) -> str:
    text = read_text(path).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n..."


def main() -> None:
    errors: list[str] = []
    for req in [P6_PERSONA_INPUTS, P4_QUOTES, P3_CONTRADICTIONS, PRODUCT_VISION, RESEARCH_BRIEF]:
        if not req.exists():
            errors.append(f"Missing required input: {req.relative_to(ROOT)}")

    input_files = sorted(P6_PERSONA_INPUTS.glob("archetype-*.json")) if P6_PERSONA_INPUTS.exists() else []
    if len(input_files) != 5:
        errors.append(f"Expected 5 persona input packs; found {len(input_files)}")

    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        print("\nStatus: FAIL")
        raise SystemExit(1)

    quote_index = load_quotes_index()
    contradictions = load_contradictions()

    personas: list[dict] = []

    for pack_path in input_files:
        pack = load_persona_input(pack_path)
        persona_md = ROOT / pack["output_file"]
        if not persona_md.exists():
            print(f"FAIL  Missing persona file: {pack['output_file']}")
            print("\nStatus: FAIL")
            raise SystemExit(1)

        name = persona_name(persona_md)
        participants = pack.get("participants", [])

        evidence_refs: list[dict] = []
        ref_count = 1

        # Seed refs from archetype evidence quotes.
        for q in pack.get("evidence_quotes", []):
            pid = (q.get("participant_id") or "").strip()
            txt = (q.get("quote") or "").strip()
            if not pid or not txt:
                continue
            evidence_refs.append(
                {
                    "ref_id": f"A{pack['archetype_number']}E{ref_count}",
                    "participant_id": pid,
                    "quote": txt,
                    "source": "archetype_evidence",
                }
            )
            ref_count += 1

        # Add up to 2 consolidated quote anchors from assigned participants.
        for pid in participants:
            for row in quote_index.get(pid, [])[:1]:
                if row["quote"]:
                    evidence_refs.append(
                        {
                            "ref_id": f"A{pack['archetype_number']}E{ref_count}",
                            "participant_id": pid,
                            "quote": row["quote"],
                            "tag": row["tag"],
                            "consolidated_tag": row["consolidated_tag"],
                            "source": "consolidated_quotes",
                        }
                    )
                    ref_count += 1
            if ref_count > 5:
                break

        persona_contras: list[dict] = []
        for pid in participants:
            persona_contras.extend(contradictions.get(pid, []))

        personas.append(
            {
                "archetype_number": pack["archetype_number"],
                "archetype_name": pack["archetype_name"],
                "persona_name": name,
                "persona_slug": persona_md.stem,
                "persona_file": str(persona_md.relative_to(ROOT)),
                "participants": participants,
                "pattern": pack.get("pattern", ""),
                "differentiators": pack.get("differentiators", []),
                "evidence_refs": evidence_refs,
                "contradictions": persona_contras,
                "voice_guardrails": [
                    "Speak as this persona in first person.",
                    "Do not claim certainty beyond evidence; label inferences explicitly.",
                    "Prefer concise practical reactions to product choices.",
                ],
            }
        )

    P7_DIR.mkdir(parents=True, exist_ok=True)
    P7_SESSIONS.mkdir(parents=True, exist_ok=True)

    product_context = compact_text(PRODUCT_VISION)
    research_context = compact_text(RESEARCH_BRIEF)

    pack_payload = {
        "version": "1",
        "workflow": "build-dynamic-personas",
        "phase": "p7-role-play",
        "personas": personas,
        "moderator_policy": {
            "must_include": [
                "agreements",
                "disagreements",
                "implications",
                "open_questions",
            ],
            "grounding": "All concrete claims must cite evidence refs from the index.",
        },
        "context": {
            "product_vision_excerpt": product_context,
            "research_brief_excerpt": research_context,
        },
    }

    session_pack = P7_DIR / "session-pack.json"
    session_pack.write_text(json.dumps(pack_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    panel_prompt = P7_DIR / "panel-system-prompt.md"
    panel_prompt.write_text(
        """# Persona Panel System Prompt

You are running a realistic five-persona focus-group discussion with a neutral moderator.

Rules:
- Maintain distinct persona voices and viewpoints.
- Let personas react to each other (not just isolated monologues).
- Keep responses practical and product-focused.
- Keep each line concise (1-3 sentences).

Required output markdown structure:

## Team Question
[repeat user question]

## Focus Group Conversation
- [Persona Name]: [message]
- [Persona Name]: [message]
- [Persona Name]: [message]
(At least 10 lines total. All five personas must speak at least once.)

## Moderator Summary
Agreements:
- ...
Tensions:
- ...
Implications:
- ...
""",
        encoding="utf-8",
    )

    runbook = P7_DIR / "session-runbook.md"
    runbook.write_text(
        """# Persona Role-Play Runbook

1. Ensure `session-pack.json` and `panel-system-prompt.md` are present.
2. Start the app from Phase 8.
3. Create a session and ask one product question per turn.
4. Review moderator implications and disagreements after each turn.
5. Export sessions for team review.
""",
        encoding="utf-8",
    )

    qtpl = P7_DIR / "question-template.md"
    qtpl.write_text(
        """# Team Question Template

- Product concept / feature:
- Target user context:
- Risk/constraint to stress-test:
- Decision we need from personas:

Question:
""",
        encoding="utf-8",
    )

    print("\nPhase 7: Prepare Roleplay Pack")
    print("─" * 50)
    print(f"  Session pack   : {session_pack.relative_to(ROOT)}")
    print(f"  Panel prompt   : {panel_prompt.relative_to(ROOT)}")
    print(f"  Runbook        : {runbook.relative_to(ROOT)}")
    print(f"  Personas loaded: {len(personas)}")
    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
