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
