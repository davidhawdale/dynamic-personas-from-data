#!/usr/bin/env python3
"""
Phase 4: Verify Tag Consolidation
Validates consolidated quote outputs for completeness, integrity, and tag-count bounds.

Usage:
    python3 02-workflows/build-dynamic-personas/verify-tag-consolidation.py

Exit codes:
    0 — PASS
    1 — FAIL
"""

import csv
import sys
from collections import Counter
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]
QUOTES_PATH = ROOT / "04-process" / "build-dynamic-personas" / "p1-quote-extraction" / "quotes.csv"
PHASE4_DIR = ROOT / "04-process" / "build-dynamic-personas" / "p4-consolidate-tags"
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

CONSOLIDATED_COLUMNS = [*QUOTE_COLUMNS, "consolidated_tag"]
CROSSWALK_COLUMNS = ["original_tag", "consolidated_tag", "original_count", "notes"]
CONSOLIDATED_COUNT_MIN = 35
CONSOLIDATED_COUNT_MAX = 45
MAX_UNCHANGED_TAG_RATIO = 0.35
MAX_CATCH_ALL_ROW_RATIO = 0.15
MAX_DOMINANT_CONSOLIDATED_ROW_RATIO = 0.20
# Keep this conservative to avoid false positives on legitimate tags.
CATCH_ALL_MARKERS = ("general", "misc", "miscellaneous", "various", "catch-all")


def load_csv(path: Path, expected_columns: list[str]) -> tuple[list[dict], list[str]]:
    rows = []
    errors = []
    if not path.exists():
        errors.append(f"Missing file: {path.relative_to(ROOT)}")
        return rows, errors
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if list(reader.fieldnames or []) != expected_columns:
                errors.append(
                    f"{path.name} columns were {reader.fieldnames}; expected {expected_columns}"
                )
                return rows, errors
            rows = list(reader)
    except Exception as e:
        errors.append(f"Could not read {path.relative_to(ROOT)}: {e}")
    return rows, errors


def semantic_quality_errors(
    source_rows: list[dict], crosswalk_map: dict[str, str], consolidated_rows: list[dict]
) -> list[str]:
    errors = []
    if not source_rows:
        return errors

    source_tags = {row["tag"] for row in source_rows}
    unchanged_count = sum(
        1 for tag in source_tags if crosswalk_map.get(tag, "").strip().lower() == tag.strip().lower()
    )
    unchanged_ratio = unchanged_count / len(source_tags) if source_tags else 0.0
    if unchanged_ratio > MAX_UNCHANGED_TAG_RATIO:
        errors.append(
            f"Unchanged-tag ratio was {unchanged_ratio:.1%} ({unchanged_count}/{len(source_tags)}), "
            f"above limit {MAX_UNCHANGED_TAG_RATIO:.0%}. Mapping is too pass-through."
        )

    total_rows = len(consolidated_rows)
    consolidated_counts = Counter(
        row["consolidated_tag"].strip()
        for row in consolidated_rows
        if (row["consolidated_tag"] or "").strip()
    )
    if consolidated_counts and total_rows:
        dominant_tag, dominant_count = consolidated_counts.most_common(1)[0]
        dominant_ratio = dominant_count / total_rows
        if dominant_ratio > MAX_DOMINANT_CONSOLIDATED_ROW_RATIO:
            errors.append(
                f"Dominant consolidated tag '{dominant_tag}' covered {dominant_ratio:.1%} of rows, "
                f"above limit {MAX_DOMINANT_CONSOLIDATED_ROW_RATIO:.0%}. Clusters are too broad."
            )

        catch_all_rows = 0
        for consolidated_tag, count in consolidated_counts.items():
            name = consolidated_tag.lower()
            if any(marker in name for marker in CATCH_ALL_MARKERS):
                catch_all_rows += count
        catch_all_ratio = catch_all_rows / total_rows
        if catch_all_ratio > MAX_CATCH_ALL_ROW_RATIO:
            errors.append(
                f"Catch-all style consolidated tags covered {catch_all_ratio:.1%} of rows, "
                f"above limit {MAX_CATCH_ALL_ROW_RATIO:.0%}."
            )

    return errors


def main():
    errors = []
    warnings = []

    source_rows, source_errors = load_csv(QUOTES_PATH, QUOTE_COLUMNS)
    consolidated_rows, consolidated_errors = load_csv(CONSOLIDATED_QUOTES_PATH, CONSOLIDATED_COLUMNS)
    crosswalk_rows, crosswalk_errors = load_csv(CROSSWALK_PATH, CROSSWALK_COLUMNS)
    errors.extend(source_errors + consolidated_errors + crosswalk_errors)

    report_exists = REPORT_PATH.exists()
    if not report_exists:
        warnings.append(f"Missing report file: {REPORT_PATH.relative_to(ROOT)}")

    if not errors:
        if len(source_rows) != len(consolidated_rows):
            errors.append(
                f"Row count mismatch: source={len(source_rows)} consolidated={len(consolidated_rows)}"
            )

        source_tag_counts = Counter(row["tag"] for row in source_rows)
        source_tags = set(source_tag_counts)

        crosswalk_map = {}
        for idx, row in enumerate(crosswalk_rows, start=2):
            original = (row["original_tag"] or "").strip()
            consolidated = (row["consolidated_tag"] or "").strip()
            count_text = (row["original_count"] or "").strip()
            if not original:
                errors.append(f"tag-crosswalk.csv:{idx}: original_tag is empty")
                continue
            if not consolidated:
                errors.append(f"tag-crosswalk.csv:{idx}: consolidated_tag is empty for '{original}'")
                continue
            try:
                parsed_count = int(count_text)
            except Exception:
                errors.append(f"tag-crosswalk.csv:{idx}: original_count '{count_text}' is not an integer")
                parsed_count = None
            if original in crosswalk_map and crosswalk_map[original] != consolidated:
                errors.append(
                    f"tag-crosswalk.csv:{idx}: conflicting consolidated_tag for '{original}'"
                )
            crosswalk_map[original] = consolidated
            if parsed_count is not None and source_tag_counts.get(original) != parsed_count:
                errors.append(
                    f"tag-crosswalk.csv:{idx}: original_count for '{original}' was {parsed_count}, "
                    f"expected {source_tag_counts.get(original, 0)}"
                )

        crosswalk_tags = set(crosswalk_map)
        missing_crosswalk = sorted(source_tags - crosswalk_tags)
        extra_crosswalk = sorted(crosswalk_tags - source_tags)
        if missing_crosswalk:
            errors.append(
                f"{len(missing_crosswalk)} source tag(s) missing in crosswalk: "
                + ", ".join(missing_crosswalk[:20])
                + ("..." if len(missing_crosswalk) > 20 else "")
            )
        if extra_crosswalk:
            warnings.append(
                f"{len(extra_crosswalk)} extra crosswalk tag(s) not in source: "
                + ", ".join(extra_crosswalk[:20])
                + ("..." if len(extra_crosswalk) > 20 else "")
            )

        for idx, (source, consolidated) in enumerate(
            zip(source_rows, consolidated_rows), start=2
        ):
            for col in QUOTE_COLUMNS:
                if source[col] != consolidated[col]:
                    errors.append(
                        f"consolidated-quotes.csv:{idx}: source column '{col}' changed "
                        f"(expected verbatim copy)"
                    )
                    break

            consolidated_tag = (consolidated["consolidated_tag"] or "").strip()
            if not consolidated_tag:
                errors.append(f"consolidated-quotes.csv:{idx}: consolidated_tag is empty")
                continue

            expected_consolidated = crosswalk_map.get(source["tag"])
            if expected_consolidated and consolidated_tag != expected_consolidated:
                errors.append(
                    f"consolidated-quotes.csv:{idx}: consolidated_tag '{consolidated_tag}' does not "
                    f"match crosswalk '{expected_consolidated}' for original tag '{source['tag']}'"
                )

        semantic_errors = semantic_quality_errors(source_rows, crosswalk_map, consolidated_rows)
        errors.extend(semantic_errors)

        # Per requirements, cardinality is enforced after semantic quality passes.
        consolidated_unique = len(
            {
                row["consolidated_tag"].strip()
                for row in consolidated_rows
                if (row["consolidated_tag"] or "").strip()
            }
        )
        if not semantic_errors and (
            consolidated_unique < CONSOLIDATED_COUNT_MIN
            or consolidated_unique > CONSOLIDATED_COUNT_MAX
        ):
            direction = "merge near-semantic neighbors" if consolidated_unique > CONSOLIDATED_COUNT_MAX else "split overloaded consolidated tags"
            errors.append(
                f"Consolidated unique tag count {consolidated_unique} was outside "
                f"{CONSOLIDATED_COUNT_MIN}-{CONSOLIDATED_COUNT_MAX}. Re-run mapping and {direction}."
            )

    print("\nPhase 4: Verify Tag Consolidation")
    print(f"{'─' * 50}")
    print(f"  Source quotes        : {QUOTES_PATH.relative_to(ROOT)}")
    print(f"  Consolidated quotes  : {CONSOLIDATED_QUOTES_PATH.relative_to(ROOT)}")
    print(f"  Crosswalk            : {CROSSWALK_PATH.relative_to(ROOT)}")
    print(f"  Report               : {REPORT_PATH.relative_to(ROOT)}")
    print(f"  Source rows          : {len(source_rows)}")
    print(f"  Consolidated rows    : {len(consolidated_rows)}")

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

    print("\nStatus: PASS")


if __name__ == "__main__":
    main()
