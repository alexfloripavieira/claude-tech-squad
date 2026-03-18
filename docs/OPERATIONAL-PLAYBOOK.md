# Operational Playbook

This playbook shows how to use `claude-tech-squad` in common delivery scenarios inside a real repository.

Use it when you want a practical answer to: "which command should I run for this kind of work?"

## Core Rule

Choose the lightest command that still matches the real delivery scope:

- `/claude-tech-squad:discovery` for shaping and planning
- `/claude-tech-squad:implement` for execution after approval
- `/claude-tech-squad:squad` for end-to-end or audit-style work

## Scenario 1: New Feature

Use:

- `/claude-tech-squad:discovery`

When:

- the problem still needs shaping
- architecture is not yet confirmed
- acceptance criteria need to be clarified

Prompt example:

```text
/claude-tech-squad:discovery
Design the next delivery slice for subscription management, including admin roles, audit trail, rollout boundaries, and acceptance criteria.
```

Healthy output:

- `Phase Start` lines for discovery and blueprint
- explicit agent handoffs such as PM, Planner, Architect, Tech Lead, and Design Principles Specialist
- a final blueprint document

## Scenario 2: Implement Approved Blueprint

Use:

- `/claude-tech-squad:implement`

When:

- discovery is already done
- architecture and scope have been approved
- you want TDD cycle planning, build, review, QA, docs, and UAT coordination

Prompt example:

```text
/claude-tech-squad:implement
Use the approved blueprint to implement the next delivery slice through TDD cycles, run validation, update docs, and produce release-ready output.
```

Healthy output:

- build and quality phases
- design guardrails before implementation agents start
- a TDD delivery plan or refreshed TDD cycle map before implementation agents start
- implementation agent handoffs
- reviewer and QA loops when needed
- final implementation report with `Agent Execution Log`

## Scenario 2A: TDD-First Delivery Slice

Use:

- `/claude-tech-squad:discovery`
- then `/claude-tech-squad:implement`

When:

- you want development to start from failing tests rather than direct implementation
- the slice is small enough to benefit from explicit red-green-refactor cycles

Prompt example:

```text
/claude-tech-squad:discovery
Plan the next billing retry slice and prepare it for TDD, including the first failing tests, cycle order, design guardrails, and QA handoff.
```

Then:

```text
/claude-tech-squad:implement
Use the approved discovery package to execute the billing retry slice through TDD cycles and validate the result.
```

## Scenario 3: End-To-End Delivery

Use:

- `/claude-tech-squad:squad`

When:

- you want the full path from discovery to release preparation
- the task spans multiple specialties and approvals

Prompt example:

```text
/claude-tech-squad:squad
Add SSO login with audit trail, admin approval flow, automated coverage, documentation, and release artifacts.
```

Healthy output:

- discovery, blueprint, build, quality, and release phases
- visible orchestration across specialists
- final squad report and `Agent Execution Log`

## Scenario 4: Jira Or Acceptance Audit

Use:

- `/claude-tech-squad:squad`

When:

- you need to compare a ticket to real implementation
- you want PM, QA, reviewer, and technical roles involved in the audit

Prompt example:

```text
/claude-tech-squad:squad
Audit the linked Jira story against the current implementation, validate requirements and acceptance criteria, review structural design quality, run relevant checks, and show explicit agent execution lines with Agent Execution Log.
```

Healthy output:

- requirement and acceptance matrices
- evidence by file or test
- visible execution trace
- final verdict with blockers and gaps

## Scenario 5: Refactor Or Debt Reduction

Use:

- `/claude-tech-squad:discovery`
- then `/claude-tech-squad:implement`

When:

- the goal is technical improvement rather than new scope
- you still need design, risk analysis, and controlled implementation

Prompt example:

```text
/claude-tech-squad:discovery
Plan a refactor of webhook retry handling to improve idempotency, observability, and rollback safety without changing user-facing behavior.
```

## Scenario 6: Release Readiness

Use:

- `/claude-tech-squad:implement`
- or `/claude-tech-squad:squad` if you need the full pass

When:

- implementation is mostly done
- you need QA confidence, docs delta, Jira/Confluence updates, and rollout guidance

Prompt example:

```text
/claude-tech-squad:implement
Run release-readiness validation for the approved scope, including QA, documentation delta, Jira/Confluence pack, and rollout preparation.
```

## Scenario 7: Production Incident Follow-Through

Use:

- `/claude-tech-squad:squad`

When:

- the issue already crosses diagnosis, remediation, testing, operational safety, and release

Prompt example:

```text
/claude-tech-squad:squad
Investigate the duplicate webhook incident, implement the fix, validate regressions, update operational docs, and prepare a safe rollout plan.
```

## What Good Execution Looks Like

You should expect:

- visible phase transitions
- role-specific handoff lines
- structural guidance before the implementation pass when architecture matters
- retries when review or QA fails
- batch lines when specialist benches run in parallel
- a final `Agent Execution Log`

If these markers are missing, use [EXECUTION-TRACE.md](EXECUTION-TRACE.md).
