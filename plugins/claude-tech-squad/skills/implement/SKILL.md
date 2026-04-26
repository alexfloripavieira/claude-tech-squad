---
name: implement
description: This skill should be used when an approved discovery/blueprint exists and the team is ready to build — runs implementation, code review, QA, conformance, UAT, and operations gates with separate teammate contexts per phase. Trigger with "implementar feature", "rodar implement", "executar blueprint", "/implement", "build phase", "implementation phase", "construir feature aprovada", "post-discovery build". Uses TDD-first cycles, multi-lens reviewer/QA/conformance gates with retry budgets and checkpoints. NOT for greenfield planning (use /discovery first) or one-shot bug fixes (use /bug-fix).
user-invocable: true
---

# /implement — Build & Quality

Implementation and quality validation from a Discovery & Blueprint Document. Each specialist runs as an independent teammate in its own tmux pane.

## Global Safety Contract

Applies to every teammate. Violation requires explicit written user confirmation. No teammate may execute destructive SQL without verified rollback, delete production cloud resources, run app deletion commands, merge to protected branches without an approved PR, force-push protected branches, remove production secrets, run `terraform destroy`, disable auth as a workaround, deploy without a tested rollback, skip pre-commit hooks without authorization, execute `eval()` / dynamic shell injection, apply migrations without a verified backup, or deploy to production before staging passes. Any conflict: STOP and surface to user.

## TDD Execution Rule

If the discovery package came from `/squad` or marks TDD as required, TDD is mandatory: start from failing tests, follow the TDD Delivery Plan, state exceptions explicitly.

## Teammate Architecture

Use `TeamCreate` then `Agent` with `team_name` + `name` + `subagent_type` to spawn each specialist in its own tmux pane. Use `SendMessage` to communicate, `TaskCreate` / `TaskUpdate` to track work. **Do NOT use `Agent` without `team_name`** — that runs an inline subagent, not a visible pane.

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

After every `[Teammate Done]`, run the 6-signal health check (preferred: `python3 plugins/claude-tech-squad/bin/squad-cli health`). It returns `signals_triggered`, `context_enrichment`, `budget_percent`, `is_critical`. Warning signals prepend enrichment to the next teammate; critical signals emit `[Health Warning]`. Full signal list and CLI flags in `references/runtime-resilience.md`.

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

After every teammate returns, pipe its `result_contract.metrics` JSON to `plugins/claude-tech-squad/scripts/render-teammate-card.sh` and print the card inline. Before writing the SEP log, assemble pipeline summary JSON (matching `scripts/test-fixtures/pipeline-board-input.json`) and pipe to `plugins/claude-tech-squad/scripts/render-pipeline-board.sh`. Respect `observability.teammate_cards.format` and `observability.pipeline_board.enabled` in `runtime-policy.yaml`. Renderer failures are non-fatal (log WARNING, continue). Full contract in `references/visual-reporting.md`.

## Runtime Resilience Contract

Load `plugins/claude-tech-squad/runtime-policy.yaml` before command detection or team creation. It is the source of truth for: retry budgets, fallback matrix, severity policy, checkpoint/resume rules, cost guardrails, doom-loop heuristics, auto-advance, entropy management, and reliability metrics recorded in SEP logs.

If the policy file is missing or unreadable, stop and surface `[Gate] Runtime Policy Missing` — never silently fall back to hardcoded defaults. Phase-by-phase retry budgets, fallback matrix, doom-loop patterns, cost guardrails, and auto-advance rules are tabulated in `references/runtime-resilience.md`.

---

## Execution

### Preflight Gate

Emit `[Preflight Start] implement`. Preferred path:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli preflight \
  --skill implement --policy plugins/claude-tech-squad/runtime-policy.yaml --project-root .
python3 plugins/claude-tech-squad/bin/squad-cli init \
  --run-id {{feature_slug}} --skill implement \
  --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
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
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint save \
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

### Step 3 — TDD Specialist (Failing Tests First)

Spawn `tdd-specialist` (`subagent_type: claude-tech-squad:tdd-specialist`) with full TDD Delivery Plan + full Test Plan + architecture digest (max 500 tokens) + `{{architecture_style}}`. Instruction: write the first failing tests for the first delivery slice using red-green-refactor; do NOT write production code. Wait for completion; confirm failing tests are in place.

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

Deterministic second-lens review (tool, not LLM). Run `bash plugins/claude-tech-squad/bin/coderabbit_gate.sh`.

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
python3 plugins/claude-tech-squad/bin/squad-cli cost --run-id {{feature_slug}} \
  --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
python3 plugins/claude-tech-squad/bin/squad-cli sep-log --run-id {{feature_slug}} \
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
