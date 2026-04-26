---
description: Run the claude-tech-squad emergency hotfix workflow (skip discovery, go straight to root cause, minimal patch, hotfix branch, deploy checklist).
argument-hint: Production incident description or error
allowed-tools: ["Read", "Skill"]
---

# /hotfix

Invoke the `claude-tech-squad:hotfix` skill for production-impacting issues that require an emergency fix.

When the user runs this command, immediately invoke the `claude-tech-squad:hotfix` skill via the Skill tool with the user's incident description as input. Do not delay with planning — the skill is designed for emergency cadence.

If no argument is provided, ask the user for the incident description before invoking the skill.
