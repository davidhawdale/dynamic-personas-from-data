# /status

Show a quick project health summary: what outputs exist, which workflows have been run, and what might need attention.

## Usage

```
/status
```

No arguments. Read-only — does not run any workflow or modify any files.

## Procedure

### Step 1: List output files

Read `05-outputs/` and list every file with its modification date. Format as a table:

| Output file | Last modified |
|-------------|---------------|
| `research-question-analysis.md` | 2026-02-15 14:32 |
| ... | ... |

### Step 2: Cross-reference with directives

List each directive in `01-directives/` and flag whether a corresponding output exists in `05-outputs/`:

| Directive | Expected output | Status |
|-----------|----------------|--------|
| `analyze-by-research-question` | `research-question-analysis.md` | ✓ exists |
| `analyze-and-create-archetypes` | `participant-archetypes.md` | ✓ exists |
| `analyze-by-vc-pitch` | `vc-pitch.md` | ✓ exists |
| `create-personas-from-archetypes` | `personas-from-archetypes/` | ✓ exists |
| `build-screener-for-recruitment` | `recruitment-screener.md` | ✓ exists |
| `assess-vc-pitch-by-three-amigos` | `assess-vc-pitch-by-three-amigos.md` | ✗ missing |

### Step 3: Check for staleness

For each existing output, check if its modification date is older than the key source inputs it depends on. Flag any outputs that may be stale:

- `research-question-analysis.md` stale if older than newest file in `03-inputs/interview-transcripts/`
- `participant-archetypes.md` stale if older than `research-question-analysis.md`
- `vc-pitch.md` stale if older than newest extract in `04-process/extracts/`
- Persona files stale if older than `participant-archetypes.md`

### Step 4: Show recent run history

If `04-process/workflow-run-log.jsonl` exists, display the last 5 entries:

| Timestamp | Directive | Status | Issues |
|-----------|-----------|--------|--------|
| 2026-02-18 10:30 | analyze-by-research-question | PASS | — |
| ... | ... | ... | ... |

If the log does not exist, note: "No run history yet. Run a workflow with `/run-workflow` to start logging."

### Step 5: Summary

End with a one-line summary:
- How many outputs exist out of how many directives
- Whether any outputs are stale
- Last run date and status (from log)
