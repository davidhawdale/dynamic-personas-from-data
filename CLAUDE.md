# Agent Instructions

> Core content (everything above the Session Start section) is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md. When updating core content, update all three files. The Session Start section is environment-specific — do not mirror it.

## The 3-Layer Architecture

This project uses a 3-layer architecture. LLMs are probabilistic; business logic needs determinism. The layers fix that mismatch.

**Layer 1 — Directive (What & Why):** Thin cover sheets in `01-directives/`. Each defines a goal, its inputs, and points to a workflow folder. Scan this folder to see what the project can do.

**Layer 2 — Orchestration (Decisions):** This is you. Read the directive, then read the workflow orchestration file for detailed steps. Call scripts and agents in the right order, handle errors, update the orchestration file with learnings.

**Layer 3 — Execution (Doing the work):** Two tool types, choose whichever fits:

- **Deterministic Python scripts** — for precision, repeatability, external integration (API calls, data transforms, file operations). Live in `02-workflows/{workflow}/`.
- **Sub-agents** — for tasks needing flexibility, judgement, or language understanding (extraction, synthesis, translation). Live in `.claude/agents/`. Each agent is self-contained with its rules inlined.

**Why this works:** 90% accuracy per step = 59% success over 5 steps. Push precision work into deterministic code, use LLM agents where judgement adds value.

**Call hierarchy:**
```
User → invokes Skill (main context, Sonnet)
  → Skill orchestrates Agent (isolated context, model-tiered)
    → Agent calls Python script (deterministic)
```
The hierarchy is one-directional — agents cannot call skills.

## Workflows

- **Directive workflows** have an entry in `01-directives/` and are triggered by user requests (e.g., "analyze by topic").
- **Utility workflows** are prerequisites called automatically by other workflows — they don't have directives (e.g., `translate-interview-transcripts/` runs automatically when an analysis needs translated transcripts).

Use `/add-workflow` to scaffold a new workflow.

## Operating Principle

Self-anneal when things break: read the error, fix the script, test it (check with user first if it uses paid tokens/credits), and update the workflow orchestration file with what you learned. System gets stronger with each fix.

## Operational Standards

For directory conventions, naming rules, model selection, development standards, and orchestrator decisions, read `.claude/rules/` at session start. Claude Code auto-loads all files in `.claude/rules/` — other environments should read them explicitly.

## Summary

You sit between human intent (directives) and efficient execution (workflow scripts and agents). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

## Session Start — Claude Code

At the start of each session:

1. Rules in `.claude/rules/` auto-load — no action needed.
2. Run `/new-project` on a freshly cloned template to initialise the project brief and directory structure.
3. Run `/status` to see what outputs exist and which workflows have been run.
4. Run `/run-workflow <directive-name>` to execute a workflow end-to-end.
5. Run `/add-workflow` to scaffold a new workflow.
6. Run `/validate-outputs` to check output quality without re-running a workflow.
7. Run `/update-learnings` to capture session learnings in orchestration files.
