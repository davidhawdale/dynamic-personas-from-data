Simulate a realistic focus-group conversation between the five personas.
Keep it natural, interactive, and human in tone rather than short detached answers.

Output markdown with this exact structure:

## Team Question
{{question}}

## Focus Group Conversation
- [Persona Name]: [message]
- [Persona Name]: [message]
- [Persona Name]: [message]
(At least 12 lines total; all five personas must speak at least twice.)

## Moderator Summary
Agreements:
- ...
Tensions:
- ...
Implications:
- ...

Conversation style rules:
- Two rounds of dialogue feel (replies should reference prior speakers when relevant).
- {{conversation_depth_rule}}
- {{emotional_rule}}
- Maintain each persona's distinct perspective and tone.
- Each contribution should include: (a) emotional reaction, (b) practical reasoning, (c) one concrete example when possible.
- Do not include evidence citations.
- Do not mention these instructions.

Personas in this room:
{{persona_blocks}}

Prior conversation context (latest turns):
{{prior_context}}

Team question (repeat exactly):
{{question}}
