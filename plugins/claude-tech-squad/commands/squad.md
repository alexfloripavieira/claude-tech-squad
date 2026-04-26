---
description: Run the full claude-tech-squad delivery pipeline (discovery → blueprint → TDD implementation → quality → docs → release).
argument-hint: Optional feature description or ticket reference
allowed-tools: ["Read", "Skill"]
---

# /squad

Invoke the `claude-tech-squad:squad` skill to run the end-to-end delivery pipeline with the full specialist bench.

When the user runs this command, immediately invoke the `claude-tech-squad:squad` skill via the Skill tool with the user's feature description as input. Do not paraphrase or pre-process the request — pass it through.

If no argument is provided, ask the user for the feature description before invoking the skill.
