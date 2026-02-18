# /run-workflow

Run a directive workflow end-to-end, following the correct orchestration sequence and logging the result.

## Usage

```
/run-workflow                          # show menu of available workflows
/run-workflow <directive-name>         # run a specific workflow directly
```

Examples:
- `/run-workflow analyze-by-research-question`
- `/run-workflow analyze-and-create-archetypes`
- `/run-workflow analyze-by-vc-pitch`
- `/run-workflow create-personas-from-archetypes`
- `/run-workflow build-screener-for-recruitment`
- `/run-workflow assess-vc-pitch-by-three-amigos`

## Procedure

### Step 1: List or confirm the workflow

If no argument was provided, list all directives in `01-directives/` with a one-line description of each, then ask the user which one to run.

If an argument was provided, confirm it matches a directive file before proceeding.

### Step 2: Read the directive and orchestration file

Read both:
1. `01-directives/<directive-name>.md` — goal, inputs, acceptance criteria
2. `02-workflows/<directive-name>/orchestration.md` — phases, tools, manifest format

### Step 3: Confirm prerequisites

Check that required input paths exist. For example:
- `03-inputs/interview-transcripts/` for transcript-based workflows
- `05-outputs/vc-pitch.md` for Three Amigos

If a required input is missing, stop and tell the user what is needed before proceeding.

### Step 4: Run Phase 0 (Prepare)

Follow the orchestration file exactly, starting with Phase 0. Do not skip Phase 0 — it produces the manifest that all subsequent phases depend on.

### Step 5: Execute remaining phases

Follow the orchestration file phase by phase. Apply the retry/escalation rules from `.claude/rules/orchestrator-decisions.md`.

### Step 6: Log the result

When the workflow completes, append one JSON line to `04-process/workflow-run-log.jsonl`:

```json
{"timestamp": "<ISO-8601 timestamp>", "directive": "<directive-name>", "status": "<PASS|WARN|FAIL>", "issues": ["<issue description>", ...]}
```

- `issues` is an empty array `[]` if status is PASS
- `issues` lists any WARN/FAIL conditions that occurred (even if resolved)
- Create `04-process/workflow-run-log.jsonl` if it does not exist

### Step 7: Report to user

Summarise the run:
- Workflow name and final status
- Output artifact location
- Any issues logged (WARN/FAIL with resolution status)
- Word count or record count where applicable
