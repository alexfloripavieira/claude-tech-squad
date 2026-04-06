# Agent Contract

Every agent file in `plugins/claude-tech-squad/agents/` must implement this contract. An agent that omits any required section is structurally incomplete and will be rejected by `scripts/validate.sh`.

---

## File location and naming

```
plugins/claude-tech-squad/agents/<role-slug>.md
```

Examples: `pm.md`, `backend-dev.md`, `security-reviewer.md`

---

## Required frontmatter

```yaml
---
name: <role-slug>
description: <one-line description of what this agent does and when it is invoked>
---
```

Optional field for agents that need tool access:

```yaml
tools:
  - Bash
  - Read
  - Glob
  - Grep
```

---

## Required sections

### 1. Role heading and ownership statement

```markdown
# <Role Name> Agent

You own <one-sentence scope>.
```

The ownership statement must be specific. "You do everything" is not valid.

### 2. Rules

A focused list of behavioral constraints specific to this role. These are the non-negotiable operating rules for this agent.

### 3. Handoff Protocol

Every agent returns output to the orchestrator in a defined format. This section specifies that format as a markdown code block with labeled fields.

Example:

```
## Output from <Role Name>

### <Section A>
{{field_a}}

### <Section B>
{{field_b}}
```

### 4. Result Contract

**Mandatory. A response without this block is structurally incomplete.**

Always placed at the end of the response:

```yaml
result_contract:
  status: completed | needs_input | blocked | failed
  confidence: high | medium | low
  blockers: []
  artifacts: []
  findings: []
  next_action: "..."
```

Rules for filling the contract:
- Use empty lists `[]` when there are no blockers, artifacts, or findings.
- `next_action` must name the single most useful downstream step.
- `status: blocked` requires at least one entry in `blockers`.
- A response missing `result_contract` is treated as a retry trigger.

### 5. Documentation Standard

Every agent includes this block verbatim. It governs how agents look up library and framework documentation.

```markdown
## Documentation Standard — Context7 First, Repository Fallback

Before using **any** library, framework, or external API — regardless of stack — use Context7 when it is available. If Context7 is unavailable, fall back to repository evidence, installed local docs, and explicit assumptions in your output. Training data alone is never the source of truth for API signatures or default behavior.

**Required workflow for every library or API used:**

1. Resolve the library ID:
   mcp__plugin_context7_context7__resolve-library-id("library-name")
2. Query the relevant docs:
   mcp__plugin_context7_context7__query-docs(context7CompatibleLibraryID, topic="specific feature or method")

**If Context7 is unavailable or does not have documentation for the library:** note it explicitly and proceed with caution, flagging assumptions in your output.
```

---

## Conditional sections

### Absolute Prohibitions (required for agents with execution authority)

Agents that can execute commands, write code, make git operations, or interact with infrastructure must include this section.

```markdown
## Absolute Prohibitions

**NEVER execute or suggest any of these without explicit written user confirmation:**

- [action 1 specific to this role]
- [action 2 specific to this role]
- ...

**If a task seems to require any of the above:** STOP. Explain the risk and ask the user explicitly.
```

Agents that require this section: `backend-dev`, `frontend-dev`, `mobile-dev`, `data-engineer`, `devops`, `ci-cd`, `dba`, `platform-dev`, `cloud-architect`, `release`, `sre`, `incident-manager`.

Agents that do not require this section: pure analysis roles (`pm`, `business-analyst`, `architect`, `reviewer`, `qa`, `security-reviewer`, etc.) — they produce findings and recommendations, but do not execute.

### Architecture Guardrails (for implementation agents)

Agents that write code include guardrails for the supported architecture styles: hexagonal, layered, or repo-native. These guardrails enforce layer boundaries and import rules.

### TDD Mandate (for implementation agents)

Agents that write production code include a TDD mandate: tests are written first, implementation code follows. The mandate specifies the red-green-refactor order per architecture style.

---

## Boundary text

Every agent must be readable in isolation and answer two questions without requiring context from other files:

1. What does this agent do?
2. What does this agent NOT do?

When two agents have adjacent responsibilities (e.g., `security-reviewer` vs `security-engineer`, `docs-writer` vs `tech-writer`), each agent must explicitly state the boundary.

Example from the split between `docs-writer` and `tech-writer`:
- `docs-writer` → internal developer and operator documentation
- `tech-writer` → external user guides, public API references, customer changelogs

---

## What makes an agent invalid

| Problem | Effect |
|---|---|
| Missing `result_contract` | Treated as a retry trigger; breaks SEP log |
| Missing `Documentation Standard` | Agent may silently use stale training data for API signatures |
| Execution agent without `Absolute Prohibitions` | Rejected by `validate.sh` |
| Ownership statement too broad | Overlaps with other agents; breaks the specialist model |
| No handoff format defined | Orchestrator cannot parse output; breaks the chain |
