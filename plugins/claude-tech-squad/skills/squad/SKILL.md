---
name: squad
description: Run the full technology squad workflow end-to-end with the full specialist bench: discovery, blueprint, design-principles and TDD-first implementation, quality, documentation, Jira/Confluence, reliability, and release preparation.
---

# /squad — Full Technology Squad

Run the complete workflow with the full technology squad. This command is best when the user wants end-to-end delivery, but discovery and blueprint remain interactive for the decisions that require user input.

## Core Principle

Do not assume the stack, the conventions, or the product domain. Discover them from the repository and validate technical decisions against current documentation.

## TDD Default Mode

When `/squad` is used for work that changes code, TDD is the default development strategy.

That means:

- do not start implementation before the Test Plan and TDD Delivery Plan are both ready
- implementation agents should begin from failing tests whenever the repository has a viable test stack
- use red-green-refactor cycles as the normal execution model, not as an optional extra

TDD may be relaxed only when one of these is true:

- the task is documentation-only, release-only, or otherwise non-code
- the current repository genuinely has no viable automated test path for the slice
- an external constraint makes tests-first impossible for a specific step

If TDD is relaxed, the workflow must say so explicitly in the output and explain why.

## Operator Visibility Contract

This end-to-end workflow must surface the squad orchestration in the terminal output, even when the UI does not show each tool call separately.

For the full run, emit these plain-text progress lines:

- `[Phase Start] <phase-name>`
- `[Agent Start] <role> | <subagent_type> | <objective>`
- `[Agent Done] <role> | Status: completed | Output: <one-line summary>`
- `[Agent Blocked] <role> | Waiting on: <missing input or approval>`
- `[Agent Retry] <role> | Reason: <review or validation failure>`

When a set of specialists is run in parallel, emit:

- `[Agent Batch Start] <phase-name> | Agents: <comma-separated roles>`
- one `Agent Start` / `Agent Done` line per agent
- `[Agent Batch Done] <phase-name> | Outcome: <one-line summary>`

Maintain an `Agent Execution Log` throughout the workflow and include it in the final output.

---

## Execution

### Step 1 — Discovery Chain
Follow the same execution as `/discovery`. The chain runs: PM → BA → PO [Gate] → Planner [Gate] → Architect → TechLead [Gate] → Specialists → Design Principles → Test Planner → TDD Specialist [Final Gate].

### Step 2 — Build Chain
After you confirm the blueprint, Tech Lead starts the build chain: TDD Specialist → Implementation batch → Reviewer → QA → Quality bench → Docs → Jira/Confluence → PM [UAT Gate].

### Step 3 — Release Chain
After UAT approval, invoke Release using the Agent tool with `subagent_type: "claude-tech-squad:release"` with the full delivery package. Release will call SRE for final reliability sign-off.

### Step 4 — SRE Sign-off
After Release, invoke SRE using the Agent tool with `subagent_type: "claude-tech-squad:sre"` for final go/no-go.

---

## Final Output

```
## Squad Complete

### Agent Execution Log
- Phase: [...]
- Role: [...] | Subagent: [...] | Status: [...] | Output: [...]
- Role: [...] | Subagent: [...] | Status: [...] | Output: [...]

### Product
- User story: [...]
- Acceptance criteria: [...]
- Release slice: [...]

### Architecture
- Overall design: [...]
- Tech lead plan: completed
- Specialist notes: [summary]
- Design guardrails: completed
- Quality baselines: completed
- Test plan: completed
- TDD delivery plan: completed

### Delivery
- Workstreams executed: [...]
- Delivery mode: TDD-first / exception declared
- Review: APPROVED / CHANGES REQUESTED
- Continuous quality: PASS / FAIL
- Full QA: PASS / FAIL
- Specialist reviews: [summary]
- Docs: updated / plan produced
- Jira / Confluence: updated / pack produced
- UAT: APPROVED / REJECTED

### Release
- Release plan: completed
- SRE sign-off: completed
- Breaking changes: [...]
- Rollback plan: defined

### Stack Validation
- Docs checked via context7 for: [...]
```
