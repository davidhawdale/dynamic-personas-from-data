# Build Dynamic Personas

> **Directive workflow** — triggered by user request. See `01-directives/build-dynamic-personas.md` for goal, inputs, and acceptance criteria.

## Approach

Extract and tag verbatim quotes from interview transcripts, cluster participants into distinct archetypes based on their attitudes and behaviours, then synthesise each archetype into a fully-formed Dynamic Persona profile grounded in transcript evidence.

## Process

### Phase 0: Prepare

- Goal: Validate inputs and build a manifest of all transcripts to process.
- Run: `python 02-workflows/build-dynamic-personas/prepare.py`
- Paths:
  - Transcripts in: `03-inputs/interview-transcripts/`
  - Research brief in: `03-inputs/research-brief.md`
  - Manifest out: `04-process/build-dynamic-personas/p0-prepare/manifest.json`
- Input: Files in `03-inputs/interview-transcripts/`, research brief
- Output: `p0-prepare/manifest.json` with transcript count, file paths, and language flags
- If fail: Check `03-inputs/` structure; ensure transcripts are in expected format

### Phase 1: Extract Quotes

- Goal: Extract notable quotes from each transcript; tag each with a memorable label, severity rating, sentiment, and question reference
- Input: Each transcript entry from `p0-prepare/manifest.json`
- For each transcript in the manifest, spawn a `transcript-quote-extractor` sub-agent with these values in the task prompt:
  - `participant_id` — from manifest
  - `transcript_id` — from manifest (`id` field)
  - `transcript_path` — full path to the transcript file (from manifest `path` field, resolved from project root)
  - `output_path` — `04-process/build-dynamic-personas/p1-quote-extraction/quote-parts/{participant_id}.csv`
- Output: One CSV part file per transcript in `04-process/build-dynamic-personas/p1-quote-extraction/quote-parts/`
- Merge: `python3 02-workflows/build-dynamic-personas/merge-quotes.py`
- Validate completeness: `python3 02-workflows/build-dynamic-personas/verify-quote-extracts-completion.py`
- If fail: Re-run the failed agent with a specific correction instruction; if second fail, skip and log WARN

### Phase 2: Validate Quotes

- Goal: Confirm every extracted quote is verbatim — no paraphrasing.
- Run: `python3 02-workflows/build-dynamic-personas/validate-quotes.py`
- Input: `p1-quote-extraction/quotes.csv` + `p0-prepare/manifest.json` (for transcript paths)
- Output: `p2-validate-quotes/quote-validation-report.csv` (status, reason, transcript_match, transcript_lines per quote)
- If FAIL: quote was paraphrased — re-run that participant's extractor with explicit instruction to copy text verbatim; if second fail, flag for human review

### Phase 2 Gate: Human Review — HARD STOP

**Always stop here. Do not continue without explicit user confirmation.**

After Phase 2 completes, read `p2-validate-quotes/quote-validation-report.csv` and present a summary:

```
Phase 2 complete — Quote Validation Summary
───────────────────────────────────────────
Total quotes:   N
Passed:         N
Failed:         N

[If failures > 0, list each:]
  FAIL  [tag]  participant: [id]  reason: [reason]

[If failures = 0:]
  All quotes passed verbatim check.
```

Then ask:

- **If failures > 0:** "There are [N] failed quotes. Would you like to go back and re-run the affected participant(s) before continuing, or continue to the next phase anyway?"
- **If failures = 0:** "All quotes passed. Ready to continue to the next phase?"

Do not proceed to the next phase until the user explicitly says yes.

### Phase 3: Check for Contradictions

- Goal: For each participant, identify where their quotes contradict each other. Apply the rules in `.claude/rules/contradiction-rules.md`.
- Input: `p1-quote-extraction/quotes.csv` (all validated quotes) + `p0-prepare/manifest.json` (for participant list)
- Sequence:
  1. Run `participant-contradiction-checker` per participant.
  2. Run `python3 02-workflows/build-dynamic-personas/verify-contradictions-completion.py`.
  3. Run `python3 02-workflows/build-dynamic-personas/merge-contradictions.py`.
  4. Run the Phase 3 Human Review Gate summary and stop for user confirmation.
- For each participant in the manifest, spawn a `participant-contradiction-checker` sub-agent with:
  - `participant_id` — from manifest
  - `transcript_id` — from manifest (`id` field)
  - `quotes_path` — full path to `p1-quote-extraction/quotes.csv`
  - `output_path` — `04-process/build-dynamic-personas/p3-check-contradictions/contradiction-parts/{participant_id}.csv`
- In Codex/OpenAI, "spawn sub-agent" means: read `.claude/agents/participant-contradiction-checker.md` and execute those instructions inline for each participant.
- Output: One CSV part file per participant in `04-process/build-dynamic-personas/p3-check-contradictions/contradiction-parts/` (empty CSV with header if no contradictions)
- Verify completion: `python3 02-workflows/build-dynamic-personas/verify-contradictions-completion.py`
- Merge: `python3 02-workflows/build-dynamic-personas/merge-contradictions.py`
- If fail: Re-run the failed agent once with a specific correction instruction; if second fail, skip and log WARN

### Phase 3 Gate: Human Review — HARD STOP

**Always stop here. Do not continue without explicit user confirmation.**

After Phase 3 completes, read:
- `04-process/build-dynamic-personas/p0-prepare/manifest.json`
- `04-process/build-dynamic-personas/p3-check-contradictions/contradictions.csv`

Present a summary:

```
Phase 3 complete — Contradiction Check Summary
──────────────────────────────────────────────
Participants checked:             N
Participants with contradictions: N
Total contradictions found:       N

[If contradictions found:]
  Detailed results: 04-process/build-dynamic-personas/p3-check-contradictions/contradictions.csv
  Use this file for participant-level contradiction details and quote pairs.

[If none:]
  No contradictions found across all participants.
```

Then ask:

- **If contradictions found:** "There are [N] contradictions across [N] participants. Please review 04-process/build-dynamic-personas/p3-check-contradictions/contradictions.csv. Would you like to re-run any participants before continuing?"
- **If none:** "No contradictions found. Ready to continue to the next phase?"

Do not proceed to the next phase until the user explicitly says yes.
