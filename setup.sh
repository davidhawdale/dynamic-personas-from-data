#!/usr/bin/env bash
# Bootstrap the project workspace directory structure.
# Run from the project root: bash setup.sh
#
# Creates all required directories and configuration files.
# Safe to re-run: skips files that already exist.

set -euo pipefail

# --- Directories ---

dirs=(
  "00-brief"
  "01-directives"
  "02-workflows"
  "02-workflows/shared"
  "03-inputs"
  "04-process/translated"
  "04-process/extracts"
  "05-outputs"
  "10-resources/templates"
  ".tmp"
  ".claude/agents"
  ".claude/rules"
  ".claude/skills"
)

for dir in "${dirs[@]}"; do
  mkdir -p "$dir"
done

echo "Directories created."

# --- .claude/settings.json ---

if [ ! -f ".claude/settings.json" ]; then
  cat > ".claude/settings.json" << 'SETTINGS'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "permissions": {
    "allow": ["Bash", "Write", "Edit"],
    "deny": []
  }
}
SETTINGS
  echo "Created .claude/settings.json"
else
  echo "Skipped .claude/settings.json (already exists)"
fi

# --- .env (symlink to master or placeholder) ---

if [ ! -f ".env" ] && [ ! -L ".env" ]; then
  if [ -f "${HOME}/.agent-project.env" ]; then
    ln -s "${HOME}/.agent-project.env" ".env"
    echo "Created .env → symlink to ~/.agent-project.env"
  else
    cat > ".env" << 'ENV'
# Environment variables and API keys
# Store your keys in ~/.agent-project.env and re-run setup.sh to auto-symlink,
# or fill them in here.
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
# GOOGLE_API_KEY=
ENV
    echo "Created .env placeholder (tip: store keys in ~/.agent-project.env for auto-linking)"
  fi
else
  echo "Skipped .env (already exists)"
fi

# --- Done ---

echo ""
echo "Setup complete. Project structure is ready."
