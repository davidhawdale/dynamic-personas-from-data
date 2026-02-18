# Orchestrator Decisions

Applies to all directive workflows. Use these rules whenever you are orchestrating a workflow and encounter a WARN, FAIL, or ambiguous situation.

## When to Self-Anneal (Auto-Fix)

Attempt automatic correction without asking the user when:
- A Python script errors due to a missing file, wrong path, or import issue
- An agent output is malformed (wrong format, missing required section, wrong count)
- Count parity mismatch between expected and actual files (e.g. N transcripts in ≠ N extracts out)

## Self-Annealing Procedure

When something breaks, follow this sequence:

1. Fix the script or tool
2. Test the fix — make sure it works
3. Update the workflow orchestration file to capture what you learned
4. System is now stronger

## When to Ask the User

Stop and ask the user before proceeding when:
- A paid API call is required (e.g. translation via external API, model calls beyond the current session)
- Output quality is a judgment call (the output exists and is structurally valid but may be inadequate)
- Requirements are ambiguous or contradictory — don't guess, clarify

## Retry Policy

| Outcome | Action |
|---------|--------|
| `WARN` | Log it, continue — do not stop or retry |
| `FAIL` (first) | Re-run the failed agent/script **once** with a specific correction instruction |
| `FAIL` (second) | **Stop.** Report to user with: what failed, what was tried, what input/output to inspect |

**Re-run cap:** max 1 retry per agent instance, max 2 retries per phase total. Never loop indefinitely.

## How to Re-Run Correctly

When re-running after a FAIL, always provide a specific correction — don't re-run with identical inputs.

Good: "Re-run archetype-writer with explicit instruction to ensure exactly 5 archetypes and assign participant en_0042 to Archetype 3."
Bad: Re-run archetype-writer with the same prompt.

## What to Include in Final Reports

Every workflow completion report must include:
- WARN/FAIL conditions that occurred and whether they were resolved
- Any items requiring human review (quote validation WARN/FAIL examples, etc.)
- Final status: PASS, WARN, or FAIL

## Exceptions

Some workflows have genuinely different failure modes requiring different corrections — keep their specific branching logic. Example: `assess-vc-pitch-by-three-amigos` verify phase distinguishes `FAIL too long` from `FAIL missing sections` because each requires a different fix, not a generic retry.
