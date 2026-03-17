---
name: implement
description: Run build and quality for any software project based on a prior discovery document. Supports a full specialist bench across implementation, quality, operations, and delivery artifacts.
---

# /implement — Build & Quality

Run implementation and quality validation using the Discovery & Blueprint Document produced by `/discovery`.

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
- Quality and operations baselines
- Test plan

If the discovery document is not already available in the conversation, ask the user to provide it.

---

## Phase 3: Build

### Step 3.0: Tech Lead — Build Coordination

Use the Agent tool with `subagent_type: "claude-tech-squad:techlead"`.

Prompt:
```
You are the Tech Lead agent.

Use the confirmed discovery document to determine:
- which implementation agents are needed
- what order they should run in
- which ones can run in parallel safely
- what the write boundaries are
```

### Step 3.1: Relevant Implementation Agents

Run only the implementation agents needed by the architecture:

- `claude-tech-squad:backend-dev`
- `claude-tech-squad:frontend-dev`
- `claude-tech-squad:platform-dev`
- `claude-tech-squad:integration-engineer`
- `claude-tech-squad:ai-engineer`
- `claude-tech-squad:devops`
- `claude-tech-squad:ci-cd`
- `claude-tech-squad:dba`

They may run in parallel when their write scopes are independent.

Prompt template:
```
You are the [implementation-agent]. Follow your instructions exactly.

Architecture package:
- Overall architecture: [Insert Architect output]
- Tech Lead execution plan: [Insert Tech Lead output]
- Relevant specialist notes: [Insert relevant notes only]

Test plan:
[Insert Test Plan]

Relevant baselines:
[Insert security / privacy / performance / observability / analytics / compliance notes as needed]

MANDATORY:
- Verify framework or platform APIs via context7 before using them
- Follow the repo's existing conventions
- Implement only your assigned slice
- Add or update tests, configs, or validation for your logic when applicable
```

### Step 3.2: Reviewer — Code Review

Use the Agent tool with `subagent_type: "claude-tech-squad:reviewer"`.

Prompt:
```
You are the Reviewer agent in build mode.

Review all code and config changes made by the implementation agents.

Architecture package:
[Insert architecture package]

Focus on:
- correctness
- regressions
- complexity
- missing tests
- doc compliance for unfamiliar APIs
```

If the reviewer requests changes:

1. Route issues back to the appropriate implementation agent.
2. Re-run review.
3. Repeat up to 3 cycles before asking the user.

### Step 3.3: Continuous Quality Validation

Run the relevant quality implementers:

- `claude-tech-squad:test-automation-engineer`
- `claude-tech-squad:integration-qa`
- `claude-tech-squad:qa`

Prompt:
```
You are the [quality-agent] in build mode.

Test plan:
[Insert Test Plan]

Architecture package:
[Insert relevant architecture and implementation context]

Implement and run the validation relevant to your quality slice.
Report pass/fail with concrete evidence and distinguish code bugs from test issues.
```

If continuous quality fails:

1. Route failures to the responsible implementation agent.
2. Re-run Reviewer.
3. Re-run the affected quality agents.
4. Repeat up to 3 cycles before asking the user.

---

## Phase 4: Quality

### Step 4.1: Full Validation

Run:

- `claude-tech-squad:integration-qa`
- `claude-tech-squad:qa`

Prompt:
```
You are the [quality-agent] in quality mode.

PM acceptance criteria:
[Insert PM output]

Test plan:
[Insert Test Plan]

Run the full validation pass relevant to your slice:
- required automated tests
- integration and end-to-end validation
- regression checks
- manual validation items from the plan
- acceptance criteria mapping
```

### Step 4.2: Specialist Quality Reviews

Run the relevant specialists:

- `claude-tech-squad:security-reviewer`
- `claude-tech-squad:privacy-reviewer`
- `claude-tech-squad:compliance-reviewer`
- `claude-tech-squad:accessibility-reviewer`
- `claude-tech-squad:performance-engineer`
- `claude-tech-squad:observability-engineer`
- `claude-tech-squad:analytics-engineer`

Prompt:
```
You are the [specialist] agent in quality mode.

Review all code and config changes for the risks owned by your specialty.

Architecture package:
[Insert architecture package]

Relevant baselines from discovery:
[Insert relevant baseline outputs]
```

### Step 4.3: Docs and Delivery Artifacts

Run:

- `claude-tech-squad:docs-writer`
- `claude-tech-squad:jira-confluence-specialist`

Prompt:
```
You are the [docs-agent].

Review the implemented changes and identify the required documentation or delivery artifact delta.

Architecture package:
[Insert architecture package]

Quality findings:
- QA reports: [Insert QA summaries]
- Specialist reviews: [Insert specialist review summaries]
```

### Step 4.4: PM — UAT

Use the Agent tool with `subagent_type: "claude-tech-squad:pm"`.

Prompt:
```
You are the PM agent in UAT mode.

Original user story and acceptance criteria:
[Insert PM output]

QA reports:
[Insert QA report summaries]

Critical specialist reviews:
[Insert specialist review summaries]

Validate whether the delivered result solves the original problem and produce the UAT report.
```

### Quality Gate

If PM rejects the result or any critical specialist review fails:

1. Route fixes to the responsible implementation agent.
2. Re-run Reviewer, the affected quality agents, the affected specialist reviews, and PM validation.
3. Repeat up to 2 cycles before asking the user.

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
