# Directory and Naming Conventions

## Directory Map

| Directory | Purpose | Rules |
|-----------|---------|-------|
| `00-brief/` | Project brief and high-level context | Read-only |
| `01-directives/` | Thin cover sheets pointing to workflows | Read-only |
| `02-workflows/` | Self-contained workflow folders (orchestration + scripts) | Read/write during development |
| `02-workflows/shared/` | Reusable deterministic scripts used by multiple workflows | Check here before writing new scripts |
| `03-inputs/` | Raw source data | **Read-only — never write to `03-inputs/`** |
| `04-process/` | Intermediate files, regenerable | Write freely; treat as ephemeral |
| `05-outputs/` | Final deliverables | **Do not overwrite without user confirmation** |
| `10-resources/templates/` | Output formatting templates | Read-only |
| `.claude/agents/` | Sub-agent definitions | Read/write during development |
| `.claude/rules/` | Operational rules (auto-loaded by Claude Code) | Read-only at runtime |
| `.claude/skills/` | Skill procedures invoked with `/skill-name` | Read-only at runtime |
| `.env` | Environment variables and API keys | Read-only |
| `.tmp/` | Temporary intermediate files | Write freely; never commit |

## Behavioral Rules

**`04-process/` files are regenerable intermediates.**
Never treat them as final outputs. If a process file is missing or corrupted, re-run the upstream workflow phase that generates it.

**`05-outputs/` files are final deliverables.**
Do not overwrite or delete a file in `05-outputs/` without explicit user confirmation. If a workflow would replace an existing output, confirm before proceeding.

**`03-inputs/` is read-only.**
Workflows read from `03-inputs/` but never write to it. Source data must not be modified by any workflow.

**All filenames use kebab-case.**
Examples: `participant-archetypes.md`, `research-question-analysis.md`, `workflow-run-log.jsonl`.
If an agent or script produces a file with a different naming style, rename it to kebab-case before saving.

## Data Flow

Data always flows numerically through the directory structure:

```
03-inputs/ → (workflow) → 04-process/ → (workflow) → 05-outputs/
```

Never write final outputs directly to `04-process/`, and never use `03-inputs/` as a staging area.
