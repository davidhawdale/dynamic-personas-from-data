---
name: {agent-name}
description: {One sentence — what the agent does and what it returns. This is what the orchestrator reads to decide whether to invoke this agent.}
model: {haiku | sonnet | opus}
# model selection guide:
#   haiku  — mechanical tasks with clear rules (extraction, format conversion, data transforms)
#   sonnet — tasks needing judgement (evaluation, synthesis, theme identification)
#   opus   — complex reasoning or multi-step planning
openai_model: {gpt-4o-mini | gpt-4o | o1}
# openai_model equivalents:
#   haiku  → gpt-4o-mini
#   sonnet → gpt-4o
#   opus   → o1
allowed-tools: {Comma-separated list, e.g. "Read, Bash" | omit this line to allow all tools}
---
# Agent: {agent-name}

## Purpose

{One paragraph. Why this agent exists, what problem it solves, and how its output is used downstream. Include the workflow context if relevant (e.g. "used in Phase 3 of build-dynamic-personas").}

## Inputs (passed in task prompt)

- `{param_name}` — {what it is and an example value, e.g. "full path to the transcript file, e.g. `04-process/translated/en_0001.md`"}
- `{param_name}` — {description}

## Task

{Describe what the agent does, step by step. Use numbered steps if the order matters. Include any decision logic (e.g. "if the file does not exist, create it with a header row first").}

1. {Step one}
2. {Step two}
3. {Step three}

{Include field definitions, schema, or examples inline here if the task produces structured output — the agent needs this detail to do the work correctly.}

## Output

{Describe precisely what the agent returns or writes. Specify: file path, format (CSV/JSON/markdown), whether it appends or overwrites, and any required structure. If the agent returns a response to the orchestrator rather than writing a file, describe the response shape here.}

## Rules

- {Hard constraint — e.g. "Never quote the MODERATOR, only the PARTICIPANT"}
- {Hard constraint — e.g. "Do not include markdown, commentary, or explanation — CSV rows only"}
- {Hard constraint — e.g. "Do not rewrite or modify the input file"}
- {Error handling — e.g. "If the script errors, report the error verbatim and set status to FAIL"}
