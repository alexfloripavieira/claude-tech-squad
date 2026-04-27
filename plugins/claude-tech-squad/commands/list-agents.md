---
description: List which agents are active and which are disabled in the current profile.
argument-hint: (no arguments)
allowed-tools: ["Bash", "Read"]
---

# /claude-tech-squad:list-agents

Show the current agent roster — active vs. disabled — for this project.

## What this does

1. Reads `.claude-tech-squad.yml` at project root (or reports "no config — full mode, all 81 agents active").
2. Lists files in `${CLAUDE_PLUGIN_ROOT}/agents/*.md` (active) and `${CLAUDE_PLUGIN_ROOT}/agents/.disabled/*.md` (disabled).
3. Reads the state from `${CLAUDE_PLUGIN_ROOT}/.state/reconcile.json` if present.
4. Prints a structured report:

```
Profile: django-react-ai
Active (38 agents):
  ai-engineer, architect, backend-architect, ...

Disabled (43 agents):
  agent-architect, analytics-engineer, api-designer, ...

Token budget: ~7.8k (vs. ~17k for full mode)
Config: /home/alex/a1/.claude-tech-squad.yml
```

## Arguments

None.
