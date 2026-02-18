# Model Selection

Choose the right model tier for each task. Match the model to the cognitive demand.

## Tier Guide

- **Haiku** — Mechanical tasks with clear rules: translation, format conversion, data extraction with fixed patterns
- **Sonnet** — Judgement tasks: evaluating relevance, assessing sentiment, identifying themes, writing synthesis
- **Opus** — Complex reasoning, architectural decisions, multi-step planning

When in doubt, ask: "Does this task need judgement or just execution?" Execution → Haiku. Judgement → Sonnet. Planning → Opus.

## Agent vs Skill

If the task needs a specific model tier (especially Haiku) or tool restrictions — use an agent. If it's a procedure the main Sonnet context can orchestrate — use a skill. Agents cannot call skills; the call hierarchy only flows downward.
