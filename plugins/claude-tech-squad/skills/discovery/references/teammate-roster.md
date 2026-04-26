# Teammate Roster & Spawn Templates — `/discovery`

This file expands the agent-by-agent spawn detail referenced from `SKILL.md`. The orchestrator visits these phases in order. Every spawn uses `subagent_type: "claude-tech-squad:<slug>"`.

## Phase 0 — PRD Author (Step 2c)

Reuse `ai-docs/prd-{{feature_slug}}/prd.md` if it validates against `templates/prd-template.md`. Otherwise spawn `prd-author`.

```
Agent(
  team_name="discovery",
  name="prd-author",
  subagent_type="claude-tech-squad:prd-author",
  prompt=<orchestrator context digest + feature slug + feature description>
)
```

If `confidence: low` and `gaps_count > 0`, open `[Gate] PRD Confidence Low | gaps: <gap_list>`. Record checkpoint `prd-produced`.

## Phase 1 — PM (Gate 1, Step 3)

```
Agent(
  team_name=<team>,
  name="pm",
  subagent_type="claude-tech-squad:{{pm_agent}}",
  prompt="""
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
You are the PM. Define problem statement, user stories, acceptance criteria.
Return structured markdown for handoff to Business Analyst.
Do NOT chain to other agents.
"""
)
```

Gate 1 criteria: ≥3 measurable acceptance criteria, bounded scope, observable success metrics.

## Phase 2 — Business Analyst (Step 4)

```
Agent(team_name=<team>, name="ba", subagent_type="claude-tech-squad:business-analyst", prompt=<PM output + repo context + BA instructions>)
```

## Phase 3 — PO (Gate 2, Step 5)

Progressive Disclosure: PO receives full BA output + PM digest.

```
Agent(team_name=<team>, name="po", subagent_type="claude-tech-squad:po", prompt=<pm_digest + ba_output + PO instructions>)
```

Gate 2 criteria: explicit OUT-of-scope list, must-have vs nice-to-have, single-deployment release slice.

## Phase 4 — Planner (Gate 3, Step 6)

Progressive Disclosure: Planner receives full PO output + digests of PM and BA.

```
Agent(team_name=<team>, name="planner", subagent_type="claude-tech-squad:planner", prompt=<pm_digest + ba_digest + po_output + repo context>)
```

Gate 3 criteria: ≥2 technical options, selected option has rationale, breaking-change/migration risks called out.

## Phase 5 — Architect (Step 7)

Progressive Disclosure: Architect receives full Planner output + digests of PM, BA, PO.

```
Agent(team_name=<team>, name="architect", subagent_type="claude-tech-squad:architect", prompt=<pm/ba/po digests + planner_output + repo context + architecture_style>)
```

Architect must preserve the repository's current pattern unless there is a strong reason to adopt another style. Hexagonal Architecture only when feature/repo explicitly benefits.

## Phase 6 — TechLead (Gate 4, Step 8)

Progressive Disclosure: TechLead receives full Architect output + digests of PM, BA, PO, Planner.

```
Agent(team_name=<team>, name="techlead", subagent_type="claude-tech-squad:{{techlead_agent}}", prompt=<architect_output + planner_digest + pm/ba/po digests + architecture_style>)
```

TechLead must identify which specialists are needed from: backend-architect, hexagonal-architect, frontend-architect, api-designer, data-architect, ux-designer, ai-engineer, integration-engineer, devops, ci-cd, dba.

Gate 4 criteria: workstream ownership assigned, sequencing explicit, architecture-layer violations flagged.

## Phase 7 — Specialist Bench (Step 9, parallel)

Spawn only specialists in TechLead's list:

```
Agent(team_name=<team>, name="backend-arch",   subagent_type="claude-tech-squad:backend-architect",  prompt=...)
Agent(team_name=<team>, name="hexagonal-arch", subagent_type="claude-tech-squad:hexagonal-architect", prompt=...)
Agent(team_name=<team>, name="frontend-arch",  subagent_type="claude-tech-squad:frontend-architect", prompt=...)
Agent(team_name=<team>, name="api-designer",   subagent_type="claude-tech-squad:api-designer",       prompt=...)
Agent(team_name=<team>, name="data-arch",      subagent_type="claude-tech-squad:data-architect",     prompt=...)
Agent(team_name=<team>, name="ux",             subagent_type="claude-tech-squad:ux-designer",        prompt=...)
```

Each specialist receives full TechLead plan + full Architect output + PO digest + repo context + earlier-phase digests. Instruction: "Return your specialist design notes. Do NOT chain to other agents."

Wait for ALL spawned specialists to return. Apply the Teammate Failure Protocol per silent failure.

## Phase 8 — Quality Baseline (Step 10, parallel)

Auth-sensitive HARD gate: if the feature touches authentication flows, magic-link/OTP, OAuth/SSO, password reset, account recovery, impersonation, or session token storage/refresh/revocation, then `security-reviewer` is a HARD gate — CANNOT be skipped-with-risk and CANNOT be auto-advanced. Record `auth_touching_feature: true` and `security_reviewer_gate: hard` in the SEP frontmatter.

```
Agent(team_name=<team>, name="security",     subagent_type="claude-tech-squad:security-reviewer",   prompt=...)
Agent(team_name=<team>, name="privacy",      subagent_type="claude-tech-squad:privacy-reviewer",    prompt=...)
Agent(team_name=<team>, name="compliance",   subagent_type="claude-tech-squad:compliance-reviewer", prompt=...)
Agent(team_name=<team>, name="perf",         subagent_type="claude-tech-squad:performance-engineer",prompt=...)
Agent(team_name=<team>, name="observ",       subagent_type="claude-tech-squad:observability-engineer", prompt=...)
```

Each reviewer receives architecture decisions (full) + relevant specialist notes (full) + PO digest + repo context. Instruction: "Produce a quality baseline checklist. Do NOT chain."

## Phase 9 — Design Principles (Step 11)

```
Agent(team_name=<team>, name="design-principles", subagent_type="claude-tech-squad:design-principles-specialist", prompt=<architect_output + specialist_batch_output + repo context + architecture_style>)
```

Reviews boundaries, dependency direction, cohesion, coupling, testability, Clean Architecture tradeoffs.

## Phase 10 — Test Planner (Step 12)

Progressive Disclosure: full Design Principles output + full TechLead plan + architecture/PO digests.

```
Agent(team_name=<team>, name="test-planner", subagent_type="claude-tech-squad:test-planner", prompt=<architect_digest + techlead_output + po_digest + design_principles_output>)
```

Maps acceptance criteria to unit, integration, e2e, regression, manual validation. Uses repository's real test stack only.

## Phase 10b — Feature Flag Assessment (Step 12b)

Decide whether the feature requires a flag (rollout / safety / experiment / entitlement). If yes, store `{{feature_flag_strategy}}`:

```markdown
**Flag name:** `{{feature_slug}}_enabled`
**Type:** rollout | safety | experiment | entitlement
**Default:** false
**Rollout plan:** internal → staging → 5% → 25% → 100%
**Cleanup:** remove after full rollout stable (suggested 2 sprints)
**Tests required:** flag=false path + flag=true path both covered
```

Otherwise: `"No flag required — full rollout on deploy"`.

## Phase 11 — TDD Specialist (Final Gate, Step 13)

Progressive Disclosure: full Test Planner output + full TechLead plan + architecture digest.

```
Agent(team_name=<team>, name="tdd-specialist", subagent_type="claude-tech-squad:tdd-specialist", prompt=<test_planner_output + techlead_output + architect_digest + feature_flag_strategy>)
```

Converts approved scope into red-green-refactor cycles. If a flag is required, includes test cycles for both flag=false and flag=true paths.

Present output as **Final Gate: Blueprint Confirmation**. Discovery is complete on user confirm.
