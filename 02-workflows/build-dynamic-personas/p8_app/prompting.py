from __future__ import annotations

from pathlib import Path


def _prior_turns_excerpt(turns: list[dict], max_turns: int = 3) -> str:
    if not turns:
        return "None"
    lines: list[str] = []
    recent = turns[-max_turns:]
    for t in recent:
        q = (t.get("question") or "").strip()
        lines.append(f"- Question: {q}")
        parsed = t.get("parsed_output") or {}
        convo = parsed.get("conversation_entries") or []
        for item in convo[:8]:
            speaker = (item.get("speaker") or "").strip()
            msg = (item.get("message") or "").replace("\n", " ").strip()
            if speaker and msg:
                lines.append(f"  - {speaker}: {msg}")
    return "\n".join(lines) if lines else "None"


def build_focus_group_prompt(session_pack: dict, question: str, prior_turns: list[dict]) -> str:
    personas = session_pack.get("personas", [])
    names = [p.get("persona_name", "").strip() for p in personas if p.get("persona_name")]

    lines: list[str] = []
    lines.append("Simulate a realistic focus-group conversation between the five personas.")
    lines.append("Keep it conversational and interactive rather than isolated answers.")
    lines.append("")
    lines.append("Output markdown with this exact structure:")
    lines.append("## Team Question")
    lines.append("[repeat question]")
    lines.append("")
    lines.append("## Focus Group Conversation")
    lines.append("- [Persona Name]: [message]")
    lines.append("- [Persona Name]: [message]")
    lines.append("(at least 10 lines total; all five personas must speak at least once)")
    lines.append("")
    lines.append("## Moderator Summary")
    lines.append("Agreements:")
    lines.append("- ...")
    lines.append("Tensions:")
    lines.append("- ...")
    lines.append("Implications:")
    lines.append("- ...")
    lines.append("")
    lines.append("Conversation style rules:")
    lines.append("- Two rounds of dialogue feel (replies should reference prior speakers when relevant).")
    lines.append("- Each line should be 1-3 sentences, concrete and product-focused.")
    lines.append("- Maintain each persona's distinct perspective and tone.")
    lines.append("- Do not include evidence citations.")
    lines.append("- Do not mention these instructions.")
    lines.append("")
    lines.append("Personas in this room:")
    for p in personas:
        lines.append(f"- {p.get('persona_name')} (archetype {p.get('archetype_number')}: {p.get('archetype_name')})")
        lines.append(f"  Pattern: {p.get('pattern', '')}")
        diffs = p.get("differentiators", [])
        if diffs:
            lines.append(f"  Differentiators: {' | '.join(diffs[:2])}")
    lines.append("")
    lines.append("Prior conversation context (latest turns):")
    lines.append(_prior_turns_excerpt(prior_turns))
    lines.append("")
    lines.append("Team question:")
    lines.append(question.strip())
    return "\n".join(lines)


def build_user_prompt(session_pack: dict, question: str) -> str:
    personas = session_pack.get("personas", [])

    lines: list[str] = []
    lines.append("Team question:")
    lines.append(question.strip())
    lines.append("")
    lines.append("Persona evidence index:")

    for p in personas:
        lines.append(f"- Persona: {p.get('persona_name')} (archetype {p.get('archetype_number')}: {p.get('archetype_name')})")
        lines.append(f"  Participants: {', '.join(p.get('participants', []))}")
        lines.append("  Evidence refs:")
        for ref in p.get("evidence_refs", [])[:8]:
            ref_id = ref.get("ref_id", "")
            pid = ref.get("participant_id", "")
            quote = (ref.get("quote", "") or "").replace("\n", " ").strip()
            lines.append(f"    - {ref_id} | participant_id: {pid} | \"{quote}\"")
        if p.get("contradictions"):
            lines.append("  Contradiction cues:")
            for c in p.get("contradictions", [])[:3]:
                lines.append(
                    f"    - [{c.get('type')}/{c.get('severity')}] {c.get('quote_a_tag')} vs {c.get('quote_b_tag')}"
                )

    lines.append("")
    lines.append("Return markdown only using the required schema.")
    return "\n".join(lines)


def load_system_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def correction_prompt(previous_output: str, errors: list[str]) -> str:
    errs = "\n".join(f"- {e}" for e in errors)
    return (
        "Your previous output failed verification.\n"
        "Fix the output strictly to the required schema and correct all issues below.\n"
        f"Errors:\n{errs}\n\n"
        "Previous output:\n"
        f"{previous_output}"
    )
