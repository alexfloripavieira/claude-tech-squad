---
name: pre-commit-lint
description: Configures a PreToolUse hook that auto-fixes staged files with project lint tools (ruff, black, isort, eslint, prettier) before any git commit, and validates sonar rules and PEP compliance so pre-commit checks never block Claude's commits.
---

# /pre-commit-lint — Auto-fix Lint Before Commits

## Global Safety Contract

**This contract applies to every operation in this workflow. Violating it requires explicit written user confirmation.**

This skill must never:
- Generate a hook that passes `--no-verify` to git commands — doing so defeats the purpose of pre-commit safety
- Modify `.git/hooks/` directly — always use `.claude/settings.json` hooks
- Auto-fix changes that alter the semantic behavior of code (only formatting and lint are permitted)
- Remove existing hook configurations without showing the user what will be removed

If any operation requires bypassing these constraints, STOP and surface the decision to the user before proceeding.

Detects the project's lint tools from `.pre-commit-config.yaml` (or `pyproject.toml`/`package.json`) and installs a `PreToolUse` Bash hook in `.claude/settings.json` that runs auto-fix on staged files before every `git commit`.

## What This Skill Does

1. Reads `.pre-commit-config.yaml` (and fallbacks) to discover which lint tools are configured
2. Reads `.claude/settings.json` to avoid duplicate hooks
3. Writes a `PreToolUse` Bash hook that intercepts `git commit` and auto-fixes staged files
4. Re-stages the fixed files so the original commit proceeds cleanly

## Execution

Follow these steps exactly:

### Step 1 — Discover lint tools

Read `.pre-commit-config.yaml` if it exists. Identify which of these are present:
- `ruff` or `ruff-format` → Python lint + format via ruff (covers PEP 8, PEP 257 style, unused imports, complexity, security)
- `flake8` → Python lint (no auto-fix, report only)
- `black` → Python format via black
- `isort` → Python import sorting via isort
- `mypy` → Python type checking (no auto-fix, report only)
- `eslint` → JavaScript/TypeScript via eslint --fix
- `prettier` → JS/TS/CSS/JSON via prettier --write

If `.pre-commit-config.yaml` does not exist, check:
- `pyproject.toml` for `[tool.ruff]`, `[tool.black]`, `[tool.isort]` → respective tools
- `package.json` for `eslint` or `prettier` dependencies

### Step 2 — Determine ruff rule coverage

When ruff is present, check `pyproject.toml` for `[tool.ruff.lint]` select rules. Recommend enabling at minimum:

```toml
[tool.ruff.lint]
select = [
  "E",   # pycodestyle errors (PEP 8)
  "W",   # pycodestyle warnings
  "F",   # pyflakes (undefined names, unused imports)
  "I",   # isort (import order)
  "N",   # pep8-naming
  "UP",  # pyupgrade (modern Python syntax)
  "B",   # flake8-bugbear (common bugs and design issues)
  "C90", # mccabe complexity
  "S",   # flake8-bandit (security — maps to SonarQube security hotspots)
  "SIM", # flake8-simplify (dead code, redundant conditions)
  "RUF", # ruff-specific rules
]
```

These rules together cover: PEP 8, PEP 257 style, unused imports, naming conventions, cognitive complexity, security hotspots (hardcoded passwords, SQL injection patterns), and dead code — equivalent to a SonarQube Python analysis.

### Step 3 — Determine tool paths and file globs

For each detected tool, determine:
- The executable path (check `$HOME/.local/bin/`, `./node_modules/.bin/`, global PATH, Poetry venv)
- Which file types and directories it targets (from the pre-commit config `files:` and `types_or:` fields)

### Step 4 — Read existing settings

Read `.claude/settings.json`. If a `PreToolUse` hook with matcher `Bash` already exists and contains `git commit`, show the existing command and ask: keep it, replace it, or add alongside.

### Step 5 — Build the hook command

Construct a single shell command that:
1. Reads the Bash command from stdin via `jq -r '.tool_input.command // ""'`
2. Exits 0 immediately if the command does not match `git commit`
3. For each detected tool: gets staged files matching the tool's glob, runs auto-fix, re-stages with `git add`
4. For report-only tools (flake8, mypy): runs check and prints warnings but does not block (exit 0)
5. Exits 0 (never blocks the commit — only fixes and reports)

**Template for ruff (Python):**
```bash
INPUT=$(cat); CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""'); if ! echo "$CMD" | grep -qE 'git[[:space:]]+commit'; then exit 0; fi; RUFF="$HOME/.local/bin/ruff"; if [[ ! -x "$RUFF" ]]; then exit 0; fi; STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep -E '<FILES_PATTERN>'); if [[ -z "$STAGED" ]]; then exit 0; fi; while IFS= read -r f; do [[ -f "$f" ]] && $RUFF check --fix --quiet "$f" 2>/dev/null; $RUFF format --quiet "$f" 2>/dev/null; git add "$f"; done <<< "$STAGED"; exit 0
```

Replace `<FILES_PATTERN>` with the appropriate grep pattern (e.g., `'\.py$'`).

**Template for black + isort (Python, if ruff not present):**
```bash
...; BLACK=$(command -v black); ISORT=$(command -v isort); while IFS= read -r f; do [[ -f "$f" ]] && $ISORT --quiet "$f" 2>/dev/null && $BLACK --quiet "$f" 2>/dev/null; git add "$f"; done <<< "$STAGED"; exit 0
```

If multiple tools are detected, combine their fix steps in sequence within the same hook command.

### Step 6 — Pipe-test the command

Before writing to settings.json, pipe-test the raw command:
```bash
echo '{"tool_input":{"command":"git commit -m test"}}' | <hook-command>
```
Confirm exit code 0 and that the tools ran against staged files (or were skipped gracefully with no staged files).

### Step 7 — Write to settings.json

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

### Step 8 — Validate JSON syntax

Run:
```bash
jq -e '.hooks.PreToolUse[] | select(.matcher == "Bash") | .hooks[] | .command' .claude/settings.json
```
Exit 0 = correct. Fix any malformation before finishing.

### Step 9 — Report

Tell the user:
- Which tools were detected and configured
- Which ruff rule groups are active (and which SonarQube-equivalent coverage they provide)
- Which file patterns are covered
- That the hook will auto-fix and re-stage before every `git commit` from Claude
- Any report-only tools (mypy, flake8) and what they check
- To open `/hooks` or restart Claude Code if the hook does not fire immediately
