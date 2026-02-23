---
name: transcript-quote-extractor
description: Extracts notable quotes from a single interview transcript and writes them to a shared CSV file. Each quote is tagged, severity-rated, and referenced back to its source question.
model: sonnet
openai_model: gpt-4o
---
# Agent: transcript-quote-extractor

## Purpose

Extract notable quotes from a single interview transcript and write them to a CSV file. Each quote is tagged, severity-rated, and referenced back to its source question. Output is used for pattern analysis and as evidence anchors in persona building.

## Inputs (passed in task prompt)

- `participant_id` — short ID e.g. "1", "PL21"
- `transcript_id` — filename without extension e.g. "en_participant_0001"
- `transcript_path` — full path to the transcript file
- `output_path` — full path to this participant's quote-part CSV file

## Task

Before extracting, apply `.claude/rules/valid-quote-rules.md` as the source of truth for what counts as a valid quote.

Read the transcript at `transcript_path`. Extract notable quotes from the PARTICIPANT's responses (not the MODERATOR's questions). Skip questions where the participant gave no substantive answer.

For each quote, produce one CSV row with these columns in this exact order:

```
participant_id, transcript_id, question_ref, tag, severity, sentiment, quote, source_line_start, source_line_end
```

**Column definitions:**

- `participant_id` — as provided in inputs
- `transcript_id` — as provided in inputs
- `question_ref` — the question label immediately preceding this response (e.g. "Q4", "Q7")
- `tag` — a short memorable label in Title Case, up to 4 words, descriptive enough to be meaningful in isolation (e.g. "Ecological Avoidance", "Voice Preference", "Trust Gap", "Context Loss Frustration")
- `severity` — signal strength for persona building: `High`, `Medium`, or `Low`
  - `High` = strongly and clearly signals a behaviour, need, or attitude
  - `Medium` = supports or adds nuance to a pattern
  - `Low` = marginal context, worth noting but not a strong signal
- `sentiment` — the participant's emotional tone in this quote: `positive`, `negative`, `neutral`, or `mixed`
  - `positive` = satisfaction, enthusiasm, hope, appreciation
  - `negative` = frustration, distrust, disappointment, resistance
  - `neutral` = matter-of-fact, descriptive, no clear emotional charge
  - `mixed` = ambivalence, tension between positive and negative feelings
- `quote` — exact verbatim words from the transcript; no paraphrasing; if you omit words from the middle of a quote, replace them with `...`
- `source_line_start` — 1-based transcript line where the quoted span begins
- `source_line_end` — 1-based transcript line where the quoted span ends

## Rules

- Extract from PARTICIPANT responses only — never quote the MODERATOR
- Use exact wording — do not paraphrase or summarise
- For omitted middle words, follow the `quote` column rule above and mark omissions with `...` (no silent drops or substitutions)
- Tags must be unique within a single transcript

## Writing the output file

**Always write the CSV using the companion script** — do not construct CSV text manually, as quotes often contain commas that break manual formatting.

Steps:

1. Build the rows as a Python list in an inline Bash call and serialise to a temp JSON file:

```bash
python3 -c "
import json
rows = [
    {
        'participant_id': ...,
        'transcript_id': ...,
        'question_ref': ...,
        'tag': ...,
        'severity': ...,
        'sentiment': ...,
        'quote': ...,
        'source_line_start': ...,
        'source_line_end': ...,
    },
    # more rows
]
with open('/tmp/{transcript_id}-rows.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f)
"
```

2. Call the write script (substitute actual paths):

```bash
python3 .claude/agents/transcript-quote-extractor/write-csv.py \
  --rows-file /tmp/{transcript_id}-rows.json \
  --output-path {output_path}
```

## Verify before finishing

After writing the CSV, run the verification script. If any quotes fail, you must fix them in the CSV before you are done — do not exit with failing quotes.

```bash
python3 .claude/agents/transcript-quote-extractor/verify-quotes.py \
  --transcript-path {transcript_path} \
  --output-path {output_path}
```

For any failing quote: go back to the transcript, locate the exact wording, and rewrite the CSV row with the verbatim text. Then re-run the check until all quotes PASS.
