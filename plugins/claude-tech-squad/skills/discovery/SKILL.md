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

## Progressive Disclosure — Context Digest Protocol

Do not forward full upstream agent output to every downstream agent. Instead, produce a **context digest** (max 500 tokens) between sequential phases.

**Digest format:**

```markdown
## Context Digest — {{source_agent}} ({{phase}})

**Key decisions:** {{bullet_list}}
**Artifacts produced:** {{file_list}}
**Open questions:** {{list_or_none}}
**Blockers:** {{list_or_none}}
**Architecture style:** {{style}}
**Full output reference:** available on request from orchestrator
```

**Rules:**
- Sequential agents (PM → BA → PO → Planner → Architect → TechLead): each receives a digest of the prior agent's output plus the full output of the immediately preceding agent only
- Parallel batch agents (specialist-bench, quality-baseline): each receives only the context relevant to its specialty, not the complete output of all prior agents
- Agents that explicitly need full upstream output (e.g., TechLead needs full Architect output, Architect needs full Planner output): receive it in addition to digests of earlier phases
- The orchestrator tracks token consumption per teammate and logs it in the SEP log

## Teammate Failure Protocol

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role, including the required `result_contract` block.

**For every teammate spawned — without exception:**

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - **Doom loop check** — before re-spawning, consult `doom_loop_detection` in `runtime-policy.yaml`. Compare the failed output against the prior attempt (if any). If a doom loop pattern is detected (growing_diff, oscillating_fix, or same_error):
     - Emit: `[Doom Loop Detected] <name> | pattern=<rule_name> | retries=<count>`
     - Skip the retry and go directly to step 3 (fallback) — retrying the same agent will waste tokens
   - If no doom loop detected: Emit `[Teammate Retry] <name> | Reason: silent failure — re-spawning` and re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails (or doom loop was detected in step 2):
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

## Inline Health Check

After every `[Teammate Done]`, run the health check (6 signals).

**python3 plugins/claude-tech-squad/bin/squad-cli health** (preferred — deterministic, saves ~2K tokens per teammate):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli health \
  --run-id {{feature_slug}} --teammate <name> \
  --tokens-in <N> --tokens-out <N> \
  --status <completed|failed|blocked> --confidence <high|medium|low> \
  --retries <N> --findings-blocking <N> --duration-ms <N> \
  --policy plugins/claude-tech-squad/runtime-policy.yaml \
  --state-dir .squad-state
```

Returns JSON with `signals_triggered`, `context_enrichment`, `budget_percent`, `is_critical`. Use `context_enrichment` directly as prepended text for the next teammate.

If `squad-cli` is not available: evaluate the 6 signals manually.

- Emit: `[Health Check] <name> | signals: <triggered_signals_or_ok>`
- **warning signals**: prepend context to next teammate
- **critical signals**: emit `[Health Warning]` and surface to user

## Agent Result Contract (ARC)

A teammate response is only considered structurally valid when it contains ALL of:
- the role-specific body requested by that agent
- a plan section (`## Pre-Execution Plan` for execution agents, `## Analysis Plan` for analysis agents)
- a final `result_contract` block
- a final `verification_checklist` block

Required blocks:

```yaml
result_contract:
  status: completed | needs_input | blocked | failed
  confidence: high | medium | low
  blockers: []
  artifacts: []
  findings: []
  next_action: "..."

verification_checklist:
  plan_produced: true
  base_checks_passed: [completeness, accuracy, contract, scope, downstream]
  role_checks_passed: [<role-specific check names>]
  issues_found_and_fixed: 0
  confidence_after_verification: high | medium | low
```

Validation rules:
- `status` must reflect the real execution outcome
- `blockers`, `artifacts`, and `findings` use empty lists when there is nothing to report
- `next_action` must identify the single best downstream step
- `confidence_after_verification` must match `confidence` in `result_contract`
- Missing `result_contract` OR missing `verification_checklist` means the teammate output is structurally invalid and must trigger the Teammate Failure Protocol

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

Emit `[Preflight Start] discovery`

**python3 plugins/claude-tech-squad/bin/squad-cli accelerated preflight** (preferred — saves ~5K tokens):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli preflight --skill discovery --policy plugins/claude-tech-squad/runtime-policy.yaml --project-root .
```

Returns JSON with `stack`, `ai_feature`, `routing` (pm_agent, techlead_agent, etc.), `lint_profile`, `token_budget_max`, `resume_from`, and `warnings`.

Then initialize the run state:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli init --run-id {{feature_slug}} --skill discovery --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
```

If `squad-cli` is not available, fall back to manual preflight: read `runtime-policy.yaml`, detect stack from signal files, resolve routing, check for resumable prior runs.

**Ticket Intake** — If the user's input matches a ticket ID pattern (`[A-Z]+-[0-9]+` for Jira, `#[0-9]+` for GitHub Issues, `LIN-[0-9]+` for Linear):
  1. Read the ticket via the appropriate MCP tool
  2. Extract: title, description, acceptance criteria, priority, subtasks, labels, comments
  3. Use the extracted content as `{{user_request}}`
  4. Emit: `[Ticket Read] {{source}} | {{ticket_id}} | type={{issue_type}} | priority={{priority}}`
  5. If MCP is unavailable, ask the user to paste the ticket content — do not block

Emit all warnings from preflight, then:
- Emit `[Preflight Passed] discovery | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`

### Checkpoint / Resume Rules

Checkpoints: `preflight-passed`, `gate-1-approved`, `gate-2-approved`, `gate-3-approved`, `gate-4-approved`, `specialist-bench-complete`, `quality-baseline-complete`, `blueprint-confirmed`.

**python3 plugins/claude-tech-squad/bin/squad-cli checkpoint** (preferred):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint save --run-id {{feature_slug}} --cursor <checkpoint> --state-dir .squad-state
```

If `squad-cli` is not available: emit `[Checkpoint Saved] discovery | cursor=<checkpoint>` and track state manually.

### Step 1 — Repository Recon and Variable Extraction

Read CLAUDE.md and README.md. Note architecture patterns and constraints.

**Stack, routing, and lint detection** — all resolved by `python3 plugins/claude-tech-squad/bin/squad-cli preflight`. The returned JSON contains `stack`, `routing`, `lint_profile`, and `ai_feature`.

Extract and store:
- `{{feature_slug}}` — derived from the user's request as lowercase kebab-case (or ticket ID)
- `{{user_request_one_line}}` — one-line summary
- `{{architecture_style}}` — from preflight or defaulted to `existing-repo-pattern`
- `{{lint_profile}}` — from preflight

Emit: `[Stack Detected] {{detected_stack}} | pm={{pm_agent}} | techlead={{techlead_agent}}`

### Step 2 — Create Discovery Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "discovery"
- `description`: "Discovery and blueprint session for: {{user_request_one_line}}"

Emit: `[Team Created] discovery`

### Step 2b — Scope Confirmation Gate (Gate 0)

If the ticket or user request involves **multiple API versions, multiple features, or ambiguous scope**, present a scope confirmation gate BEFORE spawning PM:

**Trigger conditions** (check any):
- Ticket title contains "v1" AND "v2" (or multiple version references)
- User request mentions "and also", "plus", or lists 3+ distinct features
- Ticket has subtasks spanning different modules or APIs

If triggered:

```
[Gate] Scope Confirmation

The task appears to involve multiple scopes:
- {{scope_a}} (e.g., v1 API)
- {{scope_b}} (e.g., v2 API)

Which scope should this discovery cover?
[1] {{scope_a}} only
[2] {{scope_b}} only
[A] Both (larger discovery)
```

Store the confirmed scope as `{{confirmed_scope}}` and pass it to PM as context.

If no ambiguity is detected, skip this gate silently — do not ask unnecessary questions.

Emit (if triggered): `[Gate] Scope Confirmation | Waiting for user input`

### Step 3 — PM Teammate (Gate 1)

Spawn PM as a teammate:

```
Agent(
  team_name = <team from Step 2>,
  name = "pm",
  subagent_type = "claude-tech-squad:{{pm_agent}}",
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

**Progressive Disclosure:** PO receives full BA output (immediately preceding) + digest of PM.

Before spawning, produce the PM digest:
```
pm_digest = summarize(pm_output, max_tokens=500, format=context_digest)
```

Spawn PO:

```
Agent(
  team_name = <team>,
  name = "po",
  subagent_type = "claude-tech-squad:po",
  prompt = """
## Prioritization

### PM Summary (digest — full output available on request)
{{pm_digest}}

### BA Output (full)
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

**Progressive Disclosure:** Planner receives full PO output (immediately preceding) + digests of PM and BA.

Before spawning, produce digests:
```
pm_digest = summarize(pm_output, max_tokens=500, format=context_digest)
ba_digest = summarize(ba_output, max_tokens=500, format=context_digest)
```

Spawn Planner:

```
Agent(
  team_name = <team>,
  name = "planner",
  subagent_type = "claude-tech-squad:planner",
  prompt = """
## Technical Planning

### PM Summary (digest)
{{pm_digest}}

### BA Summary (digest)
{{ba_digest}}

### PO Output (full — approved scope)
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

**Progressive Disclosure:** Architect receives full Planner output (immediately preceding) + digests of PM, BA, PO.

Before spawning, produce digests:
```
pm_digest  = summarize(pm_output, max_tokens=500, format=context_digest)
ba_digest  = summarize(ba_output, max_tokens=500, format=context_digest)
po_digest  = summarize(po_output, max_tokens=500, format=context_digest)
```

Spawn Architect:

```
Agent(
  team_name = <team>,
  name = "architect",
  subagent_type = "claude-tech-squad:architect",
  prompt = """
## Architecture Design

### Product Requirements (PM digest)
{{pm_digest}}

### Domain Rules (BA digest)
{{ba_digest}}

### Approved Scope (PO digest)
{{po_digest}}

### Planner Output (full — selected path)
{{planner_output}}

### Repository Context
{{stack_and_structure}}

### Architecture Style
{{architecture_style}}

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

**Progressive Disclosure:** TechLead receives full Architect output (immediately preceding) + digests of PM, BA, PO, Planner.

Before spawning, produce digests:
```
pm_digest      = summarize(pm_output, max_tokens=500, format=context_digest)
ba_digest      = summarize(ba_output, max_tokens=500, format=context_digest)
po_digest      = summarize(po_output, max_tokens=500, format=context_digest)
planner_digest = summarize(planner_output, max_tokens=500, format=context_digest)
```

Spawn TechLead:

```
Agent(
  team_name = <team>,
  name = "techlead",
  subagent_type = "claude-tech-squad:{{techlead_agent}}",
  prompt = """
## Tech Lead Execution Plan

### Architecture (full)
{{architect_output}}

### Technical Requirements (Planner digest)
{{planner_digest}}

### Product Requirements (PM digest)
{{pm_digest}}

### Domain Rules (BA digest)
{{ba_digest}}

### Approved Scope (PO digest)
{{po_digest}}

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

**Progressive Disclosure:** Specialist batch agents receive full TechLead plan + full Architect output (both directly relevant) + digests of PM, BA, PO, Planner.

Each specialist prompt must include:
- TechLead execution plan (full — their specific workstream assignment)
- Architecture decisions (full — they need structural context)
- Chosen architecture style: `{{architecture_style}}`
- Product scope (PO digest — only the boundaries relevant to their specialty)
- Repository context
- Earlier phases (PM, BA, Planner digests — not full outputs)
- Instruction: "Return your specialist design notes. Do NOT chain to other agents."

Wait for all specialist teammates to complete.

### Step 10 — Quality Baseline Batch (Parallel)

**Auth-sensitive HARD gate (MANDATORY):** if the feature touches any of:

- authentication flows (login, logout, session lifecycle)
- magic-link / one-time-token issuance or consumption
- OAuth / SSO integrations (Google, Microsoft, SAML, OIDC)
- password reset, account recovery, impersonation
- session token storage, refresh, revocation

then `security-reviewer` is a **HARD gate** — it CANNOT be skipped-with-risk and CANNOT be auto-advanced. The run must wait for security-reviewer output with status=APPROVED or BLOCKED. Record `auth_touching_feature: true` and `security_reviewer_gate: hard` in the SEP frontmatter. Added 2026-04-18 after the retrospective flagged magic-link and session-auth as recurring orphaned discoveries with skipped security review.

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

**Progressive Disclosure:** Quality baseline agents receive architecture decisions + specialist notes (both directly relevant) + digest of product scope. They do NOT need full PM, BA, Planner, or TechLead outputs.

Each reviewer receives:
- Architecture decisions (full)
- Specialist notes relevant to their domain (full)
- Product scope (PO digest)
- Repository context
- Instruction: "Produce a quality baseline checklist for this feature. Do NOT chain."

### Step 11 — Design Principles Teammate

**Progressive Disclosure:** Design Principles receives full Architect output + full specialist notes (both directly relevant). Earlier phases are NOT forwarded.

Spawn design principles guardrails review:

```
Agent(
  team_name = <team>,
  name = "design-principles",
  subagent_type = "claude-tech-squad:design-principles-specialist",
  prompt = """
## Design Principles Review

### Architecture (full)
{{architect_output}}

### Specialist Notes (full)
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

**Progressive Disclosure:** Test Planner receives full Design Principles output (immediately preceding) + full TechLead plan + digests of architecture and product scope.

Before spawning:
```
architect_digest = summarize(architect_output, max_tokens=500, format=context_digest)
po_digest        = summarize(po_output, max_tokens=500, format=context_digest)
```

Spawn Test Planner:

```
Agent(
  team_name = <team>,
  name = "test-planner",
  subagent_type = "claude-tech-squad:test-planner",
  prompt = """
## Test Planning

### Architecture (digest)
{{architect_digest}}

### TechLead Plan (full)
{{techlead_output}}

### Product Scope and Acceptance Criteria (PO digest)
{{po_digest}}

### Design Principles (full)
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

**Progressive Disclosure:** TDD Specialist receives full Test Planner output (immediately preceding) + full TechLead plan + digests of architecture.

Before spawning:
```
architect_digest = summarize(architect_output, max_tokens=500, format=context_digest)
```

Spawn TDD Specialist with the feature flag strategy so it can write flag-aware tests:

```
Agent(
  team_name = <team>,
  name = "tdd-specialist",
  subagent_type = "claude-tech-squad:tdd-specialist",
  prompt = """
## TDD Delivery Plan

### Test Plan (full)
{{test_planner_output}}

### TechLead Execution Plan (full)
{{techlead_output}}

### Architecture (digest)
{{architect_digest}}

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

### Step 13c — Run Cost Summary and SEP Log

**python3 plugins/claude-tech-squad/bin/squad-cli cost + sep-log** (preferred — uses real token counts):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli cost --run-id {{feature_slug}} --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
python3 plugins/claude-tech-squad/bin/squad-cli sep-log --run-id {{feature_slug}} --output-dir ai-docs/.squad-log --state-dir .squad-state
```

Emit:
```
[Run Summary] /discovery | teammates: {{N}} | tokens: {{total_input}}K in / {{total_output}}K out | est. cost: ~${{usd}} | duration: {{elapsed}}
```

If `squad-cli` is not available: sum tokens manually, estimate cost, and write the SEP log manually to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-discovery-{{run_id}}.md` with full YAML frontmatter. The SEP log MUST use YAML frontmatter between `---` delimiters — `/dashboard` and `/factory-retrospective` parse these fields programmatically.

**Required frontmatter fields for discovery SEP logs:**

```yaml
---
run_id: {{run_id}}
skill: discovery
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}      # required — refreshed whenever the log is edited
final_status: completed | in_flight | aborted
execution_mode: teammates | inline
architecture_style: {{style}}
checkpoints: [preflight-passed, gate-1-approved, ...]
fallbacks_invoked: []
retry_count: {{N}}
tokens_input: {{actual_or_null}}  # required — actual measurement or null; 0 placeholder forbidden
tokens_output: {{actual_or_null}} # required — actual measurement or null; 0 placeholder forbidden
estimated_cost_usd: {{usd}}
total_duration_ms: {{ms}}
implement_triggered: true | false
implement_deferred_reason: {{required_when_implement_triggered_false}}  # MUST be non-empty when implement_triggered=false
auth_touching_feature: true | false
security_reviewer_gate: hard | soft | n/a
---
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
- **REQUIRED:** populate `implement_deferred_reason` in the SEP frontmatter. This field is mandatory whenever `implement_triggered: false`. Empty string or missing field means the SEP log is structurally incomplete and `/factory-retrospective` will flag it as an orphaned discovery with unknown cause. Collect the reason from the user (e.g. "waiting on design review", "deprioritized", "blocked by FF-262") — do NOT leave blank.
- Write a pending-implement tracker file so the blueprint is not lost:
  ```
  Write to tasks/pending-implement-{{feature_slug}}.md:
  # Pending Implementation: {{feature_slug}}

  **Blueprint:** ai-docs/{{feature_slug}}/blueprint.md
  **Discovery run:** {{run_id}}
  **Date:** {{YYYY-MM-DD}}

  To implement: /implement ai-docs/{{feature_slug}}/blueprint.md

  ## Reason for deferral
  {{user_reason_or_deferred_by_user}}
  ```
- Inform: "Registrado em tasks/pending-implement-{{feature_slug}}.md. Para implementar depois: /implement ai-docs/{{feature_slug}}/blueprint.md"
- The `factory-retrospective` will detect this as an orphaned discovery

Emit: `[Gate] implement-bridge | Waiting for user input`

### Step 16 — Team Cleanup (mandatory epilogue)

After the bridge gate resolves (regardless of user choice), clean up the team to prevent ghost members from blocking future TeamCreate calls:

```
TeamDelete(name="discovery")
```

Emit: `[Team Deleted] discovery | cleanup complete`

If TeamDelete fails (team does not exist or already deleted), ignore the error silently — do not block the run.

**Why this is mandatory:** Team members persist across session restarts. If not cleaned up, the next skill that calls TeamCreate will fail with "Already leading team". This was discovered in golden run testing (APPS-519 ghost team blocked factory-retrospective TeamCreate).

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
