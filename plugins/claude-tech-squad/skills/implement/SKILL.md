---
name: implement
description: Run build and quality for any software project based on a prior discovery document. Supports a full specialist bench across implementation, quality, operations, and delivery artifacts.
---

# /implement — Build & Quality

Run implementation and quality validation using the Discovery & Blueprint Document produced by `/discovery`.
Each specialist runs as an independent teammate in its own tmux pane.

## TDD Execution Rule

If the discovery package came from `/squad`, or if the package explicitly marks TDD as required, treat TDD as mandatory:

- Implementation starts from failing tests, not from direct production code edits
- The TDD Delivery Plan becomes the default execution sequence
- Exceptions must be stated explicitly

## Teammate Architecture

This workflow creates a team and spawns each specialist as a real teammate (separate tmux pane). Use the following tool sequence:

1. `TeamCreate` — create the implementation team
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist as a teammate
3. `SendMessage` — communicate with running teammates
4. `TaskCreate` + `TaskUpdate` — assign and track work per teammate

**Do NOT use Agent without team_name** — that runs an inline subagent, not a visible teammate pane.

## Operator Visibility Contract

Emit these lines for every teammate action:

- `[Team Created] <team-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <review or validation failure>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`

---

## Required Input

This command expects a Discovery & Blueprint Document (from `/discovery` or `/squad`).
If not available, ask the user to run `/discovery` first or paste the blueprint.

---

## Execution

### Step 1 — Validate Blueprint

Confirm the Discovery & Blueprint Document is present.
If missing, stop and ask the user to provide it.

### Step 2 — Create Implementation Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "implement"
- `description`: "Implementation run for: {{feature_or_task_one_line}}"

Emit: `[Team Created] implement`

### Step 3 — TDD Specialist Teammate (Failing Tests First)

Spawn TDD Specialist to produce the first failing tests before any production code:

```
Agent(
  team_name = <team>,
  name = "tdd-specialist",
  subagent_type = "claude-tech-squad:tdd-specialist",
  prompt = """
## TDD — First Failing Tests

### TDD Delivery Plan
{{tdd_delivery_plan}}

### Test Plan
{{test_plan}}

### Architecture
{{architecture}}

---
You are the TDD Specialist. Write the first failing tests for the first delivery slice.
Use red-green-refactor cycles. Write tests using the repository's real test stack.
Do NOT write production code — only the failing tests.
Return the failing test files and run instructions.
"""
)
```

Emit: `[Teammate Spawned] tdd-specialist | pane: tdd-specialist`

Wait for TDD Specialist to complete. Confirm failing tests are in place before proceeding.

### Step 4 — Implementation Batch (Parallel)

Spawn implementation agents in parallel based on the TechLead's workstream plan.
Only spawn agents for workstreams that apply to this task.

```
# Spawn all relevant implementation agents in parallel
Agent(team_name=<team>, name="backend-dev",  subagent_type="claude-tech-squad:backend-dev",  prompt=...)
Agent(team_name=<team>, name="frontend-dev", subagent_type="claude-tech-squad:frontend-dev", prompt=...)
Agent(team_name=<team>, name="platform-dev", subagent_type="claude-tech-squad:platform-dev", prompt=...)
```

Emit: `[Batch Spawned] implementation | Teammates: <list>`

Each implementation agent prompt must include:
- TechLead execution plan (their specific workstream)
- Architecture decisions
- Failing test files from TDD Specialist
- Relevant specialist notes (backend-arch, frontend-arch, api-designer, etc.)
- Design principles guardrails
- Instruction: "Implement until the failing tests pass. Follow TDD. When done, return a summary of files changed and test results. Do NOT chain to other agents."

Wait for all implementation teammates to complete.

### Step 5 — Reviewer Teammate

Spawn Reviewer with implementation output:

```
Agent(
  team_name = <team>,
  name = "reviewer",
  subagent_type = "claude-tech-squad:reviewer",
  prompt = """
## Code Review

### Files Changed
{{implementation_batch_output}}

### Architecture and Design Guardrails
{{architecture_and_design_principles}}

### Test Plan
{{test_plan}}

---
You are the Reviewer. Review for correctness, simplicity, maintainability,
TDD compliance, lint compliance, and documentation compliance.
Flag bugs, regressions, missing tests, and unnecessary complexity.
Return: APPROVED or CHANGES REQUESTED with specific items.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] reviewer | pane: reviewer`

If reviewer returns CHANGES REQUESTED:
- Emit: `[Teammate Retry] <impl-agent> | Reason: <review item>`
- Spawn the relevant implementation agent again with the review feedback
- Repeat Step 5 until APPROVED

### Step 6 — QA Teammate

Spawn QA after reviewer approval:

```
Agent(
  team_name = <team>,
  name = "qa",
  subagent_type = "claude-tech-squad:qa",
  prompt = """
## QA Validation

### Implementation Output
{{approved_implementation}}

### Acceptance Criteria
{{acceptance_criteria}}

### Test Plan
{{test_plan}}

---
You are QA. Run real test commands against the implementation.
Validate all acceptance criteria. Check for regressions.
Return: PASS or FAIL with detailed failure diagnosis.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] qa | pane: qa`

If QA returns FAIL:
- Emit: `[Teammate Retry] <impl-agent> | Reason: <qa failure>`
- Spawn the relevant implementation agent with QA failure details
- Repeat Steps 5–6 until QA PASS

### Step 7 — Quality Bench (Parallel)

After QA PASS, spawn quality specialist reviewers in parallel:

```
Agent(team_name=<team>, name="security-rev",  subagent_type="claude-tech-squad:security-reviewer",      prompt=...)
Agent(team_name=<team>, name="privacy-rev",   subagent_type="claude-tech-squad:privacy-reviewer",       prompt=...)
Agent(team_name=<team>, name="perf-eng",      subagent_type="claude-tech-squad:performance-engineer",   prompt=...)
Agent(team_name=<team>, name="access-rev",    subagent_type="claude-tech-squad:accessibility-reviewer", prompt=...)
Agent(team_name=<team>, name="integ-qa",      subagent_type="claude-tech-squad:integration-qa",         prompt=...)
```

Emit: `[Batch Spawned] quality-bench | Teammates: <list>`

Only spawn reviewers relevant to this project. Each receives the full implementation output.
Instruction per reviewer: "Review from your specialist lens. Return findings as a checklist. Do NOT chain."

### Step 8 — Docs Writer Teammate

Spawn Docs Writer with the complete delivery package:

```
Agent(
  team_name = <team>,
  name = "docs-writer",
  subagent_type = "claude-tech-squad:docs-writer",
  prompt = """
## Documentation Update

### Implementation Output
{{approved_implementation}}

### Architecture Decisions
{{architecture}}

### Quality Review Findings
{{quality_bench_output}}

---
You are the Docs Writer. Update technical docs, migration notes, operator guidance,
changelog inputs, and developer-facing usage notes for this change.
Return a documentation delta or updated files.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] docs-writer | pane: docs-writer`

### Step 9 — Jira/Confluence Teammate

Spawn Jira/Confluence Specialist:

```
Agent(
  team_name = <team>,
  name = "jira-confluence",
  subagent_type = "claude-tech-squad:jira-confluence-specialist",
  prompt = """
## Jira and Confluence Update

### Delivery Package
{{full_implementation_summary}}

### Documentation Delta
{{docs_writer_output}}

---
You are the Jira/Confluence Specialist. Update Jira tickets and Confluence pages
for this delivery. Create subtasks, add comments, update status, and publish
documentation as appropriate.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] jira-confluence | pane: jira-confluence`

### Step 10 — PM UAT Gate

Spawn PM for UAT validation:

```
Agent(
  team_name = <team>,
  name = "pm-uat",
  subagent_type = "claude-tech-squad:pm",
  prompt = """
## UAT Validation

### Original Acceptance Criteria
{{acceptance_criteria}}

### Implementation Evidence
{{qa_output}}

### Quality Reviews
{{quality_bench_output}}

---
You are the PM performing UAT. Validate that each acceptance criterion has concrete
evidence of fulfillment from the QA and implementation output.
Return: APPROVED or REJECTED with specific gaps.
"""
)
```

Emit: `[Teammate Spawned] pm-uat | pane: pm-uat`
Emit: `[Gate] UAT | Waiting for user input`

Present PM UAT output to user. Implementation is complete when user approves.

---

## Output: Implementation Report

```
## Implementation Complete

### Agent Execution Log
- Team: implement
- Teammate: tdd-specialist | Status: completed | Output: failing tests written
- Batch: implementation | Teammates: [...] | Status: completed
- Teammate: reviewer | Status: APPROVED
- Teammate: qa | Status: PASS
- Batch: quality-bench | Teammates: [...] | Status: completed
- Teammate: docs-writer | Status: completed
- Teammate: jira-confluence | Status: completed
- Teammate: pm-uat | Status: [APPROVED/REJECTED]

### Build
- Workstreams executed: [...]
- Files changed: [...]
- TDD cycle: completed
- Review: APPROVED
- QA: PASS

### Quality
- Security: [summary]
- Privacy: [summary]
- Performance: [summary]
- Accessibility: [summary]
- Integration QA: [summary]
- Documentation: updated
- Jira / Confluence: updated
- UAT: [APPROVED/REJECTED]

### Evidence
- Tests run: [...]
- Acceptance criteria validated: [...]
- Outstanding issues: [...]
```
