---
name: discovery
description: Run discovery and blueprint for any software project with a full specialist squad. Produces product definition, prioritization, business analysis, architecture, specialist design notes, test and TDD delivery guidance, quality baselines, and delivery artifacts guidance.
---

# /discovery — Discovery & Blueprint

Run the planning phases before implementation. Each specialist runs as an independent teammate in its own tmux pane.

## Global Safety Contract

**This contract applies to every teammate spawned by this workflow. Violating it requires explicit written user confirmation.**

No teammate may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in production
- Run `tsuru app-remove`, `heroku apps:destroy`, or any equivalent application deletion command
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a workaround
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists

If any teammate believes a task requires one of these actions, it must STOP and surface the decision to the user before proceeding. The speed of a discovery workflow does not override this contract.

## Core Principle

All technical decisions must be grounded in the repository's real stack, conventions, and current documentation via context7.

## Teammate Architecture

This workflow creates a team and spawns each specialist as a real teammate (separate tmux pane). Use the following tool sequence:

1. `TeamCreate` — create the discovery team
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist as a teammate
3. `SendMessage` — communicate with running teammates
4. `TaskCreate` + `TaskUpdate` — assign and track work per teammate

**Do NOT use Agent without team_name** — that runs an inline subagent, not a visible teammate pane.

## Operator Visibility Contract

Emit these lines for every teammate action:

- `[Team Created] <team-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`

---

## Execution

### Step 1 — Repository Recon

Read the following files to understand the project:
- README.md, CLAUDE.md, package.json, pyproject.toml, requirements.txt
- List the main directories and identify the tech stack
- Note any existing architecture patterns, conventions, or constraints

### Step 2 — Create Discovery Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "discovery"
- `description`: "Discovery and blueprint session for: {{user_request_one_line}}"

Emit: `[Team Created] discovery`

### Step 3 — PM Teammate (Gate 1)

Spawn PM as a teammate:

```
Agent(
  team_name = <team from Step 2>,
  name = "pm",
  subagent_type = "claude-tech-squad:pm",
  prompt = """
## Discovery Start — Repository Context

### Stack
{{detected_stack}}

### Project structure
{{key_directories_and_files}}

### CLAUDE.md summary
{{claude_md_summary}}

### Task/Feature requested
{{user_request}}

---
You are the PM in the discovery chain. Analyze this from a product perspective.
Define the problem statement, user stories, and acceptance criteria.
When done, return your output as structured markdown for handoff to Business Analyst.
Do NOT chain to other agents — the orchestrator handles sequencing.
"""
)
```

Emit: `[Teammate Spawned] pm | pane: pm`

Wait for PM to complete. Present output as **Gate 1: Product Definition**. Ask user to confirm before continuing.

### Step 4 — Business Analyst Teammate

Spawn BA with PM output:

```
Agent(
  team_name = <team>,
  name = "ba",
  subagent_type = "claude-tech-squad:business-analyst",
  prompt = """
## Business Analysis

### PM Output
{{pm_output}}

### Repository Context
{{stack_and_structure}}

---
You are the Business Analyst. Extract business rules, workflow constraints, role interactions,
and operational edge cases from the PM output and repository context.
Return structured business analysis for handoff to PO.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] ba | pane: ba`

### Step 5 — PO Teammate (Gate 2)

Spawn PO with PM + BA output:

```
Agent(
  team_name = <team>,
  name = "po",
  subagent_type = "claude-tech-squad:po",
  prompt = """
## Prioritization

### PM Output
{{pm_output}}

### BA Output
{{ba_output}}

---
You are the PO. Decide scope, release slices, and what ships now vs later.
Perform the Post-Implementation Audit checklist.
Return a structured scope decision with acceptance criteria mapped to deliverables.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] po | pane: po`

Present PO output as **Gate 2: Scope Validation**. Ask user to confirm or cut scope before continuing.

### Step 6 — Planner Teammate (Gate 3)

Spawn Planner with full context so far:

```
Agent(
  team_name = <team>,
  name = "planner",
  subagent_type = "claude-tech-squad:planner",
  prompt = """
## Technical Planning

### PM Output
{{pm_output}}

### BA Output
{{ba_output}}

### PO Output (approved scope)
{{po_output}}

### Repository Context
{{stack_and_structure}}

---
You are the Planner. Inspect the real stack, validate capabilities, identify constraints,
decompose workstreams, and surface tradeoffs. Return a structured technical requirements
document with implementation options and risks.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] planner | pane: planner`

Present Planner output as **Gate 3: Technical Tradeoffs**. User selects the preferred implementation path.

### Step 7 — Architect Teammate

Spawn Architect with accumulated context:

```
Agent(
  team_name = <team>,
  name = "architect",
  subagent_type = "claude-tech-squad:architect",
  prompt = """
## Architecture Design

### Planner Output (selected path)
{{planner_output}}

### Repository Context
{{stack_and_structure}}

### Product Scope
{{po_output}}

---
You are the Architect. Design the overall solution: options, system decomposition,
workstream boundaries, sequencing, and implementation blueprint.
Align with Hexagonal Architecture if applicable to the stack.
Return structured architecture decisions for TechLead.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] architect | pane: architect`

### Step 8 — TechLead Teammate (Gate 4)

Spawn TechLead as execution strategy coordinator:

```
Agent(
  team_name = <team>,
  name = "techlead",
  subagent_type = "claude-tech-squad:techlead",
  prompt = """
## Tech Lead Execution Plan

### Architecture
{{architect_output}}

### Planner Output
{{planner_output}}

### Scope
{{po_output}}

---
You are the Tech Lead. Reconcile architecture and specialist inputs.
Choose the implementation path, assign workstream boundaries, and produce an
execution sequence. Identify which specialists are needed from this list:
backend-architect, frontend-architect, api-designer, data-architect, ux-designer,
ai-engineer, integration-engineer, devops, ci-cd, dba.
Return the execution plan and a list of required specialists.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] techlead | pane: techlead`

Present TechLead output as **Gate 4: Architecture Direction**. Confirm specialist set before spawning.

### Step 9 — Specialist Batch (Parallel)

Based on TechLead's specialist list, spawn relevant teammates in parallel.
Only spawn specialists that apply to this project and task.

```
# Example: spawn all that apply in parallel
Agent(team_name=<team>, name="backend-arch",   subagent_type="claude-tech-squad:backend-architect",  prompt=...)
Agent(team_name=<team>, name="frontend-arch",  subagent_type="claude-tech-squad:frontend-architect", prompt=...)
Agent(team_name=<team>, name="api-designer",   subagent_type="claude-tech-squad:api-designer",       prompt=...)
Agent(team_name=<team>, name="data-arch",      subagent_type="claude-tech-squad:data-architect",     prompt=...)
Agent(team_name=<team>, name="ux",             subagent_type="claude-tech-squad:ux-designer",        prompt=...)
```

Emit: `[Batch Spawned] specialist-bench | Teammates: <list of spawned roles>`

Each specialist prompt must include:
- TechLead execution plan
- Architecture decisions
- Product scope
- Repository context
- Instruction: "Return your specialist design notes. Do NOT chain to other agents."

Wait for all specialist teammates to complete.

### Step 10 — Quality Baseline Batch (Parallel)

Spawn quality reviewers in parallel (only relevant ones):

```
Agent(team_name=<team>, name="security",     subagent_type="claude-tech-squad:security-reviewer",   prompt=...)
Agent(team_name=<team>, name="privacy",      subagent_type="claude-tech-squad:privacy-reviewer",    prompt=...)
Agent(team_name=<team>, name="compliance",   subagent_type="claude-tech-squad:compliance-reviewer", prompt=...)
Agent(team_name=<team>, name="perf",         subagent_type="claude-tech-squad:performance-engineer",prompt=...)
Agent(team_name=<team>, name="observ",       subagent_type="claude-tech-squad:observability-engineer", prompt=...)
```

Emit: `[Batch Spawned] quality-baseline | Teammates: <list>`

Each reviewer receives: architecture decisions + specialist notes + repository context.
Instruction: "Produce a quality baseline checklist for this feature. Do NOT chain."

### Step 11 — Design Principles Teammate

Spawn design principles guardrails review:

```
Agent(
  team_name = <team>,
  name = "design-principles",
  subagent_type = "claude-tech-squad:design-principles-specialist",
  prompt = """
## Design Principles Review

### Architecture
{{architect_output}}

### Specialist Notes
{{specialist_batch_output}}

### Repository Context
{{stack_and_structure}}

---
You are the Design Principles Specialist. Review boundaries, dependency direction,
cohesion, coupling, testability, and Clean Architecture tradeoffs using the repository's
real structure. Return guardrails for the implementation phase.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] design-principles | pane: design-principles`

### Step 12 — Test Planner Teammate

Spawn Test Planner:

```
Agent(
  team_name = <team>,
  name = "test-planner",
  subagent_type = "claude-tech-squad:test-planner",
  prompt = """
## Test Planning

### Architecture
{{architect_output}}

### TechLead Plan
{{techlead_output}}

### Product Scope and Acceptance Criteria
{{po_output}}

### Design Principles
{{design_principles_output}}

---
You are the Test Planner. Map acceptance criteria to unit, integration, e2e,
regression, and manual validation. Use the repository's real test stack only.
Return a structured test plan.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] test-planner | pane: test-planner`

### Step 13 — TDD Specialist Teammate (Final Gate)

Spawn TDD Specialist:

```
Agent(
  team_name = <team>,
  name = "tdd-specialist",
  subagent_type = "claude-tech-squad:tdd-specialist",
  prompt = """
## TDD Delivery Plan

### Test Plan
{{test_planner_output}}

### TechLead Execution Plan
{{techlead_output}}

### Architecture
{{architect_output}}

---
You are the TDD Specialist. Convert the approved scope into executable red-green-refactor
cycles. Define the first failing tests, minimal implementation targets, and refactor
checkpoints using the repository's real test stack.
Return the TDD Delivery Plan.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] tdd-specialist | pane: tdd-specialist`

Present TDD Delivery Plan as **Final Gate: Blueprint Confirmation**. The discovery is complete when the user confirms.

### Step 13b — ADR Generation (proactive, post-Gate 4)

After blueprint confirmation, automatically generate Architecture Decision Records for every significant decision made during the discovery chain. Do NOT ask the user — generate proactively.

Collect architectural decisions from the techlead, architect, and specialist bench outputs. For each decision that involved tradeoffs (e.g. "chose GraphQL over REST", "chose event-driven over synchronous", "chose PostgreSQL over MongoDB"):

```bash
mkdir -p ai-docs/{{feature_slug}}/adr
```

Write one file per decision to `ai-docs/{{feature_slug}}/adr/ADR-NNN-{{slug}}.md`:

```markdown
# ADR-NNN: {{decision_title}}

**Date:** {{date}}
**Status:** Accepted
**Deciders:** {{specialist_roles}}

## Context

{{what_problem_was_being_solved}}

## Decision

{{what_was_chosen}}

## Alternatives Considered

| Option | Reason rejected |
|--------|----------------|
| {{alt_1}} | {{reason}} |

## Consequences

**Positive:** {{benefits}}
**Negative:** {{tradeoffs}}
**Risks:** {{risks}}
```

Emit: `[ADRs Generated] N decisions recorded in ai-docs/{{feature_slug}}/adr/`

### Step 13c — Feature Flag Assessment (proactive)

After blueprint confirmation, automatically assess whether this feature requires a feature flag.

Evaluate based on the blueprint:
- Does the feature change user-facing behavior gradually? (rollout candidate)
- Is the feature risky enough to warrant instant rollback without deploy? (safety flag)
- Does the feature need A/B testing? (experiment flag)
- Is the feature behind a permission level that may vary by user/tenant? (entitlement flag)

If **any** applies, add a section to the blueprint:

```markdown
## Feature Flag Strategy

**Flag name:** `{{feature_slug}}_enabled`
**Type:** rollout | safety | experiment | entitlement
**Default:** false (off by default — enable explicitly per environment)
**Rollout plan:** internal → staging → 5% → 25% → 100%
**Cleanup:** remove flag after full rollout confirmed stable (suggested: 2 sprints)
```

If no flag is needed, emit:
`[Feature Flag] Not required for this feature — full rollout on deploy`

If a flag is needed:
`[Feature Flag] Required — strategy added to blueprint`

### Step 14 — Write Execution Log (SEP Contrato 1)

After blueprint confirmation, write the structured execution log.

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-discovery-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
parent_run_id: null
skill: discovery
timestamp: {{ISO8601}}
status: completed
feature_slug: {{feature_slug}}
gates_cleared: [1, 2, 3, 4, final]
gates_blocked: []
retry_count: 0
teammates: [pm, ba, po, planner, architect, techlead, specialist-bench, quality-baseline, design-principles, test-planner, tdd-specialist]
output_artifact: ai-docs/{{feature_slug}}/blueprint.md
adrs_generated: N
feature_flag_required: true | false
implement_triggered: false
---

## Output Digest
{{one_paragraph_summary_of_what_was_designed}}

## Findings Gerados
none — discovery produces no actionable findings
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 15 — Discovery → Implement Bridge Gate (SEP Contrato 3)

Always present this gate immediately after writing the execution log:

```
Blueprint salvo em ai-docs/{{feature_slug}}/blueprint.md

Próximo passo: /implement ai-docs/{{feature_slug}}/blueprint.md

Quer iniciar a implementação agora? [S/N]
```

If the user answers **S**:
- Update `implement_triggered: true` in the execution log file using Edit tool
- Proceed to invoke `/implement` with the blueprint path

If the user answers **N**:
- Leave `implement_triggered: false` in the log
- Inform: "Para implementar depois: /implement ai-docs/{{feature_slug}}/blueprint.md"
- The `factory-retrospective` will detect this as an orphaned discovery

Emit: `[Gate] implement-bridge | Waiting for user input`

---

## Output: Discovery & Blueprint Document

```
## Discovery & Blueprint Document

### 0. Agent Execution Log
- Team: discovery
- Teammate: pm | Status: completed | Output: [...]
- Teammate: ba | Status: completed | Output: [...]
- Teammate: po | Status: completed | Output: [...]
- Teammate: planner | Status: completed | Output: [...]
- Teammate: architect | Status: completed | Output: [...]
- Teammate: techlead | Status: completed | Output: [...]
- Batch: specialist-bench | Teammates: [...] | Status: completed
- Batch: quality-baseline | Teammates: [...] | Status: completed
- Teammate: design-principles | Status: completed | Output: [...]
- Teammate: test-planner | Status: completed | Output: [...]
- Teammate: tdd-specialist | Status: completed | Output: [...]

### 1. Product Definition
[PM output]

### 2. Business Analysis
[BA output]

### 3. Product Prioritization
[PO output]

### 4. Technical Requirements
[Planner output]

### 5. Overall Architecture
[Architect output]

### 6. Tech Lead Execution Plan
[TechLead output]

### 7. Specialist Notes
#### Backend
[If present]

#### Frontend
[If present]

#### Data
[If present]

#### UX
[If present]

#### API
[If present]

#### AI
[If present]

#### Integration
[If present]

#### DevOps
[If present]

#### CI/CD
[If present]

#### DBA
[If present]

### 8. Design Principles Guardrails
[Design Principles Specialist output]

### 9. Quality, Governance, and Operations Baselines
#### Security
[If present]

#### Privacy
[If present]

#### Compliance
[If present]

#### Performance
[If present]

#### Observability
[If present]

### 10. Test Plan
[Test Planner output]

### 11. TDD Delivery Plan
[TDD Specialist output]

### 12. Stack & Conventions Observed
- Stack: [...]
- Repo conventions: [...]
- CI / deploy clues: [...]

### 13. Delivery Workstreams
- Backend: [...]
- Frontend: [...]
- Data: [...]
- AI: [...]
- Integrations: [...]
- Platform: [...]
- DevOps / CI-CD: [...]
- Docs / Jira / Confluence: [...]
- QA / Risk / Reliability: [...]
```
