#!/usr/bin/env python3
"""
Phase 6: Verify Persona Diversity
Checks set-level diversity across the five persona files.

Usage:
    python3 02-workflows/build-dynamic-personas/verify-persona-diversity.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import re
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P6_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p6-create-personas"
PERSONAS_DIR = P6_DIR / "personas"
INPUTS_DIR = P6_DIR / "persona-inputs"

AGE_PATTERNS = [r"\b2[5-9]\b", r"\b3\d\b", r"\b4\d\b", r"\b5\d\b", r"\b6\d\b", r"\b60\+\b"]
GENDER_TERMS = {"woman", "man", "female", "male", "non-binary", "nonbinary"}
PERSONALITY_TERMS = {
    "confident",
    "cautious",
    "tech-savvy",
    "tech reluctant",
    "analytical",
    "pragmatic",
    "skeptical",
    "optimistic",
}
SEVERITY_TERMS = {"frustrated", "struggle", "painful", "blocked", "satisfied", "comfortable", "mixed"}
ATTITUDE_TERMS = {"advocate", "critic", "neutral", "skeptical", "enthusiastic"}


def collect_signals(text: str) -> dict[str, set[str]]:
    lower = text.lower()
    age_hits = set()
    for pat in AGE_PATTERNS:
        if re.search(pat, lower):
            age_hits.add(pat)
    return {
        "age": age_hits,
        "gender": {t for t in GENDER_TERMS if t in lower},
        "personality": {t for t in PERSONALITY_TERMS if t in lower},
        "severity": {t for t in SEVERITY_TERMS if t in lower},
        "attitude": {t for t in ATTITUDE_TERMS if t in lower},
    }


def load_expected_persona_files() -> tuple[list[Path], list[str]]:
    errors = []
    files = []
    if not INPUTS_DIR.exists():
        return files, [f"Missing persona-inputs dir: {INPUTS_DIR.relative_to(ROOT)}"]

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
        out = ROOT / output_file
        if out.suffix != ".md" or PERSONAS_DIR not in out.parents:
            errors.append(f"{pack.name}: output_file must be a .md under {PERSONAS_DIR.relative_to(ROOT)}")
            continue
        files.append(out)

    if len({p.name for p in files}) != len(files):
        errors.append("Persona output_file names must be unique across archetypes")
    return files, errors


def main():
    files, errors = load_expected_persona_files()
    if not PERSONAS_DIR.exists():
        print(f"FAIL  Missing personas dir: {PERSONAS_DIR.relative_to(ROOT)}")
        print("\nStatus: FAIL")
        sys.exit(1)

    files = sorted(files)
    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        print("\nStatus: FAIL")
        sys.exit(1)

    if len(files) != 5:
        print(f"FAIL  Expected 5 persona files, found {len(files)}")
        print("\nStatus: FAIL")
        sys.exit(1)

    missing = [str(p.relative_to(ROOT)) for p in files if not p.exists()]
    if missing:
        for p in missing:
            print(f"FAIL  Missing persona file: {p}")
        print("\nStatus: FAIL")
        sys.exit(1)

    aggregate = {
        "age": set(),
        "gender": set(),
        "personality": set(),
        "severity": set(),
        "attitude": set(),
    }

    for path in files:
        text = path.read_text(encoding="utf-8")
        s = collect_signals(text)
        for k in aggregate:
            aggregate[k].update(s[k])

    # Hard diversity checks: must have minimum spread.
    if len(aggregate["age"]) < 2:
        errors.append("Age-range diversity was insufficient (need at least 2 distinct age signals)")
    if len(aggregate["gender"]) < 2:
        errors.append("Gender diversity was insufficient (need at least 2 distinct gender signals)")
    if len(aggregate["personality"]) < 3:
        errors.append("Personality diversity was insufficient (need at least 3 distinct personality signals)")
    if len(aggregate["severity"]) < 3:
        errors.append("Pain-point severity diversity was insufficient (need at least 3 distinct severity signals)")
    if len(aggregate["attitude"]) < 3:
        errors.append("Platform-attitude diversity was insufficient (need at least 3 distinct attitude signals)")

    print("\nPhase 6: Verify Persona Diversity")
    print(f"{'─' * 50}")
    print(f"  Personas dir        : {PERSONAS_DIR.relative_to(ROOT)}")
    print(f"  Age signals         : {len(aggregate['age'])}")
    print(f"  Gender signals      : {len(aggregate['gender'])}")
    print(f"  Personality signals : {len(aggregate['personality'])}")
    print(f"  Severity signals    : {len(aggregate['severity'])}")
    print(f"  Attitude signals    : {len(aggregate['attitude'])}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print("\nStatus: FAIL")
        sys.exit(1)

    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
