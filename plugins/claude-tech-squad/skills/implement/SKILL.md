---
name: implement
description: This skill should be used when an approved discovery/blueprint exists and the team is ready to build — runs implementation, code review, QA, conformance, UAT, and operations gates with separate teammate contexts per phase. Trigger with "implementar feature", "rodar implement", "executar blueprint", "/implement", "build phase", "implementation phase", "construir feature aprovada", "post-discovery build". Uses TDD-first cycles, multi-lens reviewer/QA/conformance gates with retry budgets and checkpoints. NOT for greenfield planning (use /discovery first) or one-shot bug fixes (use /bug-fix).
user-invocable: true
---

# /implement — Build & Quality

Implementation and quality validation from a Discovery & Blueprint Document. Prefer teammate mode, where each specialist runs as an independent teammate in its own tmux pane. If preflight resolves `mode=inline`, the workflow still runs correctly as inline subagents with the same gates, SEP logging, pt-BR language policy, and warning-only cross-talk enforcement.

## Global Safety Contract

Applies to every teammate. Violation requires explicit written user confirmation. No teammate may execute destructive SQL without verified rollback, delete production cloud resources, run app deletion commands, merge to protected branches without an approved PR, force-push protected branches, remove production secrets, run `terraform destroy`, disable auth as a workaround, deploy without a tested rollback, skip pre-commit hooks without authorization, execute `eval()` / dynamic shell injection, apply migrations without a verified backup, or deploy to production before staging passes. Any conflict: STOP and surface to user.

## TDD Execution Rule

If the discovery package came from `/squad` or marks TDD as required, TDD is mandatory: start from failing tests, follow the TDD Delivery Plan, state exceptions explicitly.

## Teammate Architecture

Use the execution mode resolved by `${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh`. In `mode=teammate`, use `TeamCreate` then `Agent` with `team_name` + `name` + `subagent_type` to spawn each specialist in its own tmux pane. In `mode=inline`, skip `TeamCreate` and spawn inline subagents while preserving specialist prompts, handoffs, gates, worktree isolation, and SEP logging. Use `SendMessage`, `TaskCreate`, and `TaskUpdate` where the backend supports them.

## Inter-Teammate Cross-Talk Protocol

Teammates MUST exchange `SendMessage` with each other — not only with the lead — before reporting their `result_contract`. Lead does NOT relay. Required by `runtime-policy.yaml::agent_teams.cross_talk_protocol`. Enforcement is **mode-aware**: `teammate` mode opens a blocking gate on missing pairs; `inline` mode (tmux unavailable) downgrades to warning-only and the pipeline continues. Mode is resolved at preflight by `${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh` (`hard_requirement: true`).

**Required pairs (implement):**
- `backend-dev` ↔ `frontend-dev` (cross-layer handoff: API contract, error envelope, fixtures)
- `backend-dev` ↔ `test-automation-engineer` (cross-layer handoff: integration fixtures)
- `frontend-dev` ↔ `test-automation-engineer` (cross-layer handoff: e2e selectors)
- `code-reviewer` ↔ `security-reviewer` (adversarial_review / advogado do diabo: correctness vs security assumptions)
- `code-reviewer` ↔ `performance-engineer` (adversarial_review / advogado do diabo: correctness vs performance trade-offs)

**Advogado do diabo:** pairs marked as `adversarial_review` MUST challenge assumptions, risks, alternatives, missing evidence, and trade-offs directly in pt-BR before synthesis. Record any objection that changes severity, scope, or implementation direction in the SEP log with mitigation and final decision.

**Spawn-prompt rule:** every spawn prompt MUST include a `peers:` block listing the teammate names this teammate must message before completing.

**Audit:** lead dumps the team mailbox to `sep_log.mailbox[]`. A teammate returning `result_contract` with zero outbound `SendMessage` to a required peer triggers the Teammate Failure Protocol with `reason: cross-talk-missing` and opens `[Gate] Cross-Talk Missing | pair: <a>↔<b> | [R]espawn / [A]ccept / [X]Abort`.

## Operator Visibility Contract

Emit one line for every teammate action. Required line types: `[Preflight Start|Warning|Passed]`, `[Team Created]`, `[Teammate Spawned|Done|Retry]`, `[Fallback Invoked]`, `[Resume From]`, `[Checkpoint Saved]`, `[Gate]`, `[Batch Spawned]`, `[Token Usage]`, `[Context Advisory]`, `[Rollover Accepted|Declined]`, `[Health Check]`, `[SEP Log Written]`. Full grammar in `references/runtime-resilience.md` and `references/gates-catalog.md`.

## Progressive Disclosure — Context Digest Protocol

Detailed reference docs live under `references/`:

- `references/arc-schema.md` — canonical Agent Result Contract schema (both legacy and canonical forms)
- `references/gates-catalog.md` — every gate, what it consumes, cycle caps, output contracts
- `references/runtime-resilience.md` — retry budgets, fallback matrix, doom-loop, cost guardrails, Teammate Failure Protocol, Inline Health Check, Context Rollover Gate
- `references/visual-reporting.md` — teammate cards + pipeline board renderer rules
- `references/teammate-roster.md` — full roster with per-phase prompts and digest rules
- `references/checkpoint-rules.md` — checkpoint sequence and resume contract

Do not forward full upstream agent output to every downstream agent. Produce a **context digest** (max 500 tokens) between sequential phases:

```markdown
## Context Digest — {{source_agent}} ({{phase}})
**Key decisions:** {{bullets}}
**Artifacts produced:** {{file_list}}
**Open questions:** {{list_or_none}}
**Blockers:** {{list_or_none}}
**Architecture style:** {{style}}
**Full output reference:** available on request from orchestrator
```

Disclosure rules per phase are tabulated in `references/teammate-roster.md`. The orchestrator tracks token consumption per teammate and logs it in the SEP log.

## Required Input

A Discovery & Blueprint Document. If missing, ask the user to run `/discovery` or paste it.

## Teammate Failure Protocol

A teammate has **failed silently** if it returns empty, errors, or output that does not match the expected format (including a missing `result_contract`). The orchestrator runs: doom-loop check → one identical retry → fallback per `runtime-policy.yaml.fallback_matrix.implement.<name>` → operator gate `[R]etry / [S]kip / [X]Abort`. Sequential skips degrade all downstream teammates and must be warned. Parallel skips log a risk but do not block the batch. Full flow in `references/runtime-resilience.md`.

## Inline Health Check

After every `[Teammate Done]`, run the 6-signal health check (preferred: `python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli health`). It returns `signals_triggered`, `context_enrichment`, `budget_percent`, `is_critical`. Warning signals prepend enrichment to the next teammate; critical signals emit `[Health Warning]`. Full signal list and CLI flags in `references/runtime-resilience.md`.

## Agent Result Contract (ARC)

Every teammate response must contain: the role-specific body, a plan section (`## Pre-Execution Plan` for execution agents, `## Analysis Plan` for analysis agents), a final `result_contract` block, and a final `verification_checklist` block.

Minimum schema (full schema and validation rules in `references/arc-schema.md`):

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
  role_checks_passed: [<role-specific>]
  issues_found_and_fixed: 0
  confidence_after_verification: high | medium | low
```

Missing `result_contract` OR `verification_checklist` triggers the Teammate Failure Protocol. See `references/arc-schema.md` for severity classification, status semantics, and the canonical PASS/FAIL/NEEDS_HUMAN form.

## Visual Reporting Contract

After every teammate returns, pipe its `result_contract.metrics` JSON to `${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh` and print the card inline. Before writing the SEP log, assemble pipeline summary JSON (matching `scripts/test-fixtures/pipeline-board-input.json`) and pipe to `${CLAUDE_PLUGIN_ROOT}/scripts/render-pipeline-board.sh`. Respect `observability.teammate_cards.format` and `observability.pipeline_board.enabled` in `runtime-policy.yaml`. Renderer failures are non-fatal (log WARNING, continue). Full contract in `references/visual-reporting.md`.

## Runtime Resilience Contract

Load `${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml` before command detection or team creation. It is the source of truth for: retry budgets, fallback matrix, severity policy, checkpoint/resume rules, cost guardrails, doom-loop heuristics, auto-advance, entropy management, and reliability metrics recorded in SEP logs.

If the policy file is missing or unreadable, stop and surface `[Gate] Runtime Policy Missing` — never silently fall back to hardcoded defaults. Phase-by-phase retry budgets, fallback matrix, doom-loop patterns, cost guardrails, and auto-advance rules are tabulated in `references/runtime-resilience.md`.

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
INIT_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/init-skill-branch.sh implement)
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
SPAWN_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/spawn-agent-worktree.sh implement <agent_name> <agent_id>)
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
CTS_LEAD_OK=1 git -C "$REPO_TOPLEVEL" commit -m "chore(squad-log): implement SEP log"
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
  - `bypasses_observed: [...]` (one entry per silenced/skipped teammate: `{agent, reason, user_decision: A|R|X, gate_emitted: true}`). EMPTY LIST IF NONE — explicit field required. Marking any agent as "BYPASSED" without a `[Gate] Reviewer Bypass Requested` and explicit user choice is a contract violation. **`user_decision` MUST come from a fresh per-gate chat reply.** Session-level preferences (e.g. "no clarifying questions" directive, autonomous-run mode, prior similar bypass) DO NOT pre-authorize the gate. See `runtime-policy.yaml::failure_handling.bypass_policy.session_preferences_do_not_authorize` and `forbidden_auto_resolutions`.



## Execution

### Preflight Gate

Emit `[Preflight Start] implement`. Preferred path:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli preflight \
  --skill implement --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml --project-root .
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli init \
  --run-id {{feature_slug}} --skill implement \
  --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml --state-dir .squad-state
```

`preflight` returns JSON with `stack`, `ai_feature`, `routing` (`backend_agent`, `frontend_agent`, `reviewer_agent`, `qa_agent`), `lint_profile`, `token_budget_max`, `orphaned_discoveries`, `resume_from`, `warnings`, plus detected `test_command`, `build_command`, `lint_command` from signal files (Makefile, package.json, pyproject.toml, go.mod, Cargo.toml, pom.xml, Gemfile, composer.json, *.csproj, …). Fallback: read `runtime-policy.yaml`, detect stack from signal files, resolve routing manually.

**Ticket Intake** — If user input matches `[A-Z]+-[0-9]+`, `#[0-9]+`, or `LIN-[0-9]+`: read the ticket via the appropriate MCP tool, extract title/description/AC/priority/subtasks/labels/comments, emit `[Ticket Read] {{source}} | {{ticket_id}}`. If MCP unavailable, ask the user to paste the ticket.

**Chain validation** — Check `ai-docs/.squad-log/` for a discovery SEP log matching `{{feature_slug}}`. If missing, emit `[Preflight Warning] no discovery SEP log found`.

**Blueprint staleness preflight (MANDATORY):**

```bash
BLUEPRINT=ai-docs/{{feature_slug}}/blueprint.md
if [ -f "$BLUEPRINT" ]; then
  AGE_DAYS=$(( ( $(date +%s) - $(stat -c %Y "$BLUEPRINT") ) / 86400 ))
fi
```

If `AGE_DAYS > 14`: emit `[Gate Blocked] blueprint-stale | age={{days}} days` and stop. Recommend `/claude-tech-squad:discovery --refresh`. Surface `[R]efresh / [F]orce-continue / [X]Abort`. On `[F]`: record `blueprint_stale_override_reason` in the SEP log.

If detected commands are empty, emit `[Gate] Commands Unknown` and ask the user. Block all agent spawns until confirmed. CLAUDE.md command overrides take priority.

Emit `[Preflight Passed] implement | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version> | stack=<detected_stack>` and `[Stack Detected] {{stack}} | backend={{backend_agent}} | frontend={{frontend_agent}} | reviewer={{reviewer_agent}} | qa={{qa_agent}}`.

### Checkpoint / Resume Rules

Checkpoint sequence: `preflight-passed`, `commands-confirmed`, `blueprint-validated`, `tasks-produced`, `work-items-produced`, `tdd-ready`, `implementation-batch-complete`, `reviewer-approved`, `qa-pass`, `conformance-pass`, `quality-bench-cleared`, `coderabbit-clean`, `docs-complete`, `uat-approved`.

Preferred:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli checkpoint save \
  --run-id {{feature_slug}} --cursor <checkpoint> --state-dir .squad-state
```

Fallback: emit `[Checkpoint Saved] implement | cursor=<checkpoint>`. On resume, `squad-cli preflight` returns `resume_from`; orchestrator emits `[Resume From] implement | checkpoint=<checkpoint>` and skips ahead. Full state-dir layout and resume contract in `references/checkpoint-rules.md`.

### Execution Budgets

Values must match `retry_budgets` in `runtime-policy.yaml`: `review_cycles_max=3`, `qa_cycles_max=2`, `conformance_cycles_max=2`, `quality_fix_cycles_max=2`, `uat_cycles_max=2`. Cycle-cap behaviour and operator gates in `references/gates-catalog.md`.

### Step 1 — Validate Blueprint

Confirm the Discovery & Blueprint Document is present. Extract: `{{feature_slug}}`, `{{acceptance_criteria}}`, `{{test_plan}}`, `{{architecture}}`, `{{architecture_style}}` (default `existing-repo-pattern`).

**Blueprint Completeness Gate (blocking):**

| Field | Severity |
|---|---|
| `acceptance_criteria` | BLOCKING |
| `architecture` | BLOCKING |
| `test_plan` | WARNING |
| `feature_slug` | WARNING |

If any BLOCKING is missing: emit `[Gate] Blueprint Incomplete` and surface `[D]iscovery / [P]rovide-fields / [F]orce`. `[F]` logs `blueprint_completeness: forced` and prepends a warning to every downstream prompt. WARNING-only: emit advisory and derive defaults.

### Step 2 — Create Implementation Team

`TeamCreate(name="implement", description="Implementation run for: {{feature_or_task_one_line}}")`. Emit `[Team Created] implement`.

### Step 2b — Delivery Docs (Phase 0)

Verify `ai-docs/prd-{{feature_slug}}/prd.md` and `techspec.md`. If missing: `[Gate] Delivery Docs Missing | Run /discovery and /inception first`. If `tasks.md` exists and validates against `templates/tasks-template.md`, reuse; else spawn `tasks-planner` (`subagent_type: claude-tech-squad:tasks-planner`). Then spawn `work-item-mapper` (`subagent_type: claude-tech-squad:work-item-mapper`) with taxonomy from `runtime-policy.yaml`. If `delivery_gates.enabled: true` and any BLOCKING finding returned, open user gate. Pipe both teammates' `metrics` JSON through `render-teammate-card.sh`. Save checkpoints `tasks-produced` and `work-items-produced`.

### Test Gate (Mandatory)

This skill is in `mandatory_test_gate.skills_in_scope` (see `runtime-policy.yaml#mandatory_test_gate`).

Contract:
- `tdd-specialist` MUST be spawned before any dev agent.
- `test-automation-engineer` MUST be spawned after dev agents and before reviewer agents.
- After `test-automation-engineer` completes, the PostToolUse hook `hooks/test-gate.sh` evaluates the gate. A `BLOCKING` verdict halts the pipeline; the operator decides skip+debt, write manual, or abort.
- No exemption is available for this skill. Any pipeline producing a new or modified production file without a paired test will block.

### Step 3 — TDD Specialist (Failing Tests First)

```
Agent(team_name=<team>, name="tdd-specialist", subagent_type="claude-tech-squad:tdd-specialist",
  prompt="Write the first failing tests for the first delivery slice using red-green-refactor; do NOT write production code. Inputs: full TDD Delivery Plan + full Test Plan + architecture digest (max 500 tokens) + {{architecture_style}}.")
```

Wait for completion; confirm failing tests are in place.

### Step 4 — Implementation Batch (Parallel)

Spawn relevant impl agents in parallel using the Preflight routing table. Only spawn workstreams in scope:

```
Agent(team_name=<team>, name="backend-dev",  subagent_type="claude-tech-squad:{{backend_agent}}",  prompt=...)
Agent(team_name=<team>, name="frontend-dev", subagent_type="claude-tech-squad:{{frontend_agent}}", prompt=...)
Agent(team_name=<team>, name="platform-dev", subagent_type="claude-tech-squad:platform-dev",       prompt=...)
```

Emit `[Batch Spawned] implementation | Teammates: <list>`. Each prompt includes: full TechLead workstream, architecture relevant to layer (full), failing tests (full), domain specialist notes (full), blueprint context (digest), `{{test_command}}`/`{{build_command}}`, `{{lint_profile}}`, `{{architecture_style}}`, design-principles guardrails, instruction "implement until failing tests pass; do NOT chain".

**SEP Contrato 4 — Task Status Protocol:** each impl agent must (1) confirm which task slice it implements, (2) verify `{{test_command}}` passes, (3) return:

```
## Completion Block
- Task: {{task_name}}
- Status: completed
- Files changed: [list]
- Tests run: {{test_command}} → PASS/FAIL
- Test count: N passed, M failed
```

Wait for all impl teammates to complete. Per-teammate digest rules in `references/teammate-roster.md`.

### Step 4b — Test Automation Engineer (Post-Impl)

```
Agent(team_name=<team>, name="test-automation-engineer", subagent_type="claude-tech-squad:test-automation-engineer",
  prompt="Validate test coverage for files modified in this implementation phase. Add edge-case tests for any new branches. Pair every new/modified production file with a test. Report unpaired files in your Result Contract.")
```

Wait for completion. The PostToolUse `hooks/test-gate.sh` then evaluates the gate.

### Step 5 — Reviewer

Spawn `reviewer` (`subagent_type: claude-tech-squad:{{reviewer_agent}}`) with: full diff, architecture digest, `{{architecture_style}}`, `{{lint_profile}}`, project commands, test plan digest. Reviewer output contract (full): `## Findings`, `## Pre-existing Findings` (Major/Minor), final verdict `APPROVED` or `CHANGES REQUESTED: <items>`, ARC blocks. Cycle cap = 3 → fallback `code-reviewer` → `[Gate] Review Limit Reached` (`[A]ccept / [S]kip / [X]Abort`). See `references/gates-catalog.md`.

### Step 5b — Pre-existing Findings Triage

If reviewer flagged any **Major** pre-existing findings: `[Gate] Pre-existing Findings | N Major issue(s)`, surface `[T]icket / [S]kip / [X]Abort`. `[T]` spawns `jira-confluence-specialist` to create one Jira subtask per Major finding. Record `pre_existing_findings_triaged: ticketed | skipped | none`. Minor-only: auto-advance. Emit `[Checkpoint Saved] implement | cursor=reviewer-approved`.

### Step 6 — QA

Spawn `qa` (`subagent_type: claude-tech-squad:{{qa_agent}}`) with: implementation digest (run tests, don't review code), full AC, full test plan, `{{test_command}}`. QA returns PASS or FAIL + diagnosis. Cycle cap = 2 → fallback `qa-tester` (Playwright path) → `[Gate] QA Limit Reached`.

### Step 6b — TechLead Conformance Audit

**MANDATORY GATE — Quality Bench MUST NOT start until CONFORMANT. Never skippable.** Spawn `techlead-audit` (`subagent_type: claude-tech-squad:techlead`) with: TechLead execution plan, architect output, TDD plan, `{{architecture_style}}`, AC, aggregated implementation, QA output. Audit checks: workstream coverage, architecture conformance, TDD compliance, requirements traceability, technical debt introduced. Required output format and NON-CONFORMANT cycle (cap=2 → fallback → `[Gate] Conformance Limit Reached`) in `references/gates-catalog.md`.

### Step 7 — Quality Bench (Parallel, Mandatory)

**MANDATORY GATE — Step 8 MUST NOT start until ALL bench agents return a structured checklist. Skipping FORBIDDEN.** Spawn in parallel (only those relevant): `security-reviewer`, `privacy-reviewer`, `performance-engineer`, `accessibility-reviewer`, `integration-qa`, `code-quality` (must include `{{lint_command}}` + full diff). **Load test agent** (conditional): spawn if HTTP endpoints, queues, batch jobs, or variable-volume operations are touched — baseline + 3x stress + 10x spike plan, slowest query / highest memory / bottleneck, p99 latency + error-rate AC, ready-to-run scripts when k6/locust/Artillery/JMeter is present.

Each reviewer returns a structured checklist. Failure recovery (retry → fallback → consolidated batch-failure gate `[R]/[1,3]/[S]/[X]`) in `references/runtime-resilience.md`. Then `[Gate] Quality Bench Complete`.

### Step 7b — Quality Bench Issue Resolution

Findings classified BLOCKING / WARNING / INFO. BLOCKING path: spawn impl agents per affected domain to fix only listed issues; re-spawn only the bench agents that flagged blocking findings; cycle cap = 2 → `[Gate] Quality Bench Unresolved`. WARNING/INFO: surface `[A]ccept / [F]ix-then-advance`. Severity definitions and the fix-prompt template in `references/gates-catalog.md`.

### Step 7c — CodeRabbit Final Review Gate

Deterministic second-lens review (tool, not LLM). Run `bash ${CLAUDE_PLUGIN_ROOT}/bin/coderabbit_gate.sh`.

| Exit | Action |
|---|---|
| `0` | `[Gate] CodeRabbit Final Review | clean or skipped` → advance |
| `2` | findings → re-spawn `reviewer-coderabbit` with `{{coderabbit_findings}}`; max 2 cycles |
| `1` | error → `[Gate Error]` `[R]etry / [S]kip / [X]Abort` |

Persistent findings after 2 cycles: `[Gate] CodeRabbit Final Review Unresolved | [A]ccept-with-tech-debt / [X]Abort`. Emit `[Checkpoint Saved] implement | cursor=coderabbit-clean`.

### Step 8 — Docs Writer

Spawn `docs-writer` (`subagent_type: claude-tech-squad:docs-writer`) with: full implementation, architecture digest, full AC, test-plan digest, QA digest, conformance digest, quality-bench digest. Map each AC to implemented behaviour and the test that covers it. Return docs delta or updated files.

### Step 9 — Jira/Confluence

Spawn `jira-confluence` (`subagent_type: claude-tech-squad:jira-confluence-specialist`) with the implementation summary + docs delta. Update Jira tickets and Confluence pages.

### Step 9b — Coverage Gate

Detect coverage tool (`coverage report` / `pytest --cov` for Python; `nyc` / `vitest --coverage` for JS). If delta < 0 from blueprint baseline (or `main`): `[Gate] Coverage Drop` with `[C]ontinue / [T]ests-first`. `[T]` re-runs QA. Tool unavailable or delta ≥ 0: silent advance.

### Step 10 — PM UAT Gate

Spawn `pm-uat` (`subagent_type: claude-tech-squad:pm`) with: full AC + digests of QA / conformance / quality bench. PM validates evidence per AC (criterion → evidence → PASS or MISSING) and returns `APPROVED` or `REJECTED` with gaps. Emit `[Gate] UAT | Waiting for user input`.

REJECTED path: surface gaps, offer `[R]e-queue / [S]kip`. `[R]` re-runs Steps 5–10 with `## UAT Rejection Feedback` prepended. Cycle cap = 2 → fallback → `[Gate] UAT Limit Reached` (`[A]ccept / [X]Abort`). Run completes when user approves UAT or chooses `[S]`.

### Step 10a — Team Cleanup

Before SEP log: `TeamDelete(name="implement")`. Capture into `{{team_cleanup_status}}` (`success` or `failed: <reason>`). On failure, emit `[Team Cleanup Warning]` and continue.

### Step 10b — Run Cost Summary and SEP Log

Preferred (uses real token counts):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli cost --run-id {{feature_slug}} \
  --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml --state-dir .squad-state
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli sep-log --run-id {{feature_slug}} \
  --output-dir ai-docs/.squad-log --state-dir .squad-state
```

Emit `[Run Summary] /implement | teammates: {{N}} | tokens: {{in}}K in / {{out}}K out | est. cost: ~${{usd}} | duration: {{elapsed}}`.

Retro counter increment:

```bash
COUNTER_FILE="ai-docs/.squad-log/.retro-counter"
CURRENT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
echo "$((CURRENT + 1))" > "$COUNTER_FILE"
```

Fallback (manual): sum tokens, estimate cost at input × $15/M + output × $75/M, write SEP log to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-implement-{{run_id}}.md`. Substitute every `{{...}}` placeholder — including `{{team_cleanup_status}}` (never leave the literal placeholder).

Required frontmatter:

```yaml
---
run_id: {{run_id}}
skill: implement
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}
final_status: completed | in_flight | aborted
execution_mode: teammates | inline
tokens_input: {{actual_or_null}}
tokens_output: {{actual_or_null}}
teammate_token_breakdown: {}
estimated_cost_usd: {{usd}}
total_duration_ms: {{ms}}
blueprint_stale_override_reason: null
team_cleanup_status: {{team_cleanup_status}}
---
```

Emit `[SEP Log Written] ai-docs/.squad-log/{{filename}}`.

---

## Output: Implementation Report

```
## Implementation Complete

### Agent Execution Log
- Team: implement
- tdd-specialist / impl batch / reviewer / qa / quality-bench / docs-writer / jira-confluence / pm-uat — statuses

### Build
- Workstreams, files changed, TDD cycle, review, QA results

### Quality
- Security / Privacy / Performance / Accessibility / Integration QA summaries
- Documentation, Jira/Confluence, UAT verdict

### Evidence
- Tests run, AC validated, outstanding issues
```
