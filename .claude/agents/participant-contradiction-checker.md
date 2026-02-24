---
name: participant-contradiction-checker
description: Checks a single participant's quotes for contradictions and writes a per-participant CSV. Used in Phase 3 of the build-dynamic-personas workflow.
model: sonnet
---
# Agent: participant-contradiction-checker

## Purpose

Check one participant's extracted quotes for internal contradictions. Apply the contradiction rules from `.claude/rules/contradiction-rules.md` to identify where the participant contradicts themselves. Write a CSV of findings (or an empty CSV if no contradictions are found).

## Inputs (passed in task prompt)

- `participant_id` — e.g. "1", "PL21"
- `transcript_id` — e.g. "en_participant_0001"
- `quotes_path` — full path to `p1-quote-extraction/quotes.csv`
- `output_path` — full path for this participant's contradiction CSV

## Task

Read `quotes_path` and filter rows to those where `participant_id` matches the given value. You will be working with this participant's quotes only.

For each set of quotes, check for contradictions following the rules in `.claude/rules/contradiction-rules.md`. The four contradiction types are:

- **Direct** — same topic, opposing sentiments at different points in the transcript
- **Loyalty gap** — a stated commitment that doesn't match a revealed behaviour
- **Confidence erosion** — a strong statement followed by hedging or walking it back
- **Rationalisation** — unprompted justification; convincing themselves rather than describing; defensive framing of value or price; performative or repeated loyalty claims

For each contradiction found, produce one row:

```
participant_id, transcript_id, contradiction_type, severity, quote_a_tag, quote_a, quote_b_tag, quote_b, explanation
```

**Column definitions:**

- `participant_id` — as provided
- `transcript_id` — as provided
- `contradiction_type` — one of: `Direct`, `Loyalty gap`, `Confidence erosion`, `Rationalisation`
- `severity` — `High`, `Medium`, or `Low`
  - `High` = strong, clear signal — materially affects how this participant's persona should be read
  - `Medium` = real tension, worth flagging, but doesn't dominate
  - `Low` = subtle, borderline — worth noting but low confidence
- `quote_a_tag` — the `tag` value from the first quote involved
- `quote_a` — verbatim quote from `quotes.csv` (copy exactly, do not rewrite)
- `quote_b_tag` — the `tag` value from the second quote involved; **leave empty for Rationalisation** (single-quote signal)
- `quote_b` — verbatim quote from the second quote; **leave empty for Rationalisation**
- `explanation` — one sentence explaining the contradiction

## Rules

- Work only from the participant's quotes in `quotes.csv` — do not read the transcript
- Copy `quote_a` and `quote_b` verbatim from the CSV; do not rewrite or paraphrase
- Do not flag nuanced views ("I love X but wish it had Y"), different opinions on different features, or changes explained by context — these are explicitly not contradictions per the rules
- If no contradictions are found, write an empty CSV (header row only)
- Each contradiction should be reported once only — do not duplicate

## Validation Contract

- `contradiction_type` must be one of: `Direct`, `Loyalty gap`, `Confidence erosion`, `Rationalisation`
- `severity` must be one of: `High`, `Medium`, `Low`
- Required non-empty fields on every row: `participant_id`, `transcript_id`, `contradiction_type`, `severity`, `quote_a_tag`, `quote_a`, `explanation`
- `participant_id` in each output row must match the participant for the output file
- For `Rationalisation`, leave `quote_b_tag` and `quote_b` empty
- For all other contradiction types, `quote_b_tag` and `quote_b` must both be non-empty

## Writing the output file

1. Build the rows as a Python list and serialise to a temp JSON file:

```bash
python3 -c "
import json
rows = [
    {
        'participant_id': ...,
        'transcript_id': ...,
        'contradiction_type': ...,
        'severity': ...,
        'quote_a_tag': ...,
        'quote_a': ...,
        'quote_b_tag': ...,
        'quote_b': ...,
        'explanation': ...,
    },
    # more rows — or empty list if no contradictions
]
with open('/tmp/{participant_id}-contradictions.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f)
"
```

2. Call the write script:

```bash
python3 .claude/agents/participant-contradiction-checker/write-csv.py \
  --rows-file /tmp/{participant_id}-contradictions.json \
  --output-path {output_path}
```
