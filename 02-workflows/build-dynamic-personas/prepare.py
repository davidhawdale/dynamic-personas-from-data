#!/usr/bin/env python3
"""
Phase 0: Prepare
Scans 03-inputs/interview-transcripts/, validates files, and writes a manifest
to 04-process/build-dynamic-personas/manifest.json.

Usage:
    python 02-workflows/build-dynamic-personas/prepare.py

Exit codes:
    0 — PASS
    1 — FAIL (missing inputs or critical error)
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS_DIR = ROOT / "03-inputs" / "interview-transcripts"
RESEARCH_BRIEF = ROOT / "03-inputs" / "research-brief.md"
PROCESS_DIR = ROOT / "04-process" / "build-dynamic-personas"
MANIFEST_PATH = PROCESS_DIR / "p0-prepare" / "manifest.json"

EXPECTED_COUNT = 53

# ── Filename patterns ──────────────────────────────────────────────────────────
# en_participant_0001.txt
STANDARD_PATTERN = re.compile(r"^en_participant_(\d{4})\.txt$")
# en_translated_from_fr_participant_0001.txt
TRANSLATED_PATTERN = re.compile(r"^en_translated_from_([a-z]{2})_participant_(\d{4})\.txt$")


def parse_filename(filename: str) -> Optional[dict]:
    """Return transcript metadata dict, or None if filename doesn't match."""
    m = STANDARD_PATTERN.match(filename)
    if m:
        seq = str(int(m.group(1)))  # strip leading zeros → "49"
        return {
            "id": filename[:-4],
            "participant_id": seq,
            "language": "en",
            "source_language": None,
            "translated": False,
        }
    m = TRANSLATED_PATTERN.match(filename)
    if m:
        lang = m.group(1).upper()   # "pl" → "PL"
        seq = str(int(m.group(2)))  # strip leading zeros → "21"
        return {
            "id": filename[:-4],
            "participant_id": f"{lang}{seq}",
            "language": "en",
            "source_language": m.group(1),
            "translated": True,
        }
    return None


def main():
    warnings = []
    errors = []

    # ── Check inputs exist ─────────────────────────────────────────────────────

    if not TRANSCRIPTS_DIR.exists():
        print(f"FAIL  Transcripts directory not found: {TRANSCRIPTS_DIR}")
        sys.exit(1)

    if not RESEARCH_BRIEF.exists():
        errors.append(f"Research brief not found: {RESEARCH_BRIEF}")

    # ── Scan transcripts ───────────────────────────────────────────────────────

    transcripts = []
    skipped = []

    for path in sorted(TRANSCRIPTS_DIR.glob("*.txt")):
        meta = parse_filename(path.name)
        if meta is None:
            skipped.append(path.name)
            continue
        meta["path"] = str(path.relative_to(ROOT))
        meta["size_bytes"] = path.stat().st_size
        transcripts.append(meta)

    # ── Count checks ───────────────────────────────────────────────────────────

    total_files = len(transcripts)

    if total_files != EXPECTED_COUNT:
        msg = f"Expected {EXPECTED_COUNT} transcripts, found {total_files}"
        if total_files < EXPECTED_COUNT:
            errors.append(msg)
        else:
            warnings.append(msg)

    if skipped:
        warnings.append(f"Skipped {len(skipped)} unrecognised files: {skipped}")

    # ── Check for empty files ──────────────────────────────────────────────────

    empty = [t["id"] for t in transcripts if t["size_bytes"] == 0]
    if empty:
        errors.append(f"Empty transcript files: {empty}")

    # ── Write manifest ─────────────────────────────────────────────────────────

    if not errors:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "transcript_count": total_files,
            "transcripts": transcripts,
            "research_brief_path": str(RESEARCH_BRIEF.relative_to(ROOT)),
            "warnings": warnings,
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    # ── Report ─────────────────────────────────────────────────────────────────

    print(f"\nPhase 0: Prepare")
    print(f"{'─' * 50}")
    print(f"  Transcripts dir : {TRANSCRIPTS_DIR.relative_to(ROOT)}")
    print(f"  Transcripts found: {total_files} (expected {EXPECTED_COUNT})")
    print(f"  Research brief  : {'found' if RESEARCH_BRIEF.exists() else 'MISSING'}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN  {w}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\nStatus: FAIL — manifest not written")
        sys.exit(1)

    print(f"\n  Manifest written: {MANIFEST_PATH.relative_to(ROOT)}")
    print(f"\nStatus: {'PASS' if not warnings else 'PASS (with warnings)'}")


if __name__ == "__main__":
    main()
