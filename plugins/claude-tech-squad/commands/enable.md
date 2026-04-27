---
description: Enable an agent that is outside the current profile.
argument-hint: <agent-name>
allowed-tools: ["Bash", "Read", "Edit", "Write"]
---

# /claude-tech-squad:enable

Add a single agent to the active set without changing the underlying profile.

## What this does

1. Reads `.claude-tech-squad.yml` at project root (errors if missing — tell user to run `/claude-tech-squad:setup` first).
2. Adds `$1` to `overrides.enable` (deduped). If `$1` is in `overrides.disable`, removes it from there.
3. Validates that an agent file `agents/$1.md` exists in `${CLAUDE_PLUGIN_ROOT}/agents/` or `${CLAUDE_PLUGIN_ROOT}/agents/.disabled/`. Errors with the closest-name suggestion if not.
4. Runs `${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py -v` to move the agent file from `.disabled/` back to `agents/`.
5. Confirms: "✓ Enabled <agent>. Commit .claude-tech-squad.yml to share with the team."

## Arguments

- `$1` (required): the agent name (e.g. `mobile-dev`, not `mobile-dev.md`).

## Examples

```
/claude-tech-squad:enable mobile-dev
/claude-tech-squad:enable llm-safety-reviewer
```
