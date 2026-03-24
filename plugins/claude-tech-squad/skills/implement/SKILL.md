---
name: implement
description: Run build and quality for any software project based on a prior discovery document. Supports a full specialist bench across implementation, quality, operations, and delivery artifacts.
---

# /implement — Build & Quality

Run implementation and quality validation using the Discovery & Blueprint Document produced by `/discovery`.

## TDD Execution Rule

If the discovery package came from `/squad`, or if the package explicitly marks TDD as required, treat TDD as mandatory for code changes.

That means:

- implementation starts from failing tests, not from direct production code edits
- the TDD Delivery Plan becomes the default execution sequence
- exceptions must be stated explicitly when the repository or task makes tests-first execution impossible

## Operator Visibility Contract

This workflow must expose the build and quality orchestration in the terminal output.

For every agent handoff, emit these plain-text progress lines:

- `[Phase Start] <phase-name>`
- `[Agent Start] <role> | <subagent_type> | <objective>`
- `[Agent Done] <role> | Status: completed | Output: <one-line summary>`
- `[Agent Blocked] <role> | Waiting on: <missing input, failing check, or user decision>`

When multiple implementation or quality agents run in parallel, emit:

- `[Agent Batch Start] <phase-name> | Agents: <comma-separated roles>`
- one `Agent Start` / `Agent Done` line per agent
- `[Agent Batch Done] <phase-name> | Outcome: <one-line summary>`

Also emit explicit retry lines when a loop occurs:

- `[Agent Retry] <role> | Reason: <review or validation failure>`

Do not silently move from build to quality, or from one agent to another, without these lines.

## Required Input

This command expects:

- PM output
- Business Analyst output
- PO output
- Planner output
- Overall architecture
- Tech Lead execution plan
- Relevant specialist notes
- Design principles guardrails
- Quality and operations baselines
- Test plan
- TDD delivery plan

If the discovery document is not already available in the conversation, ask the user to provide it.

---

## Execution

### Step 1 — Validate Blueprint
Ensure a Discovery & Blueprint Document exists (from `/discovery` or provided by user). If not present, ask the user to run `/discovery` first or provide the blueprint.

### Step 2 — Start the Build Chain
Invoke Tech Lead using the Agent tool with `subagent_type: "claude-tech-squad:techlead"`:

```
## Implement Start

### Blueprint
{{full_blueprint_document}}

### Architecture package
{{architecture_decisions}}

### Test Plan
{{test_plan}}

### TDD Delivery Plan
{{tdd_delivery_plan}}

---
Mode: BUILD. Coordinate the full implementation chain:
1. Call TDD Specialist to produce failing tests
2. Launch implementation agents in parallel (backend-dev, frontend-dev, etc.)
3. Each implementation agent will call Reviewer when done
4. Reviewer will call QA when approved
5. QA will call you when tests pass
6. You then launch quality review bench in parallel
7. After quality reviews, chain continues: docs-writer → jira-confluence → pm (UAT gate)
```

### Step 3 — UAT Gate
The chain will pause at PM UAT for your approval. Review the UAT report and approve or provide feedback.

### Step 4 — Release (for /squad only)
After UAT approval, invoke Release and SRE for release sign-off.

---

## Output: Implementation Report

```
## Implementation Complete

### Agent Execution Log
- Phase: [...]
- Role: [...] | Subagent: [...] | Status: [...] | Output: [...]
- Role: [...] | Subagent: [...] | Status: [...] | Output: [...]

### Build
- Workstreams executed: [...]
- Files changed: [...]
- Tech lead coordination: completed
- Design guardrails: completed / refreshed
- TDD cycle plan: completed / refreshed
- Delivery mode: TDD-first / exception declared
- Review status: APPROVED / CHANGES REQUESTED
- Continuous quality: PASS / FAIL

### Quality
- QA full validation: PASS / FAIL
- Integration QA: PASS / FAIL
- Specialist reviews: [summary]
- Documentation delta: [summary]
- Jira / Confluence pack: [summary]
- UAT: APPROVED / REJECTED

### Evidence
- Tests / commands run: [...]
- Acceptance criteria validated: [...]
- Outstanding issues: [...]
```
