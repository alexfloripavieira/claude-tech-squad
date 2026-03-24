---
name: squad
description: Run the full technology squad workflow end-to-end with the full specialist bench: discovery, blueprint, design-principles and TDD-first implementation, quality, documentation, Jira/Confluence, reliability, and release preparation.
---

# /squad — Full Technology Squad

Run the complete end-to-end workflow. Every specialist runs as an independent teammate in its own tmux pane. This is the full pipeline: discovery → blueprint → implementation → quality → docs → release.

## Core Principle

Do not assume the stack, the conventions, or the product domain. Discover them from the repository and validate technical decisions against current documentation via context7.

## TDD Default Mode

When `/squad` is used for code changes, TDD is the default strategy:

- Do not start implementation before the Test Plan and TDD Delivery Plan are ready
- Implementation agents begin from failing tests
- Use red-green-refactor cycles as the normal execution model

TDD may be relaxed only when:
- The task is documentation-only or release-only
- The repository genuinely has no viable automated test path
- An external constraint makes tests-first impossible for a specific step

If TDD is relaxed, state so explicitly and explain why.

## Teammate Architecture

This workflow creates a single team that persists across all phases. Use the following tool sequence:

1. `TeamCreate` — create the squad team (once, at start)
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist as a teammate
3. `SendMessage` — communicate with running teammates
4. `TaskCreate` + `TaskUpdate` — assign and track work per teammate

**Do NOT use Agent without team_name** — that runs an inline subagent, not a visible teammate pane.

## Operator Visibility Contract

Emit these lines for every teammate action:

- `[Team Created] <team-name>`
- `[Phase Start] <phase-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`
- `[Phase Done] <phase-name> | Outcome: <summary>`

---

## Execution

### Step 1 — Repository Recon

Read the following files to understand the project:
- README.md, CLAUDE.md, package.json, pyproject.toml, requirements.txt
- List the main directories and identify the tech stack
- Note any existing architecture patterns, conventions, or constraints

### Step 2 — Create Squad Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "squad"
- `description`: "Full squad run for: {{user_request_one_line}}"

Emit: `[Team Created] squad`

---

### PHASE 1: DISCOVERY

Emit: `[Phase Start] discovery`

Follow the same teammate sequence as `/discovery` Steps 3–13:

**Sequential chain with gates:**
1. Spawn `pm` → **Gate 1: Product Definition**
2. Spawn `ba` with PM output
3. Spawn `po` → **Gate 2: Scope Validation**
4. Spawn `planner` → **Gate 3: Technical Tradeoffs**
5. Spawn `architect`
6. Spawn `techlead` → **Gate 4: Architecture Direction**
7. Spawn specialist batch in parallel (from TechLead list)
8. Spawn quality baseline batch in parallel
9. Spawn `design-principles`
10. Spawn `test-planner`
11. Spawn `tdd-specialist` → **Gate 5: Blueprint Confirmation**

Each spawn: `Agent(team_name=<squad-team>, name=<role>, subagent_type="claude-tech-squad:<role>", prompt=...)`

All agents receive the full accumulated context from prior teammates.
All agents end with: "Do NOT chain to other agents — the orchestrator handles sequencing."

Emit: `[Phase Done] discovery | Blueprint confirmed`

---

### PHASE 2: IMPLEMENTATION

Emit: `[Phase Start] implementation`

**Sequential with parallel batches:**

1. Spawn `tdd-impl` (tdd-specialist) — write first failing tests
2. Spawn implementation batch in parallel:
   - `backend-dev`, `frontend-dev`, `platform-dev` (only relevant ones)
3. Spawn `reviewer` — review implementation
   - If CHANGES REQUESTED: retry relevant impl agent(s)
4. Spawn `qa` — run real tests against implementation
   - If FAIL: retry relevant impl agent(s), then re-review and re-qa
5. Spawn quality bench in parallel (after QA PASS):
   - `security-rev`, `privacy-rev`, `perf-eng`, `access-rev`, `integ-qa`
6. Spawn `docs-writer`
7. Spawn `jira-confluence`
8. Spawn `pm-uat` → **Gate 6: UAT Approval**

Each spawn: `Agent(team_name=<squad-team>, name=<role>, subagent_type="claude-tech-squad:<role>", prompt=...)`

Emit: `[Phase Done] implementation | UAT approved`

---

### PHASE 3: RELEASE

Emit: `[Phase Start] release`

After UAT approval, spawn Release and SRE:

**Release Teammate:**

```
Agent(
  team_name = <team>,
  name = "release",
  subagent_type = "claude-tech-squad:release",
  prompt = """
## Release Preparation

### Full Delivery Package
{{complete_implementation_summary}}

### UAT Result
{{pm_uat_output}}

### Architecture and Breaking Changes
{{architect_output}}

---
You are the Release specialist. Inventory all changes, validate CI/CD and deploy
assumptions, define rollback steps, and identify required communication and monitoring.
Return a release checklist with go/no-go recommendation.
"""
)
```

Emit: `[Teammate Spawned] release | pane: release`

**SRE Teammate (after Release):**

```
Agent(
  team_name = <team>,
  name = "sre",
  subagent_type = "claude-tech-squad:sre",
  prompt = """
## SRE Sign-off

### Release Plan
{{release_output}}

### Architecture
{{architect_output}}

---
You are the SRE specialist. Assess blast radius, SLO impact, rollback readiness,
and canary/phased rollout strategy. Return a final go/no-go recommendation.
"""
)
```

Emit: `[Teammate Spawned] sre | pane: sre`
Emit: `[Phase Done] release | SRE sign-off received`

---

## Final Output

```
## Squad Complete

### Agent Execution Log
- Team: squad
- Phase: discovery
  - Teammate: pm | Status: completed
  - Teammate: ba | Status: completed
  - Teammate: po | Status: completed (Gate 2 passed)
  - Teammate: planner | Status: completed (Gate 3 passed)
  - Teammate: architect | Status: completed
  - Teammate: techlead | Status: completed (Gate 4 passed)
  - Batch: specialist-bench | Teammates: [...] | Status: completed
  - Batch: quality-baseline | Teammates: [...] | Status: completed
  - Teammate: design-principles | Status: completed
  - Teammate: test-planner | Status: completed
  - Teammate: tdd-specialist | Status: completed (Gate 5 passed)
- Phase: implementation
  - Teammate: tdd-impl | Status: failing tests written
  - Batch: implementation | Teammates: [...] | Status: completed
  - Teammate: reviewer | Status: APPROVED
  - Teammate: qa | Status: PASS
  - Batch: quality-bench | Teammates: [...] | Status: completed
  - Teammate: docs-writer | Status: completed
  - Teammate: jira-confluence | Status: completed
  - Teammate: pm-uat | Status: APPROVED (Gate 6 passed)
- Phase: release
  - Teammate: release | Status: completed
  - Teammate: sre | Status: GO

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
- Review: APPROVED
- QA: PASS
- Specialist reviews: [summary]
- Docs: updated
- Jira / Confluence: updated
- UAT: APPROVED

### Release
- Release plan: completed
- SRE sign-off: GO
- Breaking changes: [...]
- Rollback plan: defined

### Stack Validation
- Docs checked via context7 for: [...]
```
