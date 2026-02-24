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

### Phase 4: Consolidate the Quote Tags

- Goal: Consolidate `p1` quote tags to a canonical set of around 40 tags (hard range 35-45) without changing quote text.
- Input:
  - `04-process/build-dynamic-personas/p1-quote-extraction/quotes.csv`
- Sequence:
  1. Build tag mapping with `tag-consolidator`.
  2. Run `python3 02-workflows/build-dynamic-personas/run-tag-consolidation.py`.
  3. Run `python3 02-workflows/build-dynamic-personas/verify-tag-consolidation.py`.
  4. Run the Phase 4 Human Review Gate summary and stop for user confirmation.
- For consolidation mapping, spawn a `tag-consolidator` sub-agent with:
  - `quotes_path` — full path to `p1-quote-extraction/quotes.csv`
  - `output_mapping_path` — `04-process/build-dynamic-personas/p4-consolidate-tags/tag-mapping.json`
- In Codex/OpenAI, "spawn sub-agent" means: read `.claude/agents/tag-consolidator.md` and execute those instructions inline.
- Output:
  - `04-process/build-dynamic-personas/p4-consolidate-tags/consolidated-quotes.csv` (all original quote rows + `consolidated_tag`)
  - `04-process/build-dynamic-personas/p4-consolidate-tags/tag-crosswalk.csv` (original tag to consolidated tag mapping)
  - `04-process/build-dynamic-personas/p4-consolidate-tags/tag-consolidation-report.md` (summary and distribution)
- Constraints:
  - Do not overwrite `p1-quote-extraction/quotes.csv`
  - Do not alter any `quote` text in output rows
  - Enforce semantic quality first (no over-broad catch-all buckets, avoid pass-through mapping, avoid dominant mega-buckets)
  - Only after semantic quality passes, enforce consolidated unique tag count between 35 and 45
- If fail: Re-run the failed agent/script once with a specific correction instruction; if second fail, skip and log WARN

### Phase 4 Gate: Human Review — HARD STOP

**Always stop here. Do not continue without explicit user confirmation.**

After Phase 4 completes, read:

- `04-process/build-dynamic-personas/p4-consolidate-tags/consolidated-quotes.csv`
- `04-process/build-dynamic-personas/p4-consolidate-tags/tag-consolidation-report.md`

Present a summary:

```
Phase 4 complete — Tag Consolidation Summary
────────────────────────────────────────────
Total quotes:              N
Original unique tags:      N
Consolidated unique tags:  N

Detailed results:
  04-process/build-dynamic-personas/p4-consolidate-tags/tag-consolidation-report.md
  04-process/build-dynamic-personas/p4-consolidate-tags/consolidated-quotes.csv
```

Then ask:

- **If validation passes:** "Phase 4 passed. Please review the report and consolidated quotes output. Ready to continue to the next phase?"
- **If validation fails:** "Phase 4 has validation failures. Would you like to re-run consolidation with correction instructions?"

Do not proceed to the next phase until the user explicitly says yes.

### Phase 5: Synthesize Archetypes

- Goal: Produce exactly five named core archetypes with participant assignments, plus optional outlier entries for weak-fit participants.
- Input:
  - `04-process/build-dynamic-personas/p4-consolidate-tags/consolidated-quotes.csv`
  - `04-process/build-dynamic-personas/p0-prepare/manifest.json`
- Sequence:
  1. Run `python3 02-workflows/build-dynamic-personas/prepare-archetype-extracts.py`.
  2. Run `archetype-writer` sub-agent.
  3. Run `python3 02-workflows/build-dynamic-personas/extract-archetype-assignments.py`.
  4. Run `python3 02-workflows/build-dynamic-personas/verify-archetype-assignments.py`.
  5. Run the Phase 5 Human Review Gate summary and stop for user confirmation.
- For archetype synthesis, spawn the `archetype-writer` sub-agent from:
  - `.claude/agents/archetype-writer/archetype-writer.md`
- Pass these values in the task prompt:
  - `extracts_folder` — `04-process/build-dynamic-personas/p5-synthesize-archetypes/extracts/`
  - `output_file` — `04-process/build-dynamic-personas/p5-synthesize-archetypes/archetypes.md`
  - `expected_participants` — from `04-process/build-dynamic-personas/p5-synthesize-archetypes/expected-participants.json`
- In Codex/OpenAI, "spawn sub-agent" means: read `.claude/agents/archetype-writer/archetype-writer.md` and execute those instructions inline.
- Output:
  - `04-process/build-dynamic-personas/p5-synthesize-archetypes/archetypes.md`
  - `04-process/build-dynamic-personas/p5-synthesize-archetypes/participant-archetype-assignments.csv`
- Constraints:
  - Exactly 5 core archetypes
  - Every expected participant appears exactly once across core archetypes and optional outliers
  - Evidence quotes must remain verbatim
- If fail: Re-run the failed agent/script once with a specific correction instruction; if second fail, skip and log WARN

### Phase 5 Gate: Human Review — HARD STOP

**Always stop here. Do not continue without explicit user confirmation.**

After Phase 5 completes, read:

- `04-process/build-dynamic-personas/p5-synthesize-archetypes/archetypes.md`
- `04-process/build-dynamic-personas/p5-synthesize-archetypes/participant-archetype-assignments.csv`

Present a summary:

```
Phase 5 complete — Archetype Synthesis Summary
──────────────────────────────────────────────
Core archetypes produced:   5
Participants expected:      N
Participants assigned:      N
Outliers:                   N

Detailed results:
  04-process/build-dynamic-personas/p5-synthesize-archetypes/archetypes.md
  04-process/build-dynamic-personas/p5-synthesize-archetypes/participant-archetype-assignments.csv
```

Then ask:

- **If validation passes:** "Phase 5 passed. Please review archetypes and assignments. Ready to continue to the next phase?"
- **If validation fails:** "Phase 5 has validation failures. Would you like to re-run archetype synthesis with correction instructions?"

Do not proceed to the next phase until the user explicitly says yes.

### Phase 6: Create Personas from Archetypes

- Goal: Produce five persona files, one per archetype.
- Input:
  - `04-process/build-dynamic-personas/p5-synthesize-archetypes/archetypes.md`
  - `04-process/build-dynamic-personas/p5-synthesize-archetypes/extracts/*.md`
  - `10-resources/templates/persona-template.md`
  - `.claude/rules/persona-diversity-guidance.md`
- Sequence:
  1. Run `python3 02-workflows/build-dynamic-personas/prepare-persona-inputs.py`.
  2. For each archetype input pack, run `persona-writer` sub-agent.
  3. Run `python3 02-workflows/build-dynamic-personas/sync-persona-filenames.py`.
  4. Run `python3 02-workflows/build-dynamic-personas/verify-personas.py`.
  5. Run `python3 02-workflows/build-dynamic-personas/verify-persona-diversity.py`.
  6. Run Phase 6 Human Review Gate summary and stop for user confirmation.
- For persona writing, spawn the `persona-writer` sub-agent from:
  - `.claude/agents/persona-writer/persona-writer.md`
- In Codex/OpenAI, "spawn sub-agent" means: read `.claude/agents/persona-writer/persona-writer.md` and execute those instructions inline.
- Output:
  - `04-process/build-dynamic-personas/p6-create-personas/personas/archetype-1.md`
  - `04-process/build-dynamic-personas/p6-create-personas/personas/archetype-2.md`
  - `04-process/build-dynamic-personas/p6-create-personas/personas/archetype-3.md`
  - `04-process/build-dynamic-personas/p6-create-personas/personas/archetype-4.md`
  - `04-process/build-dynamic-personas/p6-create-personas/personas/archetype-5.md`
- Constraints:
  - Keep quote evidence verbatim
  - Include exactly 2 quotes in each persona `## Key Quotes` section
  - Persona markdown filename must be the slugified H1 persona name (for example, `# Maya Patel` -> `maya-patel.md`)
  - Enforce set-level diversity using `.claude/rules/persona-diversity-guidance.md`
  - Write personas to `04-process/` first; do not write to `05-outputs/` in this phase
- If fail: Re-run the failed agent/script once with a specific correction instruction; if second fail, skip and log WARN

### Phase 6 Gate: Human Review — HARD STOP

**Always stop here. Do not continue without explicit user confirmation.**

After Phase 6 completes, read:
- `04-process/build-dynamic-personas/p6-create-personas/personas/`
- `04-process/build-dynamic-personas/p6-create-personas/`

Present a summary:

```
Phase 6 complete — Persona Creation Summary
───────────────────────────────────────────
Persona files produced:   N/5
Structural validation:    PASS|FAIL
Diversity validation:     PASS|FAIL

Detailed results:
  04-process/build-dynamic-personas/p6-create-personas/personas/
```

Then ask:

- **If validation passes:** "Phase 6 passed. Please review persona files. Ready to continue to the next phase?"
- **If validation fails:** "Phase 6 has validation failures. Would you like to re-run persona generation with correction instructions?"

Do not proceed to the next phase until the user explicitly says yes.
