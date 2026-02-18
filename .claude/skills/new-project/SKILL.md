# /new-project

Initialise a freshly cloned template into a working project: verify directory structure, create the project brief, and print a next-steps checklist.

## Usage

```
/new-project                  # interactive — asks for name, goal, and inputs
/new-project <project-name>   # skip the name prompt
```

Example:
- `/new-project customer-research-2026`

## Procedure

### Step 1: Get project details

If no argument was provided, ask:
1. What is the project name? (kebab-case, used as the folder/repo name)
2. What is the project goal in one sentence? (what this project will produce)
3. What data or inputs will you be working with? (e.g. interview transcripts, survey responses, documents)

If a project name argument was provided, ask only for the goal and inputs.

Confirm the name follows kebab-case before proceeding. If it doesn't, suggest the corrected form.

### Step 2: Ensure directory structure exists

Run `bash setup.sh` from the project root. This is idempotent — safe to run even if directories already exist. It will also wire up the `.env` file (symlink to `~/.agent-project.env` if it exists, or create a placeholder).

Report the result.

### Step 3: Create the project brief

Create `00-brief/project-brief.md` with the following content, substituting in the details collected in Step 1:

```markdown
# Project Brief: {Project Name}

## Goal

{One-sentence goal from Step 1}

## Inputs

{Description of data/inputs from Step 1}

## Research Questions / Key Questions

<!-- Add 3–5 key questions this project needs to answer -->

## Success Criteria

<!-- What does a successful outcome look like? What decisions will this inform? -->

## Constraints and Considerations

<!-- Timeline, confidentiality, language, sample size, or anything the orchestrator should know -->
```

If `00-brief/project-brief.md` already exists, do not overwrite it — report that it already exists and skip this step.

### Step 4: Print next-steps checklist

```
Project initialised. Here's what to do next:

  1. Complete 00-brief/project-brief.md
     — Fill in Research Questions, Success Criteria, and Constraints

  2. Add your source data
     — Place input files in 03-inputs/
     — Follow the naming conventions in .claude/rules/directory-and-naming-conventions.md

  3. Create your first workflow
     — Run /add-workflow to scaffold a directive and orchestration file

  4. Check project status at any time
     — Run /status to see which outputs exist and what may need attention
```
