#!/usr/bin/env python3
"""
Phase 4: Consolidate Quote Tags
Reads quote rows plus a tag mapping and writes consolidated quote/tag artifacts.

Usage:
    python3 02-workflows/build-dynamic-personas/run-tag-consolidation.py

Exit codes:
    0 — PASS
    1 — FAIL (missing inputs or mapping/schema errors)
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
QUOTES_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p1-quote-extraction" / "quotes.csv"
PHASE4_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p4-consolidate-tags"
MAPPING_PATH = PHASE4_DIR / "tag-mapping.json"
CONSOLIDATED_QUOTES_PATH = PHASE4_DIR / "consolidated-quotes.csv"
CROSSWALK_PATH = PHASE4_DIR / "tag-crosswalk.csv"
REPORT_PATH = PHASE4_DIR / "tag-consolidation-report.md"

QUOTE_COLUMNS = [
    "participant_id",
    "transcript_id",
    "question_ref",
    "tag",
    "severity",
    "sentiment",
    "quote",
    "source_line_start",
    "source_line_end",
]

CROSSWALK_COLUMNS = ["original_tag", "consolidated_tag", "original_count", "notes"]
CONSOLIDATED_COUNT_MIN = 35
CONSOLIDATED_COUNT_MAX = 45
MAX_UNCHANGED_TAG_RATIO = 0.35
MAX_CATCH_ALL_ROW_RATIO = 0.15
MAX_DOMINANT_CONSOLIDATED_ROW_RATIO = 0.20
# Keep this conservative to avoid false positives on legitimate tags.
CATCH_ALL_MARKERS = ("general", "misc", "miscellaneous", "various", "catch-all")


def load_quotes() -> tuple[list[dict], list[str]]:
    errors = []
    rows = []

    if not QUOTES_PATH.exists():
        errors.append(f"quotes.csv not found: {QUOTES_PATH.relative_to(ROOT)}")
        return rows, errors

    with open(QUOTES_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if list(reader.fieldnames or []) != QUOTE_COLUMNS:
            errors.append(
                f"quotes.csv columns were {reader.fieldnames}; expected {QUOTE_COLUMNS}"
            )
            return rows, errors
        rows = list(reader)

    if not rows:
        errors.append("quotes.csv contained no rows")

    return rows, errors


def load_mapping() -> tuple[dict[str, str], list[str], list[str]]:
    """Returns (mapping, warnings, errors)."""
    warnings = []
    errors = []
    mapping = {}

    if not MAPPING_PATH.exists():
        errors.append(
            f"Tag mapping file not found: {MAPPING_PATH.relative_to(ROOT)}. "
            f"Run tag-consolidator first."
        )
        return mapping, warnings, errors

    try:
        with open(MAPPING_PATH, encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        errors.append(f"Could not read mapping JSON: {e}")
        return mapping, warnings, errors

    entries = None
    if isinstance(payload, dict) and isinstance(payload.get("mappings"), list):
        entries = payload["mappings"]
    elif isinstance(payload, dict):
        # Backward-compatible shorthand: {original_tag: consolidated_tag}
        entries = [
            {"original_tag": k, "consolidated_tag": v}
            for k, v in payload.items()
            if isinstance(k, str)
        ]
        warnings.append("Using shorthand mapping format; preferred format is {'mappings': [...]} ")
    else:
        errors.append("Mapping JSON must be an object with a 'mappings' list")
        return mapping, warnings, errors

    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            errors.append(f"Mapping entry {idx} is not an object")
            continue
        original = str(entry.get("original_tag", "")).strip()
        consolidated = str(entry.get("consolidated_tag", "")).strip()
        if not original:
            errors.append(f"Mapping entry {idx} missing original_tag")
            continue
        if not consolidated:
            errors.append(f"Mapping entry {idx} missing consolidated_tag for '{original}'")
            continue
        if original in mapping and mapping[original] != consolidated:
            errors.append(
                f"Conflicting mapping for '{original}': '{mapping[original]}' vs '{consolidated}'"
            )
            continue
        mapping[original] = consolidated

    return mapping, warnings, errors


def semantic_quality_errors(quotes: list[dict], mapping: dict[str, str]) -> list[str]:
    errors = []

    original_tags = {row["tag"] for row in quotes}
    total_rows = len(quotes)
    if not original_tags or total_rows == 0:
        return errors

    unchanged_count = sum(
        1 for tag in original_tags if mapping.get(tag, "").strip().lower() == tag.strip().lower()
    )
    unchanged_ratio = unchanged_count / len(original_tags)
    if unchanged_ratio > MAX_UNCHANGED_TAG_RATIO:
        errors.append(
            f"Unchanged-tag ratio was {unchanged_ratio:.1%} ({unchanged_count}/{len(original_tags)}), "
            f"above limit {MAX_UNCHANGED_TAG_RATIO:.0%}. Mapping appears too pass-through."
        )

    consolidated_row_counts = Counter(mapping[row["tag"]] for row in quotes)
    dominant_tag, dominant_count = consolidated_row_counts.most_common(1)[0]
    dominant_ratio = dominant_count / total_rows
    if dominant_ratio > MAX_DOMINANT_CONSOLIDATED_ROW_RATIO:
        errors.append(
            f"Dominant consolidated tag '{dominant_tag}' covered {dominant_ratio:.1%} of rows, "
            f"above limit {MAX_DOMINANT_CONSOLIDATED_ROW_RATIO:.0%}. Clusters may be over-broad."
        )

    catch_all_rows = 0
    for consolidated_tag, count in consolidated_row_counts.items():
        name = consolidated_tag.strip().lower()
        if any(marker in name for marker in CATCH_ALL_MARKERS):
            catch_all_rows += count
    catch_all_ratio = catch_all_rows / total_rows
    if catch_all_ratio > MAX_CATCH_ALL_ROW_RATIO:
        errors.append(
            f"Catch-all style consolidated tags covered {catch_all_ratio:.1%} of rows, "
            f"above limit {MAX_CATCH_ALL_ROW_RATIO:.0%}."
        )

    return errors


def write_outputs(quotes: list[dict], mapping: dict[str, str]) -> tuple[list[str], list[str]]:
    warnings = []
    errors = []

    original_counts = Counter(row["tag"] for row in quotes)
    original_tags = set(original_counts)
    mapped_tags = set(mapping)

    missing_mappings = sorted(original_tags - mapped_tags)
    extra_mappings = sorted(mapped_tags - original_tags)

    if missing_mappings:
        errors.append(
            f"{len(missing_mappings)} original tag(s) missing from mapping: "
            + ", ".join(missing_mappings[:20])
            + ("..." if len(missing_mappings) > 20 else "")
        )

    if extra_mappings:
        warnings.append(
            f"{len(extra_mappings)} mapping tag(s) not present in quotes.csv: "
            + ", ".join(extra_mappings[:20])
            + ("..." if len(extra_mappings) > 20 else "")
        )

    if errors:
        return warnings, errors

    PHASE4_DIR.mkdir(parents=True, exist_ok=True)

    consolidated_rows = []
    consolidated_counts = Counter()
    reverse_mapping = {}
    for row in quotes:
        consolidated_tag = mapping[row["tag"]]
        consolidated_counts[consolidated_tag] += 1
        reverse_mapping.setdefault(consolidated_tag, set()).add(row["tag"])
        consolidated_rows.append({**row, "consolidated_tag": consolidated_tag})

    # Enforce semantic quality first; cardinality checks run only after semantics pass.
    errors.extend(semantic_quality_errors(quotes, mapping))

    consolidated_unique = len(consolidated_counts)
    if not errors and (
        consolidated_unique < CONSOLIDATED_COUNT_MIN
        or consolidated_unique > CONSOLIDATED_COUNT_MAX
    ):
        direction = "merge near-semantic neighbors" if consolidated_unique > CONSOLIDATED_COUNT_MAX else "split overloaded consolidated tags"
        errors.append(
            f"Consolidated unique tag count was {consolidated_unique}; expected "
            f"{CONSOLIDATED_COUNT_MIN}-{CONSOLIDATED_COUNT_MAX}. Re-run tag-consolidator and {direction}."
        )

    if errors:
        return warnings, errors

    with open(CONSOLIDATED_QUOTES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[*QUOTE_COLUMNS, "consolidated_tag"])
        writer.writeheader()
        writer.writerows(consolidated_rows)

    crosswalk_rows = [
        {
            "original_tag": original,
            "consolidated_tag": mapping[original],
            "original_count": str(original_counts[original]),
            "notes": "",
        }
        for original in sorted(original_tags)
    ]
    with open(CROSSWALK_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CROSSWALK_COLUMNS)
        writer.writeheader()
        writer.writerows(crosswalk_rows)

    report_lines = [
        "# Phase 4 Tag Consolidation Report",
        "",
        f"- Source file: `{QUOTES_PATH.relative_to(ROOT)}`",
        f"- Mapping file: `{MAPPING_PATH.relative_to(ROOT)}`",
        f"- Output file: `{CONSOLIDATED_QUOTES_PATH.relative_to(ROOT)}`",
        f"- Crosswalk file: `{CROSSWALK_PATH.relative_to(ROOT)}`",
        "",
        "## Summary",
        "",
        f"- Total quote rows: {len(quotes)}",
        f"- Original unique tags: {len(original_tags)}",
        f"- Consolidated unique tags: {consolidated_unique}",
        f"- Semantic quality checks: PASS",
        "",
        "## Consolidated Tag Distribution",
        "",
        "| consolidated_tag | quote_count |",
        "|---|---:|",
    ]
    for consolidated_tag, count in sorted(
        consolidated_counts.items(), key=lambda x: (-x[1], x[0].lower())
    ):
        report_lines.append(f"| {consolidated_tag} | {count} |")

    report_lines.extend(
        [
            "",
            "## Cluster Audit",
            "",
            "| consolidated_tag | mapped_original_tags | sample_original_tags |",
            "|---|---:|---|",
        ]
    )
    for consolidated_tag in sorted(reverse_mapping, key=lambda x: x.lower()):
        originals = sorted(reverse_mapping[consolidated_tag])
        sample = ", ".join(originals[:2])
        if len(originals) > 2:
            sample += ", ..."
        report_lines.append(
            f"| {consolidated_tag} | {len(originals)} | {sample} |"
        )

    if warnings:
        report_lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            report_lines.append(f"- {warning}")

    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return warnings, errors


def main():
    warnings = []
    errors = []

    quotes, quote_errors = load_quotes()
    errors.extend(quote_errors)

    mapping, mapping_warnings, mapping_errors = load_mapping()
    warnings.extend(mapping_warnings)
    errors.extend(mapping_errors)

    if not errors:
        write_warnings, write_errors = write_outputs(quotes, mapping)
        warnings.extend(write_warnings)
        errors.extend(write_errors)

    print("\nPhase 4: Consolidate Quote Tags")
    print(f"{'─' * 50}")
    print(f"  Source quotes         : {QUOTES_PATH.relative_to(ROOT)}")
    print(f"  Mapping file          : {MAPPING_PATH.relative_to(ROOT)}")
    print(f"  Output consolidated   : {CONSOLIDATED_QUOTES_PATH.relative_to(ROOT)}")
    print(f"  Output crosswalk      : {CROSSWALK_PATH.relative_to(ROOT)}")
    print(f"  Report                : {REPORT_PATH.relative_to(ROOT)}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  WARN  {warning}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for err in errors:
            print(f"  FAIL  {err}")
        print("\nStatus: FAIL")
        sys.exit(1)

    print(f"\nStatus: {'PASS' if not warnings else 'PASS (with warnings)'}")


if __name__ == "__main__":
    main()
