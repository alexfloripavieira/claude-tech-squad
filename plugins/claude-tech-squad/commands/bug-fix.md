---
description: Resolve a bug with the claude-tech-squad bug-fix workflow (root cause investigation, failing test, fix, validation).
argument-hint: Bug description, error message, or stack trace
allowed-tools: ["Read", "Skill"]
---

# /bug-fix

Invoke the `claude-tech-squad:bug-fix` skill to resolve a defect using the focused TDD-driven bug fix workflow.

When the user runs this command, immediately invoke the `claude-tech-squad:bug-fix` skill via the Skill tool with the user's bug report as input. Do not pre-process or hypothesize before the skill runs — it owns root cause investigation.

If no argument is provided, ask the user for the bug report (error message, stack trace, or reproduction steps) before invoking the skill.
