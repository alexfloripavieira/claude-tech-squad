---
description: Detect repo stack and pick an agent profile to keep only relevant agents loaded.
argument-hint: (optional profile name to skip detection)
allowed-tools: ["Bash", "Read", "Write", "Edit"]
---

# /claude-tech-squad:setup

Configure which subset of the 81 squad agents loads in this repo, based on the project's actual stack.

## What this does

1. Runs `${CLAUDE_PLUGIN_ROOT}/scripts/detect-stack.sh` to read repo signals (Django, React, Vue, TypeScript, RN, Flutter, dbt, AI/RAG, etc.).
2. Loads every profile in `${CLAUDE_PLUGIN_ROOT}/profiles/*.yml` and scores each one against the detected tags.
3. Suggests the highest-scoring profile, with the agent count and the matched signals.
4. Asks the user to confirm or pick another profile (including `full` to keep all 81 agents, or `minimal`).
5. Writes `.claude-tech-squad.yml` in the project root (or updates an existing one).
6. Runs `${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py -v` to physically move non-profile agents to `agents/.disabled/` inside the plugin cache.
7. Prints a summary: profile chosen, active vs disabled count, approximate token budget freed.

## Arguments

- `$1` (optional): profile name. If provided, skip auto-detection and apply directly. Useful for CI: `/claude-tech-squad:setup django-react`.

## Flow

```
1. Run detect-stack.sh, capture tags
2. Load profile files; for each profile, count detection-rule hits vs. detected tags
3. Show top-3 ranked profiles with agent count + matched signals
4. Wait for user choice (or accept top suggestion if argument supplied)
5. Build YAML body:
     profile: <chosen>
     overrides:
       enable: []
       disable: []
6. Write .claude-tech-squad.yml at project root
7. Invoke reconcile.py to move agents
8. Print: "Profile X applied — N active, M disabled. Commit .claude-tech-squad.yml so the team shares the same config."
```

## After running

- Commit the `.claude-tech-squad.yml` file to share the profile across the team.
- Re-run `/claude-tech-squad:setup` any time you want to change profiles.
- Use `/claude-tech-squad:enable <agent>` or `/claude-tech-squad:disable <agent>` for granular tweaks.
- The `SessionStart` hook re-applies the profile on every Claude Code session, so plugin auto-updates won't undo it.
