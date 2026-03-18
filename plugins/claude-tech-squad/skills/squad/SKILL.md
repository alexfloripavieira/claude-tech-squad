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

## Phase 1: Discovery

Follow the exact `/discovery` process:

1. Repository recon
2. PM first pass
3. Business analysis
4. PO prioritization
5. User answers product and domain questions
6. Planner feasibility
7. User resolves feasibility tradeoffs

Do not proceed until requirements are confirmed.

---

## Phase 2: Blueprint

Follow the exact `/discovery` blueprint process:

1. Overall Architect
2. Tech Lead execution plan
3. User resolves overall design questions
4. Relevant specialist design agents
5. User resolves specialist design questions if any
6. Design Principles Specialist
7. Test Planner
8. TDD Specialist
9. Quality, governance, and operations baselines
10. User confirms the final blueprint

Do not proceed until the user explicitly confirms the blueprint, including the TDD-first delivery approach for code changes.

---

## Phase 3: Build

Follow the exact `/implement` build process:

1. Run Tech Lead coordination
2. Run Design Principles Specialist guardrail planning
3. Run TDD Specialist cycle planning
4. Run relevant implementation agents:
   - `claude-tech-squad:backend-dev`
   - `claude-tech-squad:frontend-dev`
   - `claude-tech-squad:platform-dev`
   - `claude-tech-squad:integration-engineer`
   - `claude-tech-squad:ai-engineer`
   - `claude-tech-squad:devops`
   - `claude-tech-squad:ci-cd`
   - `claude-tech-squad:dba`
5. Run Design Principles Specialist structural review
6. Run `claude-tech-squad:reviewer`
7. Run continuous quality agents
8. Loop on build issues until approved or blocked

Additional `/squad` rule:

- treat tests-first execution as mandatory for code changes
- if an implementation agent starts without a failing-test target, send the work back through the TDD Specialist first
- make any TDD exception visible in the `Agent Execution Log`

---

## Phase 4: Quality

Follow the exact `/implement` quality process:

1. Full QA and integration validation
2. Specialist quality reviews
3. Documentation and Jira/Confluence updates
4. PM UAT
5. Loop on critical issues until approved or blocked

---

## Phase 5: Release

### Step 5.1: Release Plan

Use the Agent tool with `subagent_type: "claude-tech-squad:release"`.

Prompt:
```
You are the Release agent.

Review the implemented change set and prepare a release plan.

Use the architecture package, QA reports, specialist reviews, docs update plan, Jira / Confluence pack, and UAT result as inputs.

MANDATORY:
- Validate CI/CD and deployment tooling against current docs when relevant
- Inventory env vars, migrations, breaking changes, and rollback steps
- Produce a concrete release plan
```

### Step 5.2: Reliability Sign-Off

Use the Agent tool with `subagent_type: "claude-tech-squad:sre"`.

Prompt:
```
You are the SRE agent.

Review the release plan, observability findings, performance review, and operational changes.

Produce reliability guardrails, rollout advice, and rollback concerns.
```

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
