# Agent Project Framework

A structured template for AI-assisted analytical projects, compatible with Claude Code, OpenAI Codex, and Gemini.

## The 3-Layer Architecture

| Layer | Role | Lives in |
|---|---|---|
| **Directives** | Define what to do and why | `01-directives/` |
| **Orchestration** | You (the AI) — decide, sequence, handle errors | `02-workflows/` |
| **Execution** | Python scripts (deterministic) + sub-agents (judgement) | `02-workflows/`, `.claude/agents/` |

LLMs are probabilistic; business logic needs determinism. This architecture separates the two.

## Using This Template

### One-time setup

1. Click **Use this template** on GitHub, name your new repo, and clone it
2. Open in your AI environment (Claude Code, Codex, Gemini)
3. Run `/new-project` (Claude Code) or follow the `SKILL.md` procedure in `.claude/skills/new-project/` manually
4. Fill in `00-brief/project-brief.md`
5. Add source data to `03-inputs/`
6. Run `/add-workflow` to scaffold your first directive and workflow

### Key commands (Claude Code)

| Command | What it does |
|---|---|
| `/new-project` | Initialise a fresh clone into a working project |
| `/add-workflow` | Scaffold a new directive and workflow folder |
| `/run-workflow <name>` | Run a workflow end-to-end |
| `/status` | Show which outputs exist and what may be stale |
| `/validate-outputs` | Check output quality without re-running |
| `/update-learnings` | Capture session learnings in orchestration files |

### Environment-specific notes

- **Claude Code** — `.claude/rules/` auto-loads at session start. Use slash commands above.
- **OpenAI Codex** — Read all files in `.claude/rules/` manually at session start. See `AGENTS.md` for Codex-specific instructions.
- **Gemini** — Read all files in `.claude/rules/` manually at session start. See `GEMINI.md` for Gemini-specific instructions.

## Directory Structure

| Directory | Purpose | Writable? |
|---|---|---|
| `00-brief/` | Project brief and high-level context | Read-only at runtime |
| `01-directives/` | Thin cover sheets pointing to workflows | Read-only at runtime |
| `02-workflows/` | Workflow orchestration files and scripts | Yes |
| `02-workflows/shared/` | Reusable scripts used by multiple workflows | Yes |
| `03-inputs/` | Raw source data | **Never write here** |
| `04-process/` | Intermediate files (regenerable) | Yes |
| `05-outputs/` | Final deliverables | Confirm before overwriting |
| `10-resources/templates/` | Directive and orchestration templates | Read-only |
| `.claude/agents/` | Sub-agent definitions | Yes |
| `.claude/rules/` | Operational rules (auto-loaded by Claude Code) | Read-only |
| `.claude/skills/` | Skill procedures invoked with `/skill-name` | Read-only |

## Environment Variables

Store API keys once in `~/.agent-project.env`. When you run `bash setup.sh`, it will automatically symlink that file as `.env` in your project — no manual copying required.

```bash
# ~/.agent-project.env
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```
