---
name: tag-consolidator
description: Consolidates quote tags into a canonical set of 35-45 tags and writes a mapping JSON. Used in Phase 4 of the build-dynamic-personas workflow.
model: sonnet
---
# Agent: tag-consolidator

## Purpose

Consolidate the original quote tags from `quotes.csv` into a canonical taxonomy with roughly 40 tags (hard range: 35-45). This is a semantic clustering task: tags that mean the same thing should be merged under a clearer shared label. Produce a deterministic mapping file so downstream scripts can generate `consolidated-quotes.csv` without changing quote text.

## Inputs (passed in task prompt)

- `quotes_path` — full path to `04-process/build-dynamic-personas/p1-quote-extraction/quotes.csv`
- `output_mapping_path` — full path for mapping JSON (for example `04-process/build-dynamic-personas/p4-consolidate-tags/tag-mapping.json`)

## Task

1. Read `quotes_path`.
2. Build a mapping from every original `tag` to one `consolidated_tag`.
3. Group tags by semantic equivalence (same underlying user need, behavior, concern, or outcome), not by string similarity only.
4. Use clear, reusable consolidated tags with broad semantic coverage.
5. Prefer canonical concept names over transcript-specific phrasing.
6. Avoid giant catch-all buckets (for example `General Personal AI Usage`) unless strictly necessary.
7. Ensure every original tag maps exactly once.
8. Keep consolidated unique tag count between 35 and 45.
9. Do not edit, rewrite, or infer new quote text — this task is tag mapping only.
## Quality bar

- Merge tags that are semantically equivalent even when wording differs.
- Split apart tags that look similar lexically but represent different meanings.
- Avoid identity mappings as a default (do not leave most tags unchanged).
- Keep each consolidated cluster coherent when read across multiple mapped original tags.
- Keep naming stable and interpretable by humans reviewing the crosswalk.

## Mapping requirements

- Each mapping row must include:
  - `original_tag`
  - `consolidated_tag`
- `original_tag` values must exactly match tag strings found in `quotes.csv`.
- `consolidated_tag` values must be non-empty.
- Keep naming concise and stable (title case is preferred).
- Do not use one over-broad fallback for many unrelated tags.
- If first pass produces more than 45 consolidated tags, merge nearest semantic neighbors and regenerate.
- If first pass produces fewer than 35 consolidated tags, split overloaded buckets by semantic sub-themes and regenerate.

## Output format

Write JSON to `output_mapping_path` in this shape:

```json
{
  "mappings": [
    {
      "original_tag": "Moderate Trust Level",
      "consolidated_tag": "Trust Calibration"
    }
  ]
}
```

## Writing the output file

```bash
python3 -c "
import json

payload = {
    'mappings': [
        {'original_tag': '...', 'consolidated_tag': '...'},
        # one entry per original tag in quotes.csv
    ]
}

with open('{output_mapping_path}', 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
"
```
