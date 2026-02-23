#!/usr/bin/env python3
"""
Phase 1: Validate Quotes
Checks that each extracted quote in quotes.csv appears verbatim in its source transcript.
Handles ellipsis (...) as per valid-quote-rules: each segment must appear in order.

Usage:
    python3 02-workflows/build-dynamic-personas/validate-quotes.py

Exit codes:
    0 — all quotes PASS
    1 — one or more quotes FAIL
"""

import csv
import json
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p0-prepare" / "manifest.json"
QUOTES_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p1-quote-extraction" / "quotes.csv"
REPORT_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p1-quote-extraction" / "quote-validation-report.csv"

REPORT_COLUMNS = [
    "participant_id",
    "transcript_id",
    "question_ref",
    "tag",
    "status",
    "reason",
    "quote",
    "transcript_match",
    "transcript_lines",
]


# ── Text normalisation ───────────────────────────────────────────────────────────

def norm_quotes(text: str) -> str:
    """Normalise Unicode curly quotes/apostrophes to ASCII equivalents."""
    return (
        text
        .replace("\u2018", "'")   # LEFT SINGLE QUOTATION MARK
        .replace("\u2019", "'")   # RIGHT SINGLE QUOTATION MARK
        .replace("\u201c", '"')   # LEFT DOUBLE QUOTATION MARK
        .replace("\u201d", '"')   # RIGHT DOUBLE QUOTATION MARK
        .replace("\u2032", "'")   # PRIME (sometimes used as apostrophe)
    )


# ── Transcript loading ───────────────────────────────────────────────────────────

def load_transcript(path: Path) -> tuple[str, list[int]]:
    """
    Read a transcript and return (norm_text, char_to_line).

    norm_text      — full text with all whitespace collapsed to single spaces.
    char_to_line   — parallel list: char_to_line[i] is the 1-based original line
                     number for position i in norm_text.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    parts: list[str] = []
    char_to_line: list[int] = []

    for lineno, line in enumerate(lines, start=1):
        norm = re.sub(r"\s+", " ", norm_quotes(line)).strip()
        if not norm:
            continue
        if parts:
            # separator space between parts — map to this (next) line
            char_to_line.append(lineno)
        for _ in norm:
            char_to_line.append(lineno)
        parts.append(norm)

    norm_text = " ".join(parts)
    return norm_text, char_to_line


def _get_lines(idx: int, length: int, char_to_line: list[int]) -> str:
    """Return the line range (e.g. '12' or '12-14') for a match at [idx, idx+length)."""
    start = char_to_line[idx]
    end = char_to_line[idx + length - 1]
    return str(start) if start == end else f"{start}-{end}"


# ── Quote matching ───────────────────────────────────────────────────────────────

def match_quote(
    norm_transcript: str,
    char_to_line: list[int],
    quote: str,
) -> tuple[str, str, str, str]:
    """
    Try to find `quote` in `norm_transcript`.

    Returns (status, reason, transcript_match, transcript_lines).
      status            — 'PASS' or 'FAIL'
      reason            — empty on PASS; short description on FAIL
      transcript_match  — verbatim text found in the transcript (segments joined
                          with ' ... ' for ellipsis quotes); empty on FAIL
      transcript_lines  — original line number(s) where match was found; empty on FAIL
    """
    norm_quote = re.sub(r"\s+", " ", norm_quotes(quote)).strip()
    trans_lower = norm_transcript.lower()

    if "..." not in norm_quote:
        # Simple case: exact substring (case-insensitive)
        q_lower = norm_quote.lower()
        idx = trans_lower.find(q_lower)
        if idx < 0:
            return "FAIL", "Quote not found in transcript", "", ""
        matched = norm_transcript[idx : idx + len(norm_quote)]
        lines = _get_lines(idx, len(norm_quote), char_to_line)
        return "PASS", "", matched, lines

    # Ellipsis case: split on '...' and verify each segment appears in order
    segments = [s.strip() for s in norm_quote.split("...") if s.strip()]
    if not segments:
        return "FAIL", "Quote contains only ellipses", "", ""

    matched_segs: list[str] = []
    seg_lines: list[str] = []
    search_from = 0

    for seg in segments:
        seg_lower = seg.lower()
        idx = trans_lower.find(seg_lower, search_from)
        if idx < 0:
            short = seg[:60] + ("..." if len(seg) > 60 else "")
            return "FAIL", f'Segment not found: "{short}"', "", ""
        matched_segs.append(norm_transcript[idx : idx + len(seg)])
        seg_lines.append(_get_lines(idx, len(seg), char_to_line))
        search_from = idx + len(seg)

    return "PASS", "", " ... ".join(matched_segs), ", ".join(seg_lines)


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    # ── Check inputs ─────────────────────────────────────────────────────────────

    errors = []
    if not MANIFEST_PATH.exists():
        errors.append(f"Manifest not found: {MANIFEST_PATH.relative_to(ROOT)}")
    if not QUOTES_PATH.exists():
        errors.append(f"quotes.csv not found: {QUOTES_PATH.relative_to(ROOT)}")
    if errors:
        for e in errors:
            print(f"FAIL  {e}")
        sys.exit(1)

    # ── Load manifest ─────────────────────────────────────────────────────────────

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    pid_to_path: dict[str, Path] = {
        t["participant_id"]: ROOT / t["path"]
        for t in manifest["transcripts"]
    }

    # ── Load quotes ───────────────────────────────────────────────────────────────

    with open(QUOTES_PATH, newline="", encoding="utf-8") as f:
        quotes = list(csv.DictReader(f))

    # ── Validate each quote ───────────────────────────────────────────────────────

    transcript_cache: dict[str, tuple[str, list[int]]] = {}
    results: list[dict] = []
    n_pass = 0
    n_fail = 0

    for row in quotes:
        pid = row["participant_id"]
        base = {
            "participant_id": pid,
            "transcript_id": row["transcript_id"],
            "question_ref": row["question_ref"],
            "tag": row["tag"],
            "quote": row["quote"],
        }

        if pid not in pid_to_path:
            results.append({
                **base,
                "status": "FAIL",
                "reason": f"participant_id '{pid}' not in manifest",
                "transcript_match": "",
                "transcript_lines": "",
            })
            n_fail += 1
            continue

        if pid not in transcript_cache:
            transcript_cache[pid] = load_transcript(pid_to_path[pid])

        norm_t, c2l = transcript_cache[pid]
        status, reason, t_match, t_lines = match_quote(norm_t, c2l, row["quote"])

        results.append({
            **base,
            "status": status,
            "reason": reason,
            "transcript_match": t_match,
            "transcript_lines": t_lines,
        })
        if status == "PASS":
            n_pass += 1
        else:
            n_fail += 1

    # ── Write report ──────────────────────────────────────────────────────────────

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(results)

    # ── Print summary ─────────────────────────────────────────────────────────────

    print(f"\nPhase 1: Validate Quotes")
    print(f"{'─' * 50}")
    print(f"  Quotes checked : {len(quotes)}")
    print(f"  PASS           : {n_pass}")
    print(f"  FAIL           : {n_fail}")
    print(f"  Report         : {REPORT_PATH.relative_to(ROOT)}")

    if n_fail:
        print(f"\nFailed quotes:")
        for r in results:
            if r["status"] == "FAIL":
                q_preview = r["quote"][:80] + ("..." if len(r["quote"]) > 80 else "")
                print(f"  FAIL  [{r['participant_id']}] {r['question_ref']} / {r['tag']}")
                print(f"        Reason : {r['reason']}")
                print(f"        Quote  : {q_preview}")

    print(f"\nStatus: {'PASS' if not n_fail else 'FAIL'}")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
