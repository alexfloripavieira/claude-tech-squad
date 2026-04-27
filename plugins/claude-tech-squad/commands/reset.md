---
description: Restore all agents to active (equivalent to the 'full' profile).
argument-hint: (no arguments)
allowed-tools: ["Bash", "Read", "Write"]
---

# /claude-tech-squad:reset

Move every disabled agent back to the active directory and clear all profile/override settings.

## What this does

1. Confirms with user: "This will set the profile to 'full' and re-enable all 81 agents. Continue?"
2. Updates `.claude-tech-squad.yml` to:
   ```yaml
   profile: full
   overrides:
     enable: []
     disable: []
   ```
   (Or deletes the file if user prefers — ask which.)
3. Runs `${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py -v`.
4. Prints: "✓ All 81 agents active. Removed any project-level disable overrides."

## Arguments

None.

## When to use

- You want to temporarily access every agent for an exotic task.
- Profile drift made the active set incoherent.
- Onboarding to a new repo and want defaults before running `/claude-tech-squad:setup`.
