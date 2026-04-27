---
description: Disable an agent from the current profile to free token budget.
argument-hint: <agent-name>
allowed-tools: ["Bash", "Read", "Edit", "Write"]
---

# /claude-tech-squad:disable

Remove a single agent from the active set without changing the underlying profile.

## What this does

1. Reads `.claude-tech-squad.yml` at project root (errors if missing — suggest `/claude-tech-squad:setup` first).
2. Adds `$1` to `overrides.disable` (deduped). If `$1` is in `overrides.enable`, removes it from there.
3. Validates that an agent file `agents/$1.md` exists. Errors with the closest-name suggestion if not.
4. Runs `${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py -v` to move the agent file from `agents/` to `agents/.disabled/`.
5. Confirms: "✓ Disabled <agent>. Commit .claude-tech-squad.yml to share with the team."

## Arguments

- `$1` (required): the agent name (e.g. `jira-confluence-specialist`).

## Examples

```
/claude-tech-squad:disable jira-confluence-specialist
/claude-tech-squad:disable solutions-architect
```
