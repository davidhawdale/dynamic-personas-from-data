# /add-workflow

Scaffold a new directive workflow: create the directive cover sheet, workflow folder, and orchestration file from templates, then summarise what to fill in next.

## Usage

```
/add-workflow                  # ask for workflow name and goal
/add-workflow <workflow-name>  # skip the name prompt
```

Example:
- `/add-workflow analyze-sentiment-trends`

## Procedure

### Step 1: Get workflow name and goal

If no argument was provided, ask:
1. What is the workflow name? (will be used as the kebab-case folder and file name)
2. What does this workflow produce in one sentence?

Confirm the name follows kebab-case before proceeding. If it doesn't, suggest the corrected form.

### Step 2: Check nothing already exists

Check that neither of these paths exists:
- `01-directives/<workflow-name>.md`
- `02-workflows/<workflow-name>/`

If either exists, stop and report to the user. Do not overwrite.

### Step 3: Create the directive file

Create `01-directives/<workflow-name>.md` from `10-resources/templates/directive-template.md`.

Fill in what is known:
- Replace `{Directive Name}` with the workflow name in title case
- Replace the `## Workflow` pointer with the correct path: `See \`02-workflows/<workflow-name>/\` for the detailed process.`
- Leave all other placeholder sections (`{...}`) for the user to complete

### Step 4: Create the workflow folder and orchestration file

1. Create folder `02-workflows/<workflow-name>/`
2. Create `02-workflows/<workflow-name>/orchestration.md` from `10-resources/templates/orchestration-template.md`

Fill in what is known:
- Replace `{Workflow Name}` with the workflow name in title case
- Set the directive type line to: `**Directive workflow** — triggered by user request. See \`01-directives/<workflow-name>.md\` for goal, inputs, and acceptance criteria.`
- Leave all other placeholder sections (`{...}`) for the user to complete

### Step 5: Summarise what was created

Report:
- Files created (with paths)
- What the user still needs to fill in — list the placeholder sections by name
- Suggested next steps:
  - Complete the Goal, Context, Acceptance Criteria in the directive
  - Define the phases in orchestration.md
  - Add `prepare.py` and `verify.py` scripts to the workflow folder
  - Add any required sub-agents to `.claude/agents/`
