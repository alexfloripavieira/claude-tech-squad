---
description: Review a pull request with the full claude-tech-squad specialist bench (reviewer, security, privacy, performance, accessibility) and post inline comments.
argument-hint: PR number or URL
allowed-tools: ["Read", "Skill"]
---

# /pr-review

Invoke the `claude-tech-squad:pr-review` skill to run a multi-lens review on a pull request.

When the user runs this command, immediately invoke the `claude-tech-squad:pr-review` skill via the Skill tool with the user's PR reference as input.

If no argument is provided, ask the user for the PR number or URL before invoking the skill.
