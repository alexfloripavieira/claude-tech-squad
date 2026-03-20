---
name: pre-commit-lint
description: Configures a PreToolUse hook that auto-fixes staged files with project lint tools (ruff, eslint, etc.) before any git commit, so pre-commit checks never block Claude's commits.
---

# /pre-commit-lint — Auto-fix Lint Before Commits

Detects the project's lint tools from `.pre-commit-config.yaml` (or package.json/pyproject.toml) and installs a `PreToolUse` Bash hook in `.claude/settings.json` that runs auto-fix on staged files before every `git commit`.

## What This Skill Does

1. Reads `.pre-commit-config.yaml` (and fallbacks) to discover which lint tools are configured
2. Reads `.claude/settings.json` to avoid duplicate hooks
3. Writes a `PreToolUse` Bash hook that intercepts `git commit` and auto-fixes staged files
4. Re-stages the fixed files so the original commit proceeds cleanly

## Execution

Follow these steps exactly:

### Step 1 — Discover lint tools

Read `.pre-commit-config.yaml` if it exists. Identify which of these are present:
- `ruff` or `ruff-format` → Python lint/format via ruff
- `flake8` → Python lint (no auto-fix, skip)
- `black` → Python format via black
- `isort` → Python import sorting via isort
- `eslint` → JavaScript/TypeScript via eslint --fix
- `prettier` → JS/TS/CSS/JSON via prettier --write

If `.pre-commit-config.yaml` does not exist, check:
- `pyproject.toml` for `[tool.ruff]` → ruff
- `package.json` for `eslint` or `prettier` dependencies

### Step 2 — Determine tool paths and file globs

For each detected tool, determine:
- The executable path (check `$HOME/.local/bin/`, `./node_modules/.bin/`, global PATH)
- Which file types and directories it targets (from the pre-commit config `files:` and `types_or:` fields)

### Step 3 — Read existing settings

Read `.claude/settings.json`. If a `PreToolUse` hook with matcher `Bash` already exists and contains `git commit`, show the existing command and ask: keep it, replace it, or add alongside.

### Step 4 — Build the hook command

Construct a single shell command that:
1. Reads the Bash command from stdin via `jq -r '.tool_input.command // ""'`
2. Exits 0 immediately if the command does not match `git commit`
3. For each detected tool: gets staged files matching the tool's glob, runs auto-fix, re-stages with `git add`
4. Exits 0 (never blocks the commit — only fixes)

**Template for ruff:**
```bash
INPUT=$(cat); CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""'); if ! echo "$CMD" | grep -qE 'git[[:space:]]+commit'; then exit 0; fi; RUFF="$HOME/.local/bin/ruff"; if [[ ! -x "$RUFF" ]]; then exit 0; fi; STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep -E '<FILES_PATTERN>'); if [[ -z "$STAGED" ]]; then exit 0; fi; while IFS= read -r f; do [[ -f "$f" ]] && $RUFF check --fix --quiet "$f" 2>/dev/null; $RUFF format --quiet "$f" 2>/dev/null; git add "$f"; done <<< "$STAGED"; exit 0
```

Replace `<FILES_PATTERN>` with the appropriate grep pattern (e.g., `'^django/.*\.py$'` for ruff targeting `^django/`).

If multiple tools are detected, combine their fix steps in sequence within the same hook command.

### Step 5 — Pipe-test the command

Before writing to settings.json, pipe-test the raw command:
```bash
echo '{"tool_input":{"command":"git commit -m test"}}' | <hook-command>
```
Confirm exit code 0 and that ruff (or other tools) ran against staged files (or were skipped gracefully with no staged files).

### Step 6 — Write to settings.json

Merge the hook into `.claude/settings.json` under `hooks.PreToolUse`. Preserve all existing settings.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "<the-built-command>",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Step 7 — Validate JSON syntax

Run:
```bash
jq -e '.hooks.PreToolUse[] | select(.matcher == "Bash") | .hooks[] | .command' .claude/settings.json
```
Exit 0 = correct. Fix any malformation before finishing.

### Step 8 — Report

Tell the user:
- Which tools were detected and configured
- Which file patterns are covered
- That the hook will auto-fix and re-stage before every `git commit` from Claude
- To open `/hooks` or restart Claude Code if the hook does not fire immediately (settings watcher may need a reload)
