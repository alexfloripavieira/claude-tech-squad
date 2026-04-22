---
name: implement
description: Run build and quality for any software project based on a prior discovery document. Supports a full specialist bench across implementation, quality, operations, and delivery artifacts.
---

# /implement — Build & Quality

Run implementation and quality validation using the Discovery & Blueprint Document produced by `/discovery`.
Each specialist runs as an independent teammate in its own tmux pane.

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
- Deploy to production without a documented and tested rollback plan
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists
- Deploy to production before staging has been successfully deployed and verified

If any teammate believes a task requires one of these actions, it must STOP and surface the decision to the user before proceeding. The urgency of an implementation deadline does not override this contract.

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

- `[Preflight Start] <workflow-name>`
- `[Preflight Warning] <summary>`
- `[Preflight Passed] <workflow-name> | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`
- `[Team Created] <team-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <review or validation failure>`
- `[Fallback Invoked] <failed-role> -> <fallback-subagent> | Reason: <summary>`
- `[Resume From] <workflow-name> | checkpoint=<checkpoint>`
- `[Checkpoint Saved] <workflow-name> | cursor=<checkpoint>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`
- `[Token Usage] run=<run_id> | used=<N>k | threshold=100k`
- `[Context Advisory] run=<run_id> | recommend=finish-current-gate-then-rollover`
- `[Gate] Context Rollover Required | run=<run_id> | used=<N>k | options=[R|D|F]`
- `[Rollover Accepted] run=<run_id> | handoff=<artifact-path>`
- `[Rollover Declined] run=<run_id> | reason=<user-text>`

## Context Rollover Gate

Between every teammate completion and the next teammate spawn, inspect cumulative token usage. Emit `[Token Usage]` at each phase boundary.

- If `used >= 100k`: emit `[Context Advisory]`. Continue, but plan the next teammate as the last before rollover.
- If `used >= 140k`: emit `[Gate] Context Rollover Required` and halt for operator choice `[R|D|F]`:
  - `R` — Rollover now. Spawn `context-summarizer` as a teammate; then halt for `/clear` + `/resume-from-rollover <run_id>`.
  - `D` — Defer one phase. Proceed one more teammate only, then force rollover.
  - `F` — Force continue. Emit `[Rollover Declined]` with operator reason. Degradation risk accepted and logged.

Thresholds and summarizer agent declared in `runtime-policy.yaml` under `context_management`. Checks only at boundaries, never mid-teammate. Rationale: `docs/architecture/0001-context-rollover.md`.

---

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
- Implementation agents receive the full TDD failing tests + their specific workstream from the TechLead plan, but only a digest of the blueprint (not the entire discovery document)
- Reviewer receives the full implementation diff but only a digest of the architecture decisions
- QA receives the full test plan and acceptance criteria but only a digest of the implementation
- Quality bench agents each receive only the implementation diff relevant to their specialty plus a digest of the architecture
- Docs-writer receives full implementation output but only digests of quality bench findings
- PM UAT receives full acceptance criteria + a digest of QA results and quality bench findings
- The orchestrator tracks token consumption per teammate and logs it in the SEP log

---

## Required Input

This command expects a Discovery & Blueprint Document (from `/discovery` or `/squad`).
If not available, ask the user to run `/discovery` first or paste the blueprint.

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
   - Read `plugins/claude-tech-squad/runtime-policy.yaml` and consult `fallback_matrix.implement.<name>`
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

After every `[Teammate Done]`, run the health check (6 signals: retry_detected, fallback_used, doom_loop_short_circuit, token_budget_pressure, low_confidence_chain, blocking_findings_accumulating).

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

Returns JSON with `signals_triggered`, `context_enrichment` (text to prepend to next teammate), `budget_percent`, `is_critical`. Use `context_enrichment` directly.

If `squad-cli` is not available: evaluate the 6 signals manually from the teammate's `result_contract`.

- Emit: `[Health Check] <name> | signals: <triggered_signals_or_ok>`
- **warning signals**: prepend context enrichment to next teammate
- **critical signals**: emit `[Health Warning]` and surface to user

This is especially critical in `/implement` where the pipeline is long. A problem detected at review can be communicated to QA before it runs, reducing wasted cycles.

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

## Visual Reporting Contract

- After every teammate returns, pipe its Result Contract `metrics` JSON to `plugins/claude-tech-squad/scripts/render-teammate-card.sh` and print the card inline. Respect `observability.teammate_cards.format` (ascii | compact | silent) from `runtime-policy.yaml`.
- Immediately before writing the SEP log, assemble the pipeline summary JSON (schema identical to `scripts/test-fixtures/pipeline-board-input.json`) and pipe to `plugins/claude-tech-squad/scripts/render-pipeline-board.sh`. Respect `observability.pipeline_board.enabled`.
- Renderer failures are non-fatal: log a WARNING in the SEP log and continue.

## Runtime Resilience Contract

Load `plugins/claude-tech-squad/runtime-policy.yaml` before command detection or team creation. This file is the source of truth for:
- retry budgets
- fallback matrix
- severity policy
- checkpoint/resume rules
- reliability metrics recorded in SEP logs

If the runtime policy file is missing or unreadable, stop the run and surface `[Gate] Runtime Policy Missing`. Do not silently continue with hardcoded defaults.

---

## Execution

### Preflight Gate

Emit `[Preflight Start] implement`

**python3 plugins/claude-tech-squad/bin/squad-cli accelerated preflight** (preferred — saves ~5K tokens, detects stack + commands + routing automatically):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli preflight --skill implement --policy plugins/claude-tech-squad/runtime-policy.yaml --project-root .
```

Returns JSON with `stack`, `ai_feature`, `routing` (backend_agent, frontend_agent, reviewer_agent, qa_agent), `lint_profile`, `token_budget_max`, `orphaned_discoveries`, `resume_from`, and `warnings`. The preflight also detects `test_command`, `build_command`, and `lint_command` from signal files (Makefile, package.json, pyproject.toml, go.mod, Cargo.toml, pom.xml, Gemfile, composer.json, *.csproj, etc.).

Then initialize the run state:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli init --run-id {{feature_slug}} --skill implement --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
```

If `squad-cli` is not available, fall back to manual preflight: read `runtime-policy.yaml`, detect stack from signal files, resolve routing, detect commands, check orphans, check retro counter.

**Ticket Intake** — If the user's input matches a ticket ID pattern (`[A-Z]+-[0-9]+` for Jira, `#[0-9]+` for GitHub Issues, `LIN-[0-9]+` for Linear):
  1. Read the ticket via the appropriate MCP tool
  2. Extract: title, description, acceptance criteria, priority, subtasks, labels, comments
  3. Use the extracted content as the task context
  4. Emit: `[Ticket Read] {{source}} | {{ticket_id}} | type={{issue_type}} | priority={{priority}}`
  5. If MCP is unavailable, ask the user to paste the ticket content — do not block

**Chain validation** — Check `ai-docs/.squad-log/` for a discovery SEP log matching `{{feature_slug}}`. If missing, emit `[Preflight Warning] no discovery SEP log found — implementation has no traceable origin`.

**Blueprint staleness preflight (MANDATORY):** compute the age of the blueprint file in days.

```bash
BLUEPRINT=ai-docs/{{feature_slug}}/blueprint.md
if [ -f "$BLUEPRINT" ]; then
  AGE_DAYS=$(( ( $(date +%s) - $(stat -c %Y "$BLUEPRINT") ) / 86400 ))
  echo "blueprint_age_days=$AGE_DAYS"
fi
```

If `AGE_DAYS > 14`, emit `[Gate Blocked] blueprint-stale | age={{days}} days` and stop. Do not spawn any implementation teammate. Recommend to the user:

```
The blueprint at {{BLUEPRINT}} is {{days}} days old. The repository, dependencies,
or acceptance criteria may have drifted. Run `/claude-tech-squad:discovery --refresh`
to refresh the blueprint before implementing. Options:
- [R] Run /discovery --refresh now
- [F] Force-continue with current blueprint — reason will be logged as `blueprint_stale_override_reason`
- [X] Abort
```

If the user selects [F], record `blueprint_stale_override_reason` in the SEP log and proceed.
Added 2026-04-18 after the retrospective flagged stale blueprints as a recurring orphaned-discovery cause.

If detected commands are empty, emit `[Gate] Commands Unknown` and ask the user. Block all agent spawns until confirmed. CLAUDE.md command overrides take priority.

Emit `[Preflight Passed] implement | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version> | stack=<detected_stack>`

Emit: `[Stack Detected] {{detected_stack}} | backend={{backend_agent}} | frontend={{frontend_agent}} | reviewer={{reviewer_agent}} | qa={{qa_agent}}`

### Checkpoint / Resume Rules

Checkpoints: `preflight-passed`, `commands-confirmed`, `blueprint-validated`, `tdd-ready`, `implementation-batch-complete`, `reviewer-approved`, `qa-pass`, `conformance-pass`, `quality-bench-cleared`, `coderabbit-clean`, `docs-complete`, `uat-approved`.

**python3 plugins/claude-tech-squad/bin/squad-cli checkpoint** (preferred):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint save --run-id {{feature_slug}} --cursor <checkpoint> --state-dir .squad-state
```

If `squad-cli` is not available: emit `[Checkpoint Saved] implement | cursor=<checkpoint>` and track state manually.

### Execution Budgets

Values must match `retry_budgets` in `plugins/claude-tech-squad/runtime-policy.yaml`: `review_cycles_max = 3`, `qa_cycles_max = 2`, `conformance_cycles_max = 2`, `quality_fix_cycles_max = 2`, `uat_cycles_max = 2`.

### Step 1 — Validate Blueprint

Confirm the Discovery & Blueprint Document is present.
If missing, stop and ask the user to provide it.

Extract and store the following variables from the blueprint before spawning any agent:
- `{{feature_slug}}` — machine-readable slug for this feature (e.g. `user-auth-oauth2`, derived from the blueprint title or ticket ID, lowercase kebab-case)
- `{{acceptance_criteria}}` — full acceptance criteria list from the blueprint
- `{{test_plan}}` — test plan from TDD/discovery output (if present)
- `{{architecture}}` — architecture decisions from discovery (if present)
- `{{architecture_style}}` — explicit architecture style selected during discovery (if present). If missing, default to `existing-repo-pattern`

**Blueprint Completeness Gate (blocking):**

After extraction, check which critical fields are missing or empty:

| Field | Severity | Impact if missing |
|-------|----------|-------------------|
| `{{acceptance_criteria}}` | BLOCKING | Reviewer and QA cannot validate; UAT will fail |
| `{{architecture}}` | BLOCKING | Implementation agents lack structural guidance; high rework risk |
| `{{test_plan}}` | WARNING | TDD specialist can derive tests from acceptance criteria, but quality degrades |
| `{{feature_slug}}` | WARNING | Derivable from task description; only affects traceability |

If ANY BLOCKING field is missing or empty:

```
[Gate] Blueprint Incomplete | Missing: {{comma_separated_missing_fields}}

The discovery document is missing critical fields required for implementation.
Without these, downstream agents will produce low-quality output or fail.

Options:
- [D] Run /discovery first to produce a complete blueprint
- [P] Provide the missing fields now (paste acceptance criteria / architecture)
- [F] Force continue — implementation quality WILL be degraded (logged as risk)
```

Do NOT proceed past this gate until the user responds. If the user selects [F], log `blueprint_completeness: forced` in the SEP log and prepend a warning to every downstream agent prompt.

If only WARNING fields are missing, emit `[Preflight Warning] blueprint incomplete — missing: {{fields}}` and continue. Derive `feature_slug` from the task description and default `architecture_style` to `existing-repo-pattern`.

### Step 2 — Create Implementation Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "implement"
- `description`: "Implementation run for: {{feature_or_task_one_line}}"

Emit: `[Team Created] implement`

### Step 2b — Delivery Docs: Tasks + Work Items (Phase 0)

Before spawning TDD Specialist:

1. Verify `ai-docs/prd-{{feature_slug}}/prd.md` and `ai-docs/prd-{{feature_slug}}/techspec.md` exist. If either is missing, block with:
   ```
   [Gate] Delivery Docs Missing | Run /claude-tech-squad:discovery and /claude-tech-squad:inception first | Waiting for user input
   ```
2. If `ai-docs/prd-{{feature_slug}}/tasks.md` exists and validates against `templates/tasks-template.md`, reuse. Else spawn `tasks-planner`:
   ```
   Agent(
     team_name = "implement",
     name = "tasks-planner",
     subagent_type = "claude-tech-squad:tasks-planner",
     prompt = <digest including slug, prd path, techspec path>
   )
   ```
3. After tasks are produced, spawn `work-item-mapper`:
   ```
   Agent(
     team_name = "implement",
     name = "work-item-mapper",
     subagent_type = "claude-tech-squad:work-item-mapper",
     prompt = <digest + taxonomy context from runtime-policy.yaml>
   )
   ```
4. If `delivery_gates.enabled: true` and any BLOCKING finding is returned, open a user gate.
5. Pipe both teammates' `metrics` JSON through `render-teammate-card.sh` per the Visual Reporting Contract.
6. Record checkpoints: `tasks-produced`, `work-items-produced`. Emit `[Checkpoint Saved] implement | cursor=<checkpoint>`.

### Step 3 — TDD Specialist Teammate (Failing Tests First)

**Progressive Disclosure:** TDD Specialist receives full TDD delivery plan and test plan from the blueprint, plus an architecture digest (not the full architecture document).

Before spawning:
```
architecture_digest = summarize(architecture, max_tokens=500, format=context_digest)
```

Spawn TDD Specialist to produce the first failing tests before any production code:

```
Agent(
  team_name = <team>,
  name = "tdd-specialist",
  subagent_type = "claude-tech-squad:tdd-specialist",
  prompt = """
## TDD — First Failing Tests

### TDD Delivery Plan (full)
{{tdd_delivery_plan}}

### Test Plan (full)
{{test_plan}}

### Architecture (digest)
{{architecture_digest}}

### Architecture Style
{{architecture_style}}

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
# Spawn relevant implementation agents in parallel using routing table from Step 0.5
Agent(team_name=<team>, name="backend-dev",  subagent_type="claude-tech-squad:{{backend_agent}}",  prompt=...)
Agent(team_name=<team>, name="frontend-dev", subagent_type="claude-tech-squad:{{frontend_agent}}", prompt=...)
Agent(team_name=<team>, name="platform-dev", subagent_type="claude-tech-squad:platform-dev",       prompt=...)
```

Only spawn `backend-dev` if the workstream requires backend changes. Only spawn `frontend-dev` if the workstream requires frontend changes. Only spawn `platform-dev` if background workers, queues, or platform tooling are in scope.

Emit: `[Batch Spawned] implementation | Teammates: <list>`

**Progressive Disclosure:** Implementation agents receive full TDD failing tests + their specific workstream, plus digests of the broader blueprint context. They do NOT receive the entire discovery document.

Before spawning:
```
blueprint_digest = summarize(blueprint, max_tokens=500, format=context_digest)
```

Each implementation agent prompt must include:
- TechLead execution plan — their specific workstream only (full)
- Architecture decisions relevant to their layer (full)
- Failing test files from TDD Specialist (full — they implement against these)
- Relevant specialist notes for their domain only (full)
- Blueprint context (digest — not the full discovery document)
- Detected project commands: `{{test_command}}`, `{{build_command}}` (from Step 0)
- Lint/static-analysis profile: `{{lint_profile}}`
- Chosen architecture style: `{{architecture_style}}`
- Design principles guardrails (full)
- Project commands: `{{project_commands}}` — use these exact commands, never infer
- Instruction: "Implement until the failing tests pass. Follow TDD. When done, return a summary of files changed and test results. Do NOT chain to other agents."

**SEP Contrato 4 — Task Status Protocol:**
Each implementation agent must also:
1. Before starting: confirm which task slice it is implementing
2. After completing: verify `{{test_command}}` passes
3. Return a structured completion block:
```
## Completion Block
- Task: {{task_name}}
- Status: completed
- Files changed: [list]
- Tests run: {{test_command}} → PASS/FAIL
- Test count: N passed, M failed
```
The orchestrator uses this block to track which tasks are done before spawning Reviewer.

Wait for all implementation teammates to complete.

### Step 5 — Reviewer Teammate

**Progressive Disclosure:** Reviewer receives full implementation diff (must see all code) + architecture digest (structural context only). Does NOT receive full blueprint, PM/BA/PO outputs, or specialist notes.

Before spawning:
```
architecture_digest = summarize(architecture_and_design_principles, max_tokens=500, format=context_digest)
test_plan_digest    = summarize(test_plan, max_tokens=500, format=context_digest)
```

Spawn Reviewer with implementation output:

```
Agent(
  team_name = <team>,
  name = "reviewer",
  subagent_type = "claude-tech-squad:{{reviewer_agent}}",
  prompt = """
## Code Review

### Files Changed (full)
{{implementation_batch_output}}

### Architecture and Design Guardrails (digest)
{{architecture_digest}}

### Architecture Style
{{architecture_style}}

### Lint Profile
{{lint_profile}}

### Project Commands
{{project_commands}}

### Test Plan (digest)
{{test_plan_digest}}

---
You are the Reviewer. Review for correctness, simplicity, maintainability,
TDD compliance, lint compliance, and documentation compliance.
Flag bugs, regressions, missing tests, and unnecessary complexity.

**Output contract — you MUST produce ALL of the following before ending your turn:**
1. A section `## Findings` with in-scope issues (empty if none)
2. A section `## Pre-existing Findings` for issues found in code NOT changed by this PR — classify each as Major or Minor
3. A final verdict line: either `APPROVED` or `CHANGES REQUESTED: <item list>`
4. A `result_contract` block and a `verification_checklist` block

Do NOT stop mid-turn after reading files. Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] reviewer | pane: reviewer`

If reviewer returns CHANGES REQUESTED:
- Emit: `[Teammate Retry] <impl-agent> | Reason: <review item>`
- Spawn the relevant implementation agent again with the review feedback
- Repeat Step 5 until APPROVED — **max 3 review cycles**
- If the 3rd review still returns CHANGES REQUESTED, consult `fallback_matrix.implement.reviewer` and run one fallback review pass before asking the user
- After the fallback review also returns blocking issues: emit `[Gate] Review Limit Reached` and surface to user:

```
Reviewer requested changes 3 times.

Options:
- [A] Accept current implementation and continue
- [S] Skip review and continue with explicit risk
- [X] Abort the run
```

### Step 5b — Pre-existing Findings Triage Gate

After reviewer returns APPROVED (or after fallback reviewer completes), check whether the reviewer's `## Pre-existing Findings` section contains any **Major** items.

**If there are Major pre-existing findings:**

Emit: `[Gate] Pre-existing Findings | N Major issue(s) found in code outside this PR`

Surface to user:

```
The reviewer flagged N Major pre-existing issue(s) not caused by this PR:

{{list_of_major_pre_existing_findings}}

Options:
- [T] Ticket them — create Jira subtasks for each and continue
- [S] Skip — acknowledge and continue without ticketing
- [X] Abort — fix them before proceeding
```

If [T]: spawn `jira-confluence` (subagent_type: `jira-confluence-specialist`) to create one Jira subtask per Major finding. Record `pre_existing_findings_triaged: true` in SEP log.
If [S]: record `pre_existing_findings_triaged: skipped` in SEP log.

**If there are only Minor pre-existing findings or none:** auto-advance (no gate). Record `pre_existing_findings_triaged: none` in SEP log.

Emit: `[Checkpoint Saved] implement | cursor=reviewer-approved`

### Step 6 — QA Teammate

**Progressive Disclosure:** QA receives full acceptance criteria + full test plan (must validate against these) + implementation digest (summary of what changed, not the full diff). QA runs commands, not reads code.

Before spawning:
```
implementation_digest = summarize(approved_implementation, max_tokens=500, format=context_digest)
```

Spawn QA after reviewer approval:

```
Agent(
  team_name = <team>,
  name = "qa",
  subagent_type = "claude-tech-squad:{{qa_agent}}",
  prompt = """
## QA Validation

### Implementation Summary (digest — run tests, don't review code)
{{implementation_digest}}

### Acceptance Criteria (full)
{{acceptance_criteria}}

### Test Plan (full)
{{test_plan}}

### Test Command
{{test_command}}

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
- Repeat Steps 5–6 until QA PASS — **max 2 QA cycles**
- If the 2nd QA cycle still FAILS, consult `fallback_matrix.implement.qa` and run one fallback verification pass before asking the user
- After the fallback verification also FAILS: emit `[Gate] QA Limit Reached` and surface to user:

```
QA failed twice for this implementation slice.

Options:
- [A] Accept current implementation and continue
- [X] Abort the run
```

### Step 6b — TechLead Conformance Audit

**MANDATORY GATE — Quality Bench MUST NOT start until TechLead confirms CONFORMANT. This step is NEVER skippable.**

After QA PASS, spawn TechLead to audit conformance between the implementation and the original execution plan:

```
Agent(
  team_name = <team>,
  name = "techlead-audit",
  subagent_type = "claude-tech-squad:techlead",
  prompt = """
## Conformance Audit

### Original TechLead Execution Plan
{{techlead_execution_plan}}

### Architecture Decisions (from Discovery)
{{architect_output}}

### TDD Delivery Plan
{{tdd_delivery_plan}}

### Architecture Style
{{architecture_style}}

### Acceptance Criteria
{{acceptance_criteria}}

### Implementation Output (all workstreams)
{{aggregated_implementation_output}}

### QA Results
{{qa_output}}

---
You are the Tech Lead performing a post-implementation conformance audit.

Verify each of the following:

1. **Workstream coverage** — Was every workstream from the execution plan implemented? List any missing or partial workstreams.
2. **Architecture conformance** — Does the implementation follow `{{architecture_style}}` and the documented boundaries, DB constraints, and API contracts? Flag violations.
3. **TDD compliance** — Were failing tests written before production code for each cycle? Does test coverage match the TDD delivery plan?
4. **Requirements traceability** — Does each acceptance criterion map to concrete implemented behavior and a passing test? List any untraced criteria.
5. **Technical debt introduced** — Did the implementation introduce workarounds, shortcuts, or TODOs that block production readiness?

Return verdict: **CONFORMANT** or **NON-CONFORMANT**.

If NON-CONFORMANT: list specific gaps with the workstream/agent responsible for each gap.
Do NOT chain to other agents.

Return your output in EXACTLY this format:
```
## Output from TechLead Conformance Audit

### Verdict
CONFORMANT | NON-CONFORMANT

### Workstream Coverage
- [workstream]: covered | missing | partial

### Architecture Violations
- [none | list of violations with file:line]

### TDD Compliance
- [compliant | list of missing test cycles]

### Requirements Traceability
- [AC#]: covered by [test_name] | NOT COVERED

### Gaps (if NON-CONFORMANT)
- Gap: [description] | Owned by: [agent-name] | Action: [what to fix]
```
"""
)
```

Emit: `[Teammate Spawned] techlead-audit | pane: techlead-audit`

Wait for techlead-audit to return. Validate return contains `## Output from TechLead Conformance Audit` and `### Verdict`.
Emit: `[Teammate Done] techlead-audit | Output: {{CONFORMANT|NON-CONFORMANT}}`

**If TechLead returns NON-CONFORMANT:**
- Emit: `[Gate] Conformance Failure | Gaps: <summary>`
- For each gap: re-spawn the responsible implementation agent with the gap as context
- Re-run Steps 5–6b (reviewer → QA → conformance audit) until CONFORMANT — **max 2 conformance cycles**
- If the 2nd conformance cycle remains NON-CONFORMANT, consult `fallback_matrix.implement.techlead-audit` and run one fallback conformance pass before asking the user
- After the fallback conformance pass also returns NON-CONFORMANT: emit `[Gate] Conformance Limit Reached` and surface to user:

```
TechLead conformance audit remained NON-CONFORMANT after 2 cycles.

Options:
- [A] Accept current implementation and continue
- [X] Abort the run
```

**If TechLead returns CONFORMANT:**
- Emit: `[Gate] Conformance Passed | Advancing to Quality Bench`

### Step 7 — Quality Bench (Parallel)

**MANDATORY GATE — Step 8 (Docs) MUST NOT start until ALL Quality Bench agents have returned a structured checklist. Skipping or short-circuiting this step is FORBIDDEN.**

After Conformance Audit CONFORMANT, spawn quality specialist reviewers in parallel:

```
Agent(team_name=<team>, name="security-rev",  subagent_type="claude-tech-squad:security-reviewer",      prompt=...)
Agent(team_name=<team>, name="privacy-rev",   subagent_type="claude-tech-squad:privacy-reviewer",       prompt=...)
Agent(team_name=<team>, name="perf-eng",      subagent_type="claude-tech-squad:performance-engineer",   prompt=...)
Agent(team_name=<team>, name="access-rev",    subagent_type="claude-tech-squad:accessibility-reviewer", prompt=...)
Agent(team_name=<team>, name="integ-qa",      subagent_type="claude-tech-squad:integration-qa",         prompt=...)
Agent(team_name=<team>, name="code-quality",  subagent_type="claude-tech-squad:code-quality",           prompt=...)
```

Emit: `[Batch Spawned] quality-bench | Teammates: <list>`

Only spawn reviewers relevant to this project. Each receives the full implementation output.
Instruction per reviewer: "Review from your specialist lens. Return findings as a checklist. Do NOT chain."

The `code-quality` agent prompt must include the detected `{{lint_command}}` from Step 0 and the full implementation diff.

**Load test agent (conditional):** Spawn if the implementation adds or modifies HTTP endpoints, message queues, batch jobs, or any operation that processes variable input volume:

```
Agent(team_name=<team>, name="load-test", subagent_type="claude-tech-squad:performance-engineer",
  prompt="""
## Load Test Plan

### New/Modified Endpoints
{{endpoints_or_operations}}

### Current baseline (if known)
{{existing_throughput_or_latency_slos}}

---
You are the Performance Engineer. Produce a load test plan for these endpoints:
1. Baseline test: expected normal load (target RPS/concurrent users)
2. Stress test: 3x normal load — what breaks first?
3. Spike test: sudden 10x burst — does it recover?
4. Identify: slowest query, highest memory operation, bottleneck under load
5. Acceptance criteria: p99 latency < Xms, error rate < 0.1% at normal load

If load testing tools are available (k6, locust, Artillery, JMeter), provide ready-to-run scripts.
Return findings as a checklist. Do NOT chain.
""")
```

**Failure Recovery — Quality Bench agents:**

After spawning, track each agent's return. A valid return is a structured checklist (markdown list with findings or "no issues found"). An agent has FAILED silently if it returns an error, an empty response, or no checklist.

For each agent that fails:
1. Emit: `[Teammate Retry] <agent-name> | Reason: silent failure or error — re-spawning`
2. Re-spawn the agent once with the same prompt
3. If the re-spawn also fails:
   - Consult `fallback_matrix.implement.<agent-name>`
   - If a fallback exists, emit `[Fallback Invoked] <agent-name> -> <fallback-subagent> | Reason: quality bench recovery`
   - Spawn the fallback once before surfacing a gate
4. If the fallback also fails, or no fallback exists: add to the consolidated failure list.

**Consolidated Gate (batch failures):** After all quality bench agents have been attempted (including retries and fallbacks), if multiple agents remain in a failed state, present a single consolidated gate instead of individual prompts:

```
[Gate] Batch Failure — Quality Bench | N of M agents failed

Failed agents:
1. <agent-1> — <failure reason>
2. <agent-2> — <failure reason>
3. <agent-3> — <failure reason>

Options:
- [R] Retry all N failed agents
- [1,3] Retry specific agents by number
- [S] Skip all failed agents and continue (log risk for each)
- [X] Abort the run
```

If only one agent failed, use the standard single-agent gate format.

Block Step 8 until the user resolves every failed agent.

**Quality Bench Completion Gate:**

Before advancing to Step 8, verify:
- Every spawned quality bench agent has returned a structured checklist
- No agent is in a failed/unresolved state

Emit: `[Gate] Quality Bench Complete | All N reviewers returned. Advancing to docs.`

If any agent is unresolved, do NOT advance. Surface to user.

### Step 7b — Quality Bench Issue Resolution

After all bench agents return, classify their findings by severity:

- **BLOCKING**: Security vulnerabilities (OWASP Top 10), data/PII leaks, privacy violations, failing tests, lint errors that block CI, broken accessibility (WCAG A/AA)
- **WARNING**: Performance regressions, non-critical accessibility gaps, integration risks, code quality debt
- **INFO**: Style suggestions, optional improvements, low-priority refactors

**If BLOCKING issues exist:**

1. Emit: `[Gate] Quality Bench Blocking Issues | N blocking findings across: <agents>`
2. Group blocking issues by implementation domain (backend, frontend, infra, etc.)
3. For each domain with blocking issues, spawn the relevant impl agent(s):

```
Agent(
  team_name = <team>,
  name = "<impl-agent>-fix",
  subagent_type = "claude-tech-squad:<impl-agent>",
  prompt = """
## Blocking Issue Fix

### Original Implementation
{{approved_implementation}}

### Blocking Issues to Fix
{{blocking_findings_for_this_domain}}

---
Fix ONLY the blocking issues listed above. Do not refactor unrelated code. Do not add features.
For each fix, state: Issue → Root Cause → Change Made.
Return the updated implementation with all blocking issues resolved.
"""
)
```

4. After fixes, re-spawn only the quality bench agents that flagged blocking findings
5. Repeat until no BLOCKING issues remain — **max 2 fix cycles**
6. If blocking issues persist after 2 cycles:
   - Emit: `[Gate] Quality Bench Unresolved | Blocking issues remain after 2 cycles`
   - Surface to user: `[A]ccept with known issues (document as tech debt) / [X]Abort`

**If only WARNING or INFO issues:**

- Emit: `[Gate] Quality Bench Warnings | <N> warnings, <M> info items`
- Surface to user: "Non-blocking issues found — [A]ccept and advance / [F]ix before advancing"
- If [A]: advance immediately
- If [F]: spawn impl agents for the warnings, re-run relevant bench agents, then advance

### Step 7c — CodeRabbit Final Review Gate

**Purpose:** deterministic second-lens review (tool-based, non-LLM) to catch issues the LLM reviewer and bench may have missed. Runs **after** quality bench is clean, **before** docs.

**Execution (shell, not an agent):**

```
bash plugins/claude-tech-squad/bin/coderabbit_gate.sh
```

Capture the exit code:
- **`0`**: emit `[Gate] CodeRabbit Final Review | clean or skipped` → advance to Step 8
- **`2`**: findings detected → enter remediation cycle below
- **`1`**: unexpected error (network/auth) → emit `[Gate Error] CodeRabbit Final Review | <reason>` and surface to user: `[R]etry / [S]kip gate (document as risk) / [X]Abort`

**Remediation cycle (exit 2):**

1. Capture the CodeRabbit output (stdout of the gate script) into `{{coderabbit_findings}}`
2. Re-spawn the `reviewer` teammate with the findings as input:

```
Agent(
  team_name = <team>,
  name = "reviewer-coderabbit",
  subagent_type = "claude-tech-squad:{{reviewer_agent}}",
  prompt = """
## CodeRabbit Final Review — Remediation Pass

The CodeRabbit deterministic gate detected issues after quality bench passed.
Review each finding, validate it against the current code, and apply only necessary fixes.
Do NOT refactor unrelated code. Do NOT introduce new behavior.

### CodeRabbit Findings (full)
{{coderabbit_findings}}

### Acceptance Criteria (full)
{{acceptance_criteria}}

Return updated files and a brief per-finding disposition (fixed / false-positive-ignored-because-<reason>).
"""
)
```

3. After reviewer returns, re-run the gate script
4. Repeat — **max 2 remediation cycles**
5. If findings persist after 2 cycles:
   - Emit: `[Gate] CodeRabbit Final Review Unresolved | findings remain after 2 cycles`
   - Surface to user: `[A]ccept with known issues (document as tech debt in SEP log) / [X]Abort`

**Checkpoint:** on clean pass, emit `[Checkpoint Saved] implement | cursor=coderabbit-clean`

### Step 8 — Docs Writer Teammate

**Progressive Disclosure:** Docs Writer receives full implementation output (must document what changed) + full acceptance criteria + digests of QA, conformance, and quality bench (summary findings only, not full review details).

Before spawning:
```
architecture_digest    = summarize(architecture, max_tokens=500, format=context_digest)
qa_digest              = summarize(qa_output, max_tokens=500, format=context_digest)
conformance_digest     = summarize(conformance_output, max_tokens=500, format=context_digest)
quality_bench_digest   = summarize(quality_bench_output, max_tokens=500, format=context_digest)
test_plan_digest       = summarize(test_plan, max_tokens=500, format=context_digest)
```

Spawn Docs Writer:

```
Agent(
  team_name = <team>,
  name = "docs-writer",
  subagent_type = "claude-tech-squad:docs-writer",
  prompt = """
## Documentation Update

### Implementation Output (full)
{{approved_implementation}}

### Architecture Decisions (digest)
{{architecture_digest}}

### Acceptance Criteria (full)
{{acceptance_criteria}}

### Test Plan (digest)
{{test_plan_digest}}

### QA Validation (digest)
{{qa_digest}}

### TechLead Conformance Audit (digest)
{{conformance_digest}}

### Quality Review Findings (digest)
{{quality_bench_digest}}

---
You are the Docs Writer. Update technical docs, migration notes, operator guidance,
changelog inputs, and developer-facing usage notes for this change.
Map each acceptance criterion to the implemented behavior and the test that covers it.
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

### Step 9b — Coverage Gate

Before spawning PM for UAT, check test coverage delta.

```bash
# Detect coverage tool from project stack
# Python
coverage report --fail-under=0 2>/dev/null || pytest --cov --cov-report=term-missing 2>/dev/null || echo "COVERAGE_NOT_AVAILABLE"
# JS
npx nyc report --reporter=text 2>/dev/null || npx vitest run --coverage 2>/dev/null || echo "COVERAGE_NOT_AVAILABLE"
```

If coverage data is available:
- Compute delta: coverage after implementation vs coverage reported in blueprint (if present) or vs current `main`
- If delta < 0 (coverage dropped): emit `[Gate] Coverage Drop | Waiting for user input` and present:

```
Coverage dropped: {{before}}% → {{after}}% (delta: {{delta}}%)

Affected files without new test coverage:
{{uncovered_files}}

Options:
- [C] Continue to UAT anyway
- [T] Add tests first (re-runs QA after)
```

Block UAT until user decides. If [T]: spawn QA again with coverage gap as context.
If coverage tool is not available or delta >= 0: proceed silently.

### Step 10 — PM UAT Gate

**Progressive Disclosure:** PM UAT receives full acceptance criteria (must validate against these) + digests of QA results, conformance, and quality bench findings. PM validates evidence, not code.

Before spawning:
```
qa_digest            = summarize(qa_output, max_tokens=500, format=context_digest)
conformance_digest   = summarize(conformance_output, max_tokens=500, format=context_digest)
quality_bench_digest = summarize(quality_bench_output, max_tokens=500, format=context_digest)
```

Spawn PM for UAT validation:

```
Agent(
  team_name = <team>,
  name = "pm-uat",
  subagent_type = "claude-tech-squad:pm",
  prompt = """
## UAT Validation

### Original Acceptance Criteria (full)
{{acceptance_criteria}}

### QA Evidence (digest)
{{qa_digest}}

### TechLead Conformance Audit (digest)
{{conformance_digest}}

### Quality Reviews (digest)
{{quality_bench_digest}}

---
You are the PM performing UAT. Validate that each acceptance criterion has concrete
evidence of fulfillment from the QA output, conformance audit, and implementation output.
For each acceptance criterion, state: criterion → evidence found → PASS or MISSING.
Return: APPROVED or REJECTED with specific gaps.
Do NOT chain.
"""
)
```

Emit: `[Teammate Spawned] pm-uat | pane: pm-uat`
Emit: `[Gate] UAT | Waiting for user input`

Present PM UAT output to user.

**If PM returns REJECTED:**

Do NOT end the workflow. Extract the specific gaps from PM output and present to the user:

```
UAT REJECTED — PM identified the following gaps:
1. {{gap_1}}
2. {{gap_2}}

Options:
- [R] Re-queue: fix the gaps and re-run UAT
- [S] Skip: mark as REJECTED and close the run
```

If user chooses [R]:
- Emit: `[Teammate Retry] pm-uat | Reason: UAT REJECTED — re-queuing implementation`
- Increment `retry_count`
- Spawn the relevant implementation agents with the rejection gaps as context (same format as Step 4, prepend `## UAT Rejection Feedback\n{{gaps}}` to the prompt)
- After fixes, re-run Steps 5–10 (review → QA → quality bench → docs → UAT) — **max 2 UAT cycles**
- If the 2nd UAT cycle still returns REJECTED, consult `fallback_matrix.implement.pm-uat` and run one fallback product acceptance pass before asking the user
- After the fallback product acceptance pass also returns REJECTED: emit `[Gate] UAT Limit Reached` and surface to user:

```
PM rejected UAT twice.

Options:
- [A] Accept current implementation as-is
- [X] Abort the run
```

Implementation is complete when user approves UAT or chooses [S].

### Step 10b — Run Cost Summary and SEP Log

**python3 plugins/claude-tech-squad/bin/squad-cli cost + sep-log** (preferred — uses real token counts collected during the run):

```bash
# Cost summary
python3 plugins/claude-tech-squad/bin/squad-cli cost --run-id {{feature_slug}} --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state

# Generate SEP log
python3 plugins/claude-tech-squad/bin/squad-cli sep-log --run-id {{feature_slug}} --output-dir ai-docs/.squad-log --state-dir .squad-state
```

Emit the cost summary:
```
[Run Summary] /implement | teammates: {{N}} | tokens: {{total_input}}K in / {{total_output}}K out | est. cost: ~${{usd}} | duration: {{elapsed}}
```

**Retro counter increment:**
```bash
COUNTER_FILE="ai-docs/.squad-log/.retro-counter"
CURRENT=$(cat "$COUNTER_FILE" 2>/dev/null || echo "0")
echo "$((CURRENT + 1))" > "$COUNTER_FILE"
```

If `squad-cli` is not available: sum tokens manually, estimate cost at input x $15/M + output x $75/M, and write the SEP log manually to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-implement-{{run_id}}.md` with full YAML frontmatter.

**Required frontmatter fields (implement):**

```yaml
---
run_id: {{run_id}}
skill: implement
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}       # required — refresh on every edit
final_status: completed | in_flight | aborted
execution_mode: teammates | inline
tokens_input: {{actual_or_null}}   # required — actual measurement or null; 0 placeholder forbidden
tokens_output: {{actual_or_null}}  # required — actual measurement or null; 0 placeholder forbidden
teammate_token_breakdown: {}       # required — map {teammate_name: {tokens_in, tokens_out, cost_usd}}
estimated_cost_usd: {{usd}}
total_duration_ms: {{ms}}
blueprint_stale_override_reason: null   # non-null only when user forced continue with stale blueprint
---
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 12 — Team Cleanup (mandatory epilogue)

After writing the SEP log, clean up the team:

```
TeamDelete(name="implement")
```

Emit: `[Team Deleted] implement | cleanup complete`

If TeamDelete fails, ignore silently.

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
