---
description: List available agent profiles with descriptions and agent counts.
argument-hint: (no arguments)
allowed-tools: ["Bash", "Read"]
---

# /claude-tech-squad:profiles

Show every available profile shipped with the plugin.

## What this does

1. Reads each `.yml` file in `${CLAUDE_PLUGIN_ROOT}/profiles/`.
2. Extracts `name`, `description`, and `agents` count for each.
3. Marks the currently active profile (from `.claude-tech-squad.yml`) with `*`.
4. Prints a table:

```
PROFILE              AGENTS  DESCRIPTION
* django-react-ai    38      Django + React with LLM/RAG features
  django-react       32      Django backend + React frontend
  vue-typescript     28      Vue 3 + TypeScript frontend with Node/API backend
  react-typescript   28      React + TypeScript frontend with Node/API backend
  python-backend     28      Python backend (FastAPI/Flask/non-Django)
  mobile-fullstack   28      Mobile app (RN or Flutter) with backend
  data-platform      26      Data engineering, ETL, warehouse, analytics
  minimal            14      Smallest viable squad
  full               81      All agents (default)

To switch:    /claude-tech-squad:setup <profile-name>
For overrides: /claude-tech-squad:enable / disable <agent-name>
```

## Arguments

None.
