# /update-learnings

Capture session learnings in the Learnings sections of orchestration files before context is lost.

## Usage

```
/update-learnings                          # guided — lists current Learnings, prompts user
/update-learnings <workflow-name>          # target a specific orchestration file
```

Examples:
- `/update-learnings`
- `/update-learnings analyze-and-create-archetypes`

## Procedure

### Step 1: List orchestration files and show current Learnings

Read all `02-workflows/*/orchestration.md` files. For each, extract the `## Learnings` section and display it in a compact summary:

| Workflow | Current learnings |
|---|---|
| `analyze-by-research-question` | 2 entries (latest: 2026-02-15) |
| `analyze-and-create-archetypes` | 1 entry (latest: 2026-02-15) |
| `analyze-by-vc-pitch` | *(empty)* |
| ... | ... |

If a specific workflow was provided as an argument, show only that workflow's current Learnings in full.

### Step 2: Ask what was learned

Prompt the user:

> "What did you learn this session? Describe any issues encountered, fixes applied, new edge cases, API constraints, or anything useful for next time. You can reference one or more workflows."

Accept freeform text. If the user names a workflow explicitly, map it to the correct orchestration file.

### Step 3: Draft the learning entry

Format the user's input as a timestamped entry for the relevant `## Learnings` section:

```markdown
### <Short title> (<YYYY-MM-DD>)

<Learning text, concise — 1–4 sentences. Focus on what to do differently next time.>
```

Use today's date. If the learning applies to multiple workflows, draft an entry for each.

### Step 4: Confirm before writing

Show the draft entry (or entries) and the target file(s) to the user:

> "I'll add this to `02-workflows/<workflow>/orchestration.md`. Confirm? (yes / edit / skip)"

Only write after confirmation. On "edit", accept revised text and re-confirm. On "skip", discard that entry.

### Step 5: Append to orchestration file(s)

Append the confirmed entry to the end of the `## Learnings` section in the relevant orchestration file(s).

Report: which files were updated and the title of each entry added.
