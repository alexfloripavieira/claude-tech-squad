---
name: discovery
description: This skill should be used when starting a new feature, epic, or initiative that needs structured planning before implementation — produces product definition, prioritization, business analysis, architecture, specialist design notes, TDD delivery guidance, quality baselines. Trigger with "rodar discovery", "planejamento de feature", "blueprint do projeto", "/discovery", "discovery and blueprint", "antes de implementar", "discovery phase", "epic planning", "kickoff técnico". Uses the full specialist bench (PM, PO, BA, architects, test-planner, tdd-specialist) — each as independent teammate. NOT for direct implementation (use /implement) or full end-to-end (use /squad).
user-invocable: true
---

# /discovery — Discovery & Blueprint

Run the planning phases before implementation. Each specialist runs as an independent teammate in its own tmux pane.

## Global Safety Contract

**Applies to every teammate spawned by this workflow. Violating it requires explicit written user confirmation.**

No teammate may, under any circumstances:
- Execute destructive SQL (`DROP`, `TRUNCATE`) without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3, databases, clusters, queues) in production or run app-deletion commands (`tsuru app-remove`, `heroku apps:destroy`)
- Merge to `main`/`master`/`develop` without an approved PR, or force-push to a protected branch
- Remove production secrets/env vars, or destroy infra via `terraform destroy`
- Disable or bypass auth as a workaround
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input
- Apply production migrations without a verified backup

If a task requires any of these, STOP and surface to the user. Speed never overrides this contract.

## Core Principle

All technical decisions must be grounded in the repository's real stack, conventions, and current documentation via context7.

## Teammate Architecture

This workflow creates a team and spawns each specialist as a real teammate (separate tmux pane):

1. `TeamCreate` — create the discovery team
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist
3. `SendMessage` — communicate with running teammates
4. `TaskCreate` + `TaskUpdate` — assign and track work per teammate

Do NOT use `Agent` without `team_name` — that runs an inline subagent, not a visible teammate pane.

## Inter-Teammate Cross-Talk Protocol

Teammates MUST exchange `SendMessage` with each other — not only with the lead — before reporting their `result_contract`. Lead does NOT relay. Required by `runtime-policy.yaml::agent_teams.cross_talk_protocol`. Enforcement is **mode-aware**: `teammate` mode opens a blocking gate on missing pairs; `inline` mode (tmux unavailable) downgrades to warning-only and the pipeline continues. Mode is resolved at preflight by `${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh` (`hard_requirement: true`).

**Required pairs (discovery):**
- `pm` ↔ `business-analyst` (scope alignment)
- `architect` ↔ `backend-architect` (architectural debate)
- `architect` ↔ `data-architect` (data boundary debate)
- `test-planner` ↔ `tdd-specialist` (test strategy alignment)
- `security-reviewer` ↔ `privacy-reviewer` (adversarial review)

**Spawn-prompt rule:** every spawn prompt MUST include a `peers:` block listing the teammate names this teammate must message before completing.

**Audit:** lead dumps the team mailbox to `sep_log.mailbox[]`. A teammate returning `result_contract` with zero outbound `SendMessage` to a required peer triggers the Teammate Failure Protocol with `reason: cross-talk-missing` and opens `[Gate] Cross-Talk Missing | pair: <a>↔<b> | [R]espawn / [A]ccept / [X]Abort`.

## Operator Visibility Contract

The orchestrator emits structured `[Tag]` lines (Preflight, Team Created, Teammate Spawned/Done/Retry, Fallback Invoked, Checkpoint Saved, Gate, Batch Spawned/Completed, Resume From, etc.) so `/dashboard` and `/factory-retrospective` can parse runs.

> See `references/visual-reporting.md` for the full list of operator visibility lines and renderer integration.

## Progressive Disclosure — Context Digest Protocol

Detailed reference docs that would bloat this SKILL.md live under `references/`:

- `references/arc-schema.md` — ARC schema and validation rules for analysis-class teammates
- `references/gates-catalog.md` — every discovery gate and auto-advance rules
- `references/runtime-resilience.md` — retry, fallback, doom-loop, health-check, rollover, checkpoint detail
- `references/visual-reporting.md` — teammate cards, pipeline board, operator visibility lines
- `references/teammate-roster.md` — phase-by-phase agent spawn templates

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
- Sequential agents (PM → BA → PO → Planner → Architect → TechLead): each receives a digest of the prior agent's output plus the full output of the immediately preceding agent only.
- Parallel batch agents (specialist-bench, quality-baseline): each receives only context relevant to its specialty.
- Agents that explicitly need full upstream output (TechLead needs full Architect; Architect needs full Planner) receive it in addition to digests of earlier phases.
- The orchestrator tracks token consumption per teammate and logs it in the SEP log.

## Agent Result Contract (ARC)

A teammate response is structurally valid only when it contains the role-specific body, a plan section (`## Pre-Execution Plan` or `## Analysis Plan`), a final `result_contract` block, and a final `verification_checklist` block. Missing either block triggers the Teammate Failure Protocol.

> See `references/arc-schema.md` for the full ARC schema, required fields, and validation rules.

## Runtime Resilience Contract

Load `${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml` before creating the team — it is the source of truth for retry budgets, fallback matrix, severity policy, checkpoint/resume rules, and reliability metrics. If the file is missing or unreadable, stop the run and surface `[Gate] Runtime Policy Missing`. Do not silently continue with hardcoded defaults.

The contract covers: Teammate Failure Protocol (silent-failure detection, doom-loop check, single retry, fallback matrix lookup, user gate `[R|S|X]`), Inline Health Check after every `[Teammate Done]`, and the Context Rollover Gate at 100k/140k token thresholds.

> See `references/runtime-resilience.md` for the full resilience contract, doom-loop rules, health-check command, and rollover gate.

## Visual Reporting Contract

After every teammate returns, the orchestrator pipes the Result Contract `metrics` JSON to `${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh` and prints the card inline (respecting `observability.teammate_cards.format`). Immediately before writing the SEP log (Step 13c), it assembles the pipeline summary JSON and pipes it to `${CLAUDE_PLUGIN_ROOT}/scripts/render-pipeline-board.sh` (respecting `observability.pipeline_board.enabled`). Renderer failures are non-fatal — log a WARNING in the SEP log and continue.

> See `references/visual-reporting.md` for full templates, schemas, and the operator visibility line catalog.

---

## Orchestration Contract — Mandatory Phases (CTS hard requirement)

The lead orchestrator MUST execute the four phases below in order on every
run of this skill. Skipping any phase is a contract violation. The SEP log
MUST record `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`,
`language_policy_applied: pt-BR`, and `timeouts_observed: [...]`. `scripts/validate.sh`
greps each dev-flow SKILL.md for the phase tags `CTS-PHASE: skill-init`,
`CTS-PHASE: agent-spawn`, `CTS-PHASE: agent-monitor`, `CTS-PHASE: agent-cleanup`,
and `CTS-PHASE: skill-finalize` to enforce wiring.

### Phase A — Skill Branch Init (CTS-PHASE: skill-init)

Run BEFORE any `Agent(...)` call:

```bash
INIT_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/init-skill-branch.sh discovery)
# parse: skill_branch=<...> base_branch=<...> base_commit=<...> watchdog_pid=<...>
```

- Exit 3 → tree dirty → emit `[Preflight Failed] main worktree dirty` and STOP.
- On success emit `[Skill Branch Created] skill_branch=<...> base_branch=<...> base_commit=<...>`.
- A background watchdog daemon is launched and its pid recorded. The watchdog
  enforces the per-agent and per-skill runtime caps as a last-resort safety
  net. THE WATCHDOG DOES NOT REPLACE THE LEAD'S MONITORING DUTY — see Phase B.1.
- Persist `skill_branch` value for Phases B and D.

### Phase B — Per-Agent Spawn Wrap (CTS-PHASE: agent-spawn)

For EVERY `Agent(...)` invocation in this skill (teammate or inline mode):

```bash
SPAWN_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/spawn-agent-worktree.sh discovery <agent_name> <agent_id>)
# parse: path=<...> branch=<...> base=<...> spawned_at=<epoch>
```

The Agent spawn `prompt` MUST begin with, in this exact order:

1. `language_policy.spawn_prompt_preamble` — literal text from `runtime-policy.yaml::language_policy.spawn_prompt_preamble` (pt-BR mandate).
2. The five worktree fields from `runtime-policy.yaml::agent_worktrees.spawn_prompt_inject.fields_appended_to_every_prompt`:
   - `skill_branch: <...>`
   - `worktree_path: <path>`
   - `branch: <branch>`
   - `base_commit: <base>`
   - `instruction: cd into worktree_path before any Read/Edit/Write/Bash. ...`
3. The role-specific spawn prompt body that this SKILL.md defines below.

Emit `[Worktree Spawned] agent=<...> | path=<...> | branch=<...> | spawned_at=<epoch>`.
Record `spawned_at` per agent — Phase B.1 needs it.

### Phase B.1 — Active Monitoring (CTS-PHASE: agent-monitor) — LEAD'S FIRST-LINE DUTY

This is what the orchestrator exists for. The watchdog is the OS-level
backstop; the lead is the first responder.

For every spawned agent the lead MUST:

1. **Track wall-clock since `spawned_at`.** Cap per agent is
   `runtime-policy.yaml::failure_handling.agent_max_runtime_seconds`
   (default 900s = 15 minutes). Skill-level cap is `skill_max_runtime_seconds`
   (default 7200s = 2 hours).

2. **Never block-wait indefinitely on a single agent.** Between status
   checks, do other work (other teammates' messages, gate handling) or
   sleep in short increments — never sit in an unbounded wait. If your
   runtime offers a polling primitive, use it; otherwise emit a status
   probe every ~120s.

3. **Detect stalls.** A teammate is considered stalled if EITHER:
   - wall-clock since `spawned_at` exceeds the per-agent cap, OR
   - no progress signal (SendMessage, tool call, partial output) for >
     `failure_handling.idle_seconds` (default 300s).

4. **On stall:**
   - Emit `[Teammate Timeout] agent=<...> | reason=<runtime_cap|idle> | age_seconds=<n>`.
   - Send `pkill -f -- "--agent-id <agent>@<skill>"` (or equivalent) to
     terminate the agent process.
   - Run `bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <path>`
     to remove the worktree (merge of partial work optional; merge failure
     non-fatal here).
   - Decrement retry budget. If budget remains and the failure mode is
     recoverable, respawn (Phase B again, fresh `spawned_at`). Otherwise
     open `[Gate] Teammate Failure | agent=<...> | reason=timeout |
     [R]espawn / [S]kip / [X]Abort`.
   - Append `{agent, reason, age_seconds, action}` to the SEP log's
     `timeouts_observed[]`.

5. **Never wait for human input from a subagent.** If a subagent emits a
   recovery prompt ("What should Claude do instead?"), the lead treats it
   as `reason=idle` and triggers the stall handler. Subagents MUST NOT
   block the skill on interactive prompts.

The watchdog daemon spawned in Phase A enforces the same caps independently;
if the lead misses a stall (e.g. it crashed or is itself stuck), the
watchdog kills the agent and writes a `.killed` marker. The lead MUST
inspect `ai-docs/.squad-log/.agents/*.killed` on its next tick and reflect
the kill in the SEP log.

### Phase C — Per-Agent Cleanup (CTS-PHASE: agent-cleanup)

Immediately after the Agent returns its `result_contract` (or after Phase
B.1 stall handling, or on skill abort):

```bash
CLEANUP_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <worktree_path>)
```

- Exit 0 → emit `[Worktree Cleanup] agent=<...> | merged=<true|false> | commits_ahead=<n> | branch_deleted=<branch>`.
- Exit 4 → merge conflict → emit `[Worktree Cleanup Conflict]` and open `[Gate] Worktree Merge Conflict | [R]esolve / [A]bort`. Worktree and branch are preserved until the user resolves.

This phase runs ONCE PER AGENT SPAWN (including timed-out spawns) and is non-skippable.

### Phase C.5 — SEP Log Commit (CTS-PHASE: sep-commit)

After the SEP log file is written under `ai-docs/.squad-log/<skill>-<timestamp>.md`
and BEFORE Phase D finalize, the lead MUST commit it on the skill branch.
Without this commit, finalize-skill.sh will see a dirty main worktree and
abort. The skill-active-guard hook is wired to allow these specific git
operations when scoped to `ai-docs/.squad-log/`.

```bash
CTS_LEAD_OK=1 git -C "$REPO_TOPLEVEL" add ai-docs/.squad-log/
CTS_LEAD_OK=1 git -C "$REPO_TOPLEVEL" commit -m "chore(squad-log): discovery SEP log"
```

The lead MUST NOT delegate this step to the user — that defeats the
orchestration contract. If the commit fails, surface a `[Gate] SEP Log
Commit Failed` instead of asking the user to run the commands manually.

### Phase D — Skill Finalize (CTS-PHASE: skill-finalize)

After the last agent finishes, after the SEP log is written and committed,
and before returning control to the user:

```bash
FINAL_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/finalize-skill.sh "$skill_branch")
```

- Exit 0 → emit `[Skill Finalized] skill_branch=<...> | orphan_worktrees=0 | orphan_branches=0`. Sentinel is removed; watchdog exits on its next tick.
- Non-zero → STOP and surface the failing invariant to the user. Do NOT mark the skill complete.

`finalize-skill.sh` does NOT push, merge to base, or delete the skill
branch — that is the user's call.

### Cross-Talk & Language Audit (mandatory checks before SEP write)

- Inspect mailbox: every Required Pair declared in this skill's
  `## Inter-Teammate Cross-Talk Protocol` must have at least one outbound
  `SendMessage`. Empty pair → Teammate Failure with `reason: cross-talk-missing`.
- The lead's user-facing output (gate prompts, narrative reports) MUST
  follow `runtime-policy.yaml::language_policy.lead_to_user_preamble` (pt-BR).
- SEP log MUST contain:
  - `language_policy_applied: pt-BR`
  - `cts_phases_completed: [skill-init, agent-spawn, agent-monitor, agent-cleanup, skill-finalize]`
  - `worktrees: [...]` (one entry per agent spawn with `path`, `branch`, `commits_ahead`, `merged`, `final_status`)
  - `timeouts_observed: [...]` (empty list if none — explicit field required)



## Execution

### Preflight Gate

Emit `[Preflight Start] discovery`. Preferred (saves ~5K tokens):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli preflight --skill discovery --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml --project-root .
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli init --run-id {{feature_slug}} --skill discovery --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml --state-dir .squad-state
```

Returns JSON with `stack`, `ai_feature`, `routing` (`pm_agent`, `techlead_agent`, etc.), `lint_profile`, `token_budget_max`, `resume_from`, `warnings`. If `squad-cli` is unavailable, fall back to manual preflight (read `runtime-policy.yaml`, detect stack from signal files, resolve routing, check resumable prior runs).

**Ticket Intake** — If user input matches `[A-Z]+-[0-9]+`, `#[0-9]+`, or `LIN-[0-9]+`: read the ticket via the appropriate MCP tool, extract title/description/acceptance criteria/priority/subtasks/labels/comments, use as `{{user_request}}`, emit `[Ticket Read] {{source}} | {{ticket_id}} | type={{issue_type}} | priority={{priority}}`. If MCP is unavailable, ask the user to paste the ticket — do not block.

Emit warnings, then: `[Preflight Passed] discovery | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`.

### Checkpoint / Resume Rules

Discovery checkpoints in order: `preflight-passed`, `gate-1-approved`, `gate-2-approved`, `gate-3-approved`, `gate-4-approved`, `specialist-bench-complete`, `quality-baseline-complete`, `blueprint-confirmed`.

Preferred:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli checkpoint save --run-id {{feature_slug}} --cursor <checkpoint> --state-dir .squad-state
```

Manual fallback: emit `[Checkpoint Saved] discovery | cursor=<checkpoint>` and track state in run notes.

> See `references/runtime-resilience.md` for resume semantics and auto-advance rules.

### Step 1 — Repository Recon and Variable Extraction

Read `CLAUDE.md` and `README.md`. Note architecture patterns and constraints. Stack/routing/lint detection are resolved by the preflight CLI; the JSON contains `stack`, `routing`, `lint_profile`, `ai_feature`.

Extract and store: `{{feature_slug}}` (kebab-case from request or ticket ID), `{{user_request_one_line}}`, `{{architecture_style}}` (defaults to `existing-repo-pattern`), `{{lint_profile}}`.

Emit: `[Stack Detected] {{detected_stack}} | pm={{pm_agent}} | techlead={{techlead_agent}}`.

### Step 2 — Create Discovery Team

Call `TeamCreate` with `name="discovery"` and `description="Discovery and blueprint session for: {{user_request_one_line}}"`. Emit `[Team Created] discovery`.

### Step 2b — Scope Confirmation Gate (Gate 0)

If the request involves multiple API versions, multiple features, or ambiguous scope, present a scope confirmation gate before spawning PM. Otherwise skip silently.

> See `references/gates-catalog.md` (Gate 0 section) for trigger conditions and the prompt template.

### Step 2c — PRD Author (Phase 0)

Reuse `ai-docs/prd-{{feature_slug}}/prd.md` if it validates against `templates/prd-template.md`. Otherwise spawn `prd-author`. On `confidence: low` with `gaps_count > 0`, open `[Gate] PRD Confidence Low`. Record checkpoint `prd-produced`.

> See `references/teammate-roster.md` (Phase 0) for the spawn template.

### Step 3 — PM Teammate (Gate 1)

Spawn PM (`subagent_type: "claude-tech-squad:{{pm_agent}}"`) as a teammate with stack, project structure, CLAUDE.md summary, and `{{user_request}}`. Present output as **Gate 1: Product Definition**. If the user is unsatisfied, ask what is missing and re-spawn PM with that gap as context.

> See `references/teammate-roster.md` (Phase 1) for the full prompt and `references/gates-catalog.md` for Gate 1 criteria.

### Step 4 — Business Analyst Teammate

Spawn BA (`subagent_type: "claude-tech-squad:business-analyst"`) with PM output and repo context. Returns structured business rules and operational edge cases.

> See `references/teammate-roster.md` (Phase 2) for the prompt.

### Step 5 — PO Teammate (Gate 2)

Spawn PO (`subagent_type: "claude-tech-squad:po"`) with full BA output + PM digest. Present output as **Gate 2: Scope Validation**.

> See `references/teammate-roster.md` (Phase 3) and `references/gates-catalog.md` for Gate 2 criteria.

### Step 6 — Planner Teammate (Gate 3)

Spawn Planner (`subagent_type: "claude-tech-squad:planner"`) with full PO output + PM/BA digests + repo context. Present output as **Gate 3: Technical Tradeoffs** — user selects the preferred implementation path.

> See `references/teammate-roster.md` (Phase 4) and `references/gates-catalog.md` for Gate 3 criteria.

### Step 7 — Architect Teammate

Spawn Architect (`subagent_type: "claude-tech-squad:architect"`) with full Planner output + PM/BA/PO digests + repo context + `{{architecture_style}}`. Architect preserves the repository's current pattern unless there is a strong reason to adopt another style.

> See `references/teammate-roster.md` (Phase 5) for the prompt.

### Step 8 — TechLead Teammate (Gate 4)

Spawn TechLead (`subagent_type: "claude-tech-squad:{{techlead_agent}}"`) with full Architect output + PM/BA/PO/Planner digests. TechLead returns the execution plan and the required specialist set. Present as **Gate 4: Architecture Direction**.

> See `references/teammate-roster.md` (Phase 6) and `references/gates-catalog.md` for Gate 4 criteria and the specialist option list.

### Step 9 — Specialist Batch (Parallel)

Spawn relevant specialists in parallel based on TechLead's list (only those that apply). Each gets full TechLead plan + full Architect output + PO digest + repo context + earlier-phase digests. Wait for ALL agents; apply the Teammate Failure Protocol per silent failure. Emit `[Batch Spawned]` and `[Batch Completed] specialist-bench | N/N agents returned`.

> See `references/teammate-roster.md` (Phase 7) for the spawn list and prompt rules.

### Step 10 — Quality Baseline Batch (Parallel)

**Auth-sensitive HARD gate (MANDATORY):** if the feature touches auth flows, magic-link/OTP, OAuth/SSO, password reset, account recovery, impersonation, or session token storage/refresh/revocation, `security-reviewer` is a HARD gate — CANNOT be skipped-with-risk and CANNOT be auto-advanced. Record `auth_touching_feature: true` and `security_reviewer_gate: hard` in SEP frontmatter.

Spawn the relevant reviewers (`security-reviewer`, `privacy-reviewer`, `compliance-reviewer`, `performance-engineer`, `observability-engineer`) in parallel. Each receives full architecture decisions + relevant specialist notes + PO digest + repo context. Wait for ALL.

> See `references/teammate-roster.md` (Phase 8) and `references/gates-catalog.md` (Auth-Sensitive HARD Gate).

### Step 11 — Design Principles Teammate

Spawn `design-principles-specialist` with full Architect output + full specialist notes + repo context + `{{architecture_style}}`. Returns guardrails for implementation.

> See `references/teammate-roster.md` (Phase 9) for the prompt.

### Step 12 — Test Planner Teammate

Spawn `test-planner` with full Design Principles output + full TechLead plan + architecture/PO digests. Maps acceptance criteria to unit, integration, e2e, regression, manual validation using the repository's real test stack only.

> See `references/teammate-roster.md` (Phase 10) for the prompt.

### Step 12b — Feature Flag Assessment

Before spawning the TDD Specialist, decide whether the feature requires a flag (rollout / safety / experiment / entitlement). Store `{{feature_flag_strategy}}` (or set to "No flag required — full rollout on deploy"). Emit `[Feature Flag] Required — strategy defined` or `[Feature Flag] Not required`.

> See `references/teammate-roster.md` (Phase 10b) for criteria and the strategy template.

### Step 13 — TDD Specialist Teammate (Final Gate)

Spawn `tdd-specialist` with full Test Planner output + full TechLead plan + architecture digest + `{{feature_flag_strategy}}`. If a flag is required, the TDD plan must include cycles for both flag=false and flag=true paths. Present output as **Final Gate: Blueprint Confirmation**.

> See `references/teammate-roster.md` (Phase 11) for the prompt.

### Step 13b — ADR Generation (proactive, post-Gate 4)

After blueprint confirmation, automatically generate Architecture Decision Records for every significant decision (techlead, architect, specialist tradeoffs). Do NOT ask the user.

```bash
mkdir -p ai-docs/{{feature_slug}}/adr
```

Write one file per decision to `ai-docs/{{feature_slug}}/adr/ADR-NNN-{{slug}}.md` with sections: Context, Decision, Alternatives Considered (table), Consequences (Positive / Negative / Risks). Emit `[ADRs Generated] N decisions recorded in ai-docs/{{feature_slug}}/adr/`.

### Step 13c — Run Cost Summary and SEP Log

Preferred (uses real token counts):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli cost --run-id {{feature_slug}} --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml --state-dir .squad-state
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli sep-log --run-id {{feature_slug}} --output-dir ai-docs/.squad-log --state-dir .squad-state
```

Emit: `[Run Summary] /discovery | teammates: {{N}} | tokens: {{total_input}}K in / {{total_output}}K out | est. cost: ~${{usd}} | duration: {{elapsed}}`.

If `squad-cli` is unavailable: sum tokens manually, estimate cost, write the SEP log to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-discovery-{{run_id}}.md` with full YAML frontmatter (parsed programmatically by `/dashboard` and `/factory-retrospective`).

**Required frontmatter fields for discovery SEP logs:**

```yaml
---
run_id: {{run_id}}
skill: discovery
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}
final_status: completed | in_flight | aborted
execution_mode: teammates | inline
architecture_style: {{style}}
checkpoints: [preflight-passed, gate-1-approved, ...]
fallbacks_invoked: []
retry_count: {{N}}
tokens_input: {{actual_or_null}}
tokens_output: {{actual_or_null}}
teammate_token_breakdown: {}
estimated_cost_usd: {{usd}}
total_duration_ms: {{ms}}
implement_triggered: true | false
implement_deferred_reason: {{required_when_implement_triggered_false}}
auth_touching_feature: true | false
security_reviewer_gate: hard | soft | n/a
---
```

`tokens_input` / `tokens_output` must be the actual measurement or `null` — `0` placeholders are forbidden. `teammate_token_breakdown` is a map `{teammate_name: {tokens_in, tokens_out, cost_usd}}`.

Emit `[SEP Log Written] ai-docs/.squad-log/{{filename}}`.

### Step 15 — Discovery → Implement Bridge Gate (SEP Contrato 3)

Always present immediately after the SEP log:

```
Blueprint salvo em ai-docs/{{feature_slug}}/blueprint.md

Próximo passo: /implement ai-docs/{{feature_slug}}/blueprint.md

Quer iniciar a implementação agora? [S/N]
```

- **S**: Edit the SEP log to set `implement_triggered: true`, then invoke `/implement` with the blueprint path.
- **N**: leave `implement_triggered: false` and **populate `implement_deferred_reason`** (mandatory — empty/missing means the SEP is structurally incomplete and `/factory-retrospective` flags it as orphaned). Write `tasks/pending-implement-{{feature_slug}}.md` with blueprint path, run id, date, and the deferral reason. Inform the user: `Registrado em tasks/pending-implement-{{feature_slug}}.md`.

Emit `[Gate] implement-bridge | Waiting for user input`.

> See `references/gates-catalog.md` (Discovery → Implement Bridge Gate) for the full template and field rules.

### Step 16 — Team Cleanup (mandatory epilogue)

After the bridge gate resolves (regardless of choice):

```
TeamDelete(name="discovery")
```

Emit `[Team Deleted] discovery | cleanup complete`. Ignore errors silently. **Why mandatory:** team members persist across session restarts; uncleaned teams break future `TeamCreate` calls (`Already leading team` — discovered in APPS-519 golden run).

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

### 1. Product Definition          [PM output]
### 2. Business Analysis           [BA output]
### 3. Product Prioritization      [PO output]
### 4. Technical Requirements      [Planner output]
### 5. Overall Architecture        [Architect output]
### 6. Tech Lead Execution Plan    [TechLead output]
### 7. Specialist Notes            [Backend, Frontend, Data, UX, API, AI, Integration, DevOps, CI-CD, DBA — each if present]
### 8. Design Principles Guardrails [Design Principles Specialist output]
### 9. Quality, Governance, and Operations Baselines [Security / Privacy / Compliance / Performance / Observability — each if present]
### 10. Test Plan                  [Test Planner output]
### 11. TDD Delivery Plan          [TDD Specialist output]
### 12. Stack & Conventions Observed
- Stack: [...]
- Repo conventions: [...]
- CI / deploy clues: [...]

### 13. Delivery Workstreams
- Backend, Frontend, Data, AI, Integrations, Platform, DevOps-CI-CD, Docs, QA-Reliability
```
