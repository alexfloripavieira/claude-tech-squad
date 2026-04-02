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

- `[Preflight Start] <workflow-name>`
- `[Preflight Warning] <summary>`
- `[Preflight Passed] <workflow-name> | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`
- `[Team Created] <team-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Fallback Invoked] <failed-role> -> <fallback-subagent> | Reason: <summary>`
- `[Resume From] <workflow-name> | checkpoint=<checkpoint>`
- `[Checkpoint Saved] <workflow-name> | cursor=<checkpoint>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`

## Teammate Failure Protocol

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role, including the required `result_contract` block.

**For every teammate spawned — without exception:**

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - Emit: `[Teammate Retry] <name> | Reason: silent failure — re-spawning`
   - Re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails:
   - Read `plugins/claude-tech-squad/runtime-policy.yaml` and consult `fallback_matrix.discovery.<name>`
   - If a fallback subagent is listed:
     - Emit: `[Fallback Invoked] <name> -> <fallback-subagent> | Reason: primary failed twice`
     - Spawn the fallback once with the same context and an explicit instruction that it is acting as a surrogate for `<name>`
     - If the fallback returns a valid output, continue and record the event in `fallback_invocations` and `teammate_reliability`
   - If no fallback exists, or the fallback also fails:
     - Emit: `[Gate] Teammate Failure | <name> failed twice and fallback did not recover`
   - Surface to the user:

```
Teammate <name> failed to return a valid output (attempt 1 and 2).

Options:
- [R] Retry once more with the same prompt
- [S] Skip and continue — downstream quality WILL be degraded (log the risk)
- [X] Abort the run
```

4. **Sequential teammates** (output feeds the next agent): [S] degrades ALL downstream teammates that depend on this output — warn the user explicitly before accepting skip.
5. **Parallel batch teammates**: [S] on one agent does not block the batch, but the missing output must be logged as a risk in the final report.
6. **Do NOT advance to the next step** until every teammate in the current step has returned valid output, been explicitly skipped, or the run has been aborted.

## Agent Result Contract (ARC)

A teammate response is only considered structurally valid when it contains both:
- the role-specific body requested by that agent
- a final `result_contract` block

Required block:

```yaml
result_contract:
  status: completed | needs_input | blocked | failed
  confidence: high | medium | low
  blockers: []
  artifacts: []
  findings: []
  next_action: "..."
```

Validation rules:
- `status` must reflect the real execution outcome
- `blockers`, `artifacts`, and `findings` use empty lists when there is nothing to report
- `next_action` must identify the single best downstream step
- Missing `result_contract` means the teammate output is structurally invalid and must trigger the Teammate Failure Protocol

## Runtime Resilience Contract

Load `plugins/claude-tech-squad/runtime-policy.yaml` before creating the team. This file is the source of truth for:
- retry budgets
- fallback matrix
- severity policy
- checkpoint/resume rules
- reliability metrics recorded in SEP logs

If the runtime policy file is missing or unreadable, stop the run and surface `[Gate] Runtime Policy Missing`. Do not silently continue with hardcoded defaults.

---

## Execution

### Preflight Gate

Before creating the team, validate the run contract and emit explicit preflight lines.

Check and store:
- `execution_mode` — `tmux` if teammate mode is available, otherwise `inline`
- `resume_key` — provisional lowercase kebab-case derived from the user request before formal `{{feature_slug}}` extraction
- `{{architecture_style}}` — explicit or defaulted to `existing-repo-pattern`
- `{{lint_profile}}` — detected tool list or `none-detected`
- `docs_lookup_mode` — `context7` when available, otherwise `repo-fallback`
- `runtime_policy_version` — from `plugins/claude-tech-squad/runtime-policy.yaml`

Preflight rules:
- Emit `[Preflight Start] discovery`
- Read `plugins/claude-tech-squad/runtime-policy.yaml`
- If teammate mode is unavailable, emit `[Preflight Warning] teammate mode unavailable — continuing inline`
- If `{{architecture_style}}` had to be defaulted, emit `[Preflight Warning] architecture_style ambiguous — defaulting to existing-repo-pattern`
- If Context7 is unavailable, do **not** block; emit `[Preflight Warning] Context7 unavailable — using repository evidence and explicit assumptions`
- Inspect the latest `ai-docs/.squad-log/*-discovery-*.md` for the same `resume_key` when resuming an interrupted run
- If a prior partial discovery exists and inputs did not materially change, emit `[Resume From] discovery | checkpoint=<highest_completed_checkpoint>`
- Emit `[Preflight Passed] discovery | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`

### Checkpoint / Resume Rules

Use `checkpoint_resume.discovery` from `runtime-policy.yaml`.

Save a checkpoint whenever one of these milestones is completed:
- `preflight-passed`
- `gate-1-approved`
- `gate-2-approved`
- `gate-3-approved`
- `gate-4-approved`
- `specialist-bench-complete`
- `quality-baseline-complete`
- `blueprint-confirmed`

Checkpoint behavior:
- Emit `[Checkpoint Saved] discovery | cursor=<checkpoint>` whenever a checkpoint is reached
- On resume, skip already-completed checkpoints unless the user changed scope, architecture style, or repository context in a way that invalidates prior outputs
- Record `checkpoint_cursor`, `completed_checkpoints`, `resume_from`, `fallback_invocations`, and `teammate_reliability` in the SEP log

### Step 1 — Repository Recon and Variable Extraction

Read the following files to understand the project:
- README.md, CLAUDE.md, package.json, pyproject.toml, requirements.txt
- List the main directories and identify the tech stack
- Note any existing architecture patterns, conventions, or constraints

Extract and store for use throughout this discovery run:
- `{{feature_slug}}` — derived from the user's request as lowercase kebab-case (e.g. "user authentication with OAuth2" → `user-auth-oauth2`, or use ticket ID if provided)
- `{{user_request_one_line}}` — the user's request summarized in one line
- `{{architecture_style}}` — explicit architecture style for this feature (`existing-repo-pattern`, `layered`, `hexagonal`, `clean-architecture`, `modular-monolith`, `event-driven`, `other`). Default to `existing-repo-pattern` unless the repo or user clearly selects another style
- `{{lint_profile}}` — actual lint/format/static-analysis tools detected in the repository

`{{feature_slug}}` is used for ADR paths (`ai-docs/{{feature_slug}}/adr/`), blueprint path, feature flag naming, and the SEP log. Derive it immediately so all downstream steps have a consistent identifier.
`{{architecture_style}}` and `{{lint_profile}}` are used by Architect, TechLead, Reviewer, Design Principles, and Conformance Audit so the squad does not force a single style on every repository.

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

**Gate 1 Pass Criteria:**
- [ ] At least 3 measurable acceptance criteria defined
- [ ] Scope is bounded (no open-ended "and anything else needed")
- [ ] Success metrics are observable (testable behavior, not feelings)

If user is unsatisfied: ask specifically what is missing, re-spawn PM with that gap as context.

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

**Gate 2 Pass Criteria:**
- [ ] Scope cut is explicit — what is OUT is listed
- [ ] Must-have vs nice-to-have distinction is clear
- [ ] Release slice fits a single deployment

If user is unsatisfied: ask specifically what scope decision is wrong, re-spawn PO with that feedback.

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

**Gate 3 Pass Criteria:**
- [ ] At least 2 technical options were presented
- [ ] Selected option has rationale (not just "best practice")
- [ ] Breaking changes or migration risks are identified

If user is unsatisfied: ask which tradeoff decision needs revisiting, re-spawn Planner with that context.

### Step 7 — Architect Teammate

Spawn Architect with accumulated context:

```
Agent(
  team_name = <team>,
  name = "architect",
  subagent_type = "claude-tech-squad:architect",
  prompt = """
## Architecture Design

### PM Output (product requirements)
{{pm_output}}

### BA Output (domain rules and workflows)
{{ba_output}}

### Planner Output (selected path)
{{planner_output}}

### Repository Context
{{stack_and_structure}}

### Architecture Style
{{architecture_style}}

### Product Scope
{{po_output}}

---
You are the Architect. Design the overall solution: options, system decomposition,
workstream boundaries, sequencing, and implementation blueprint.
Preserve the repository's current pattern unless there is a strong reason to adopt another explicit style.
Use Hexagonal Architecture only when the feature or repository explicitly benefits from it.
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

### PM Output (product requirements)
{{pm_output}}

### BA Output (domain rules and workflows)
{{ba_output}}

### Scope
{{po_output}}

### Architecture Style
{{architecture_style}}

---
You are the Tech Lead. Reconcile architecture and specialist inputs.
Choose the implementation path, assign workstream boundaries, and produce an
execution sequence. Identify which specialists are needed from this list:
backend-architect, hexagonal-architect, frontend-architect, api-designer, data-architect, ux-designer,
ai-engineer, integration-engineer, devops, ci-cd, dba.
Return the execution plan and a list of required specialists.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] techlead | pane: techlead`

Present TechLead output as **Gate 4: Architecture Direction**. Confirm specialist set before spawning.

**Gate 4 Pass Criteria:**
- [ ] Workstream ownership is assigned (who builds what)
- [ ] Sequencing is explicit (what blocks what)
- [ ] Architecture layer violations are flagged or cleared

If user is unsatisfied: ask which workstream assignment or sequencing decision is wrong, re-spawn TechLead with that context.

### Step 9 — Specialist Batch (Parallel)

Based on TechLead's specialist list, spawn relevant teammates in parallel.
Only spawn specialists that apply to this project and task.

```
# Example: spawn all that apply in parallel
Agent(team_name=<team>, name="backend-arch",   subagent_type="claude-tech-squad:backend-architect",  prompt=...)
Agent(team_name=<team>, name="hexagonal-arch", subagent_type="claude-tech-squad:hexagonal-architect", prompt=...)
Agent(team_name=<team>, name="frontend-arch",  subagent_type="claude-tech-squad:frontend-architect", prompt=...)
Agent(team_name=<team>, name="api-designer",   subagent_type="claude-tech-squad:api-designer",       prompt=...)
Agent(team_name=<team>, name="data-arch",      subagent_type="claude-tech-squad:data-architect",     prompt=...)
Agent(team_name=<team>, name="ux",             subagent_type="claude-tech-squad:ux-designer",        prompt=...)
```

Emit: `[Batch Spawned] specialist-bench | Teammates: <list of spawned roles>`

Wait for ALL spawned specialist agents to return. Do NOT advance until every agent in this batch has returned a valid output block.
- For each agent that fails silently: apply the Teammate Failure Protocol defined above.
- Emit: `[Batch Completed] specialist-bench | N/N agents returned`

Each specialist prompt must include:
- TechLead execution plan
- Architecture decisions
- Chosen architecture style: `{{architecture_style}}`
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

Wait for ALL quality-baseline agents to return before proceeding.
- For each agent that fails silently: apply the Teammate Failure Protocol.
- Emit: `[Batch Completed] quality-baseline | N/N agents returned`

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

### Architecture Style
{{architecture_style}}

---
You are the Design Principles Specialist. Review boundaries, dependency direction,
cohesion, coupling, testability, and Clean Architecture tradeoffs using the repository's
real structure and the chosen architecture style. Return guardrails for the implementation phase.
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

### Step 12b — Feature Flag Assessment (proactive, before TDD)

Before spawning the TDD Specialist, assess whether this feature requires a feature flag. The TDD Specialist needs this information to write flag-gated tests.

Evaluate based on the blueprint:
- Does the feature change user-facing behavior gradually? (rollout candidate)
- Is the feature risky enough to warrant instant rollback without deploy? (safety flag)
- Does the feature need A/B testing? (experiment flag)
- Is the feature behind a permission level that may vary by user/tenant? (entitlement flag)

If **any** applies, produce a feature flag strategy and store as `{{feature_flag_strategy}}`:

```markdown
## Feature Flag Strategy

**Flag name:** `{{feature_slug}}_enabled`
**Type:** rollout | safety | experiment | entitlement
**Default:** false (off by default — enable explicitly per environment)
**Rollout plan:** internal → staging → 5% → 25% → 100%
**Cleanup:** remove flag after full rollout confirmed stable (suggested: 2 sprints)
**Tests required:** flag=false path + flag=true path must both have test coverage
```

If no flag is needed, set `{{feature_flag_strategy}}` to "No flag required — full rollout on deploy".

Emit: `[Feature Flag] Required — strategy defined` or `[Feature Flag] Not required`

### Step 13 — TDD Specialist Teammate (Final Gate)

Spawn TDD Specialist with the feature flag strategy so it can write flag-aware tests:

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

### Feature Flag Strategy
{{feature_flag_strategy}}

---
You are the TDD Specialist. Convert the approved scope into executable red-green-refactor
cycles. Define the first failing tests, minimal implementation targets, and refactor
checkpoints using the repository's real test stack.
If a feature flag is required, include test cycles for both the flag=false path and the flag=true path.
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
runtime_policy_version: {{runtime_policy_version}}
feature_slug: {{feature_slug}}
checkpoint_cursor: blueprint-confirmed
completed_checkpoints: [preflight-passed, gate-1-approved, gate-2-approved, gate-3-approved, gate-4-approved, specialist-bench-complete, quality-baseline-complete, blueprint-confirmed]
resume_from: {{resume_checkpoint | none}}
gates_cleared: [1, 2, 3, 4, final]
gates_blocked: []
retry_count: 0
fallback_invocations: []
teammate_reliability:
  pm: primary
  ba: primary
  po: primary
  planner: primary
  architect: primary
  techlead: primary
  specialist-bench: primary
  quality-baseline: primary
  design-principles: primary
  test-planner: primary
  tdd-specialist: primary
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
