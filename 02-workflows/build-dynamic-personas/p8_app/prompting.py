from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FOCUS_GROUP_TEMPLATE = ROOT / "10-resources" / "templates" / "roleplay-focus-group-prompt.md"
REQUIRED_PLACEHOLDERS = {
    "{{question}}",
    "{{conversation_depth_rule}}",
    "{{emotional_rule}}",
    "{{persona_blocks}}",
    "{{prior_context}}",
}


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
        for item in convo[:10]:
            speaker = (item.get("speaker") or "").strip()
            msg = (item.get("message") or "").replace("\n", " ").strip()
            if speaker and msg:
                lines.append(f"  - {speaker}: {msg}")
    return "\n".join(lines) if lines else "None"


def _conversation_depth_rule(depth: str) -> str:
    return {
        "brief": "Turn length target: 2-3 sentences per persona line.",
        "standard": "Turn length target: 3-4 sentences per persona line.",
        "deep": "Turn length target: 4-6 sentences per persona line.",
    }.get((depth or "deep").lower(), "Turn length target: 4-6 sentences per persona line.")


def _emotional_rule(expressiveness: str) -> str:
    return {
        "low": "Emotional setting: Keep emotional language light and mostly factual.",
        "medium": "Emotional setting: Blend practical reasoning with moderate emotional expression.",
        "high": "Emotional setting: Be openly expressive about feelings, stakes, and lived frustrations/enthusiasm while staying grounded.",
    }.get(
        (expressiveness or "high").lower(),
        "Emotional setting: Be openly expressive about feelings, stakes, and lived frustrations/enthusiasm while staying grounded.",
    )


def _persona_blocks(session_pack: dict) -> str:
    personas = session_pack.get("personas", [])
    lines: list[str] = []
    for p in personas:
        lines.append(f"- {p.get('persona_name')} (archetype {p.get('archetype_number')}: {p.get('archetype_name')})")
        lines.append(f"  Pattern: {p.get('pattern', '')}")
        diffs = p.get("differentiators", [])
        if diffs:
            lines.append(f"  Differentiators: {' | '.join(diffs[:2])}")
        if p.get("voice_style"):
            lines.append(f"  Voice style: {p.get('voice_style')}")
        if p.get("emotional_profile"):
            lines.append(f"  Emotional profile: {p.get('emotional_profile')}")
        if p.get("reasoning_style"):
            lines.append(f"  Reasoning style: {p.get('reasoning_style')}")
        phrases = p.get("sample_phrases", [])
        if phrases:
            lines.append(f"  Phrase cue: {phrases[0]}")
    return "\n".join(lines)


def _load_focus_group_template() -> str:
    if not FOCUS_GROUP_TEMPLATE.exists():
        raise RuntimeError(f"Prompt template missing: {FOCUS_GROUP_TEMPLATE}")
    text = FOCUS_GROUP_TEMPLATE.read_text(encoding="utf-8")
    missing = [ph for ph in REQUIRED_PLACEHOLDERS if ph not in text]
    if missing:
        raise RuntimeError(
            "Prompt template is missing required placeholders: " + ", ".join(sorted(missing))
        )
    return text


def build_focus_group_prompt(
    session_pack: dict,
    question: str,
    prior_turns: list[dict],
    conversation_depth: str = "deep",
    emotional_expressiveness: str = "high",
) -> str:
    template = _load_focus_group_template()
    rendered = template
    replacements = {
        "{{question}}": question.strip(),
        "{{conversation_depth_rule}}": _conversation_depth_rule(conversation_depth),
        "{{emotional_rule}}": _emotional_rule(emotional_expressiveness),
        "{{persona_blocks}}": _persona_blocks(session_pack),
        "{{prior_context}}": _prior_turns_excerpt(prior_turns),
    }
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    return rendered


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
