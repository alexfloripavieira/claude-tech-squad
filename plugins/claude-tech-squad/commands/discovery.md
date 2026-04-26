---
description: Run claude-tech-squad discovery and blueprint with the planning specialist bench (PM, PO, BA, architects, test-planner, tdd-specialist).
argument-hint: Optional feature or epic description
allowed-tools: ["Read", "Skill"]
---

# /discovery

Invoke the `claude-tech-squad:discovery` skill to plan a feature before implementation.

When the user runs this command, immediately invoke the `claude-tech-squad:discovery` skill via the Skill tool with the user's input. Do not pre-process the request.

If no argument is provided, ask the user what they want planned before invoking the skill.
