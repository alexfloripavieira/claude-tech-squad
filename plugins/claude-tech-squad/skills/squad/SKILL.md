---
name: squad
description: Run the full technology squad workflow end-to-end with the full specialist bench: discovery, blueprint, design-principles and TDD-first implementation, quality, documentation, Jira/Confluence, reliability, and release preparation.
---

# /squad — Full Technology Squad

Run the complete end-to-end workflow. Every specialist runs as an independent teammate in its own tmux pane. This is the full pipeline: discovery → blueprint → implementation → quality → docs → release.

## Global Safety Contract

**This contract applies to every teammate spawned by this workflow. It covers all phases: discovery, implementation, and release. Violating it requires explicit written user confirmation.**

No teammate may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues, Kafka topics) in production
- Run `tsuru app-remove`, `heroku apps:destroy`, or any equivalent application deletion command
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a workaround
- Deploy to production without a documented and tested rollback plan
- Disable SLO alerting or monitoring as a way to proceed faster
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists
- Deploy to production before staging has been successfully deployed and verified
- Create a version tag or cut a release when CI is FAILING

If any teammate believes a task requires one of these actions, it must STOP immediately and surface the decision to the user before proceeding. **The urgency of a deadline, incident, or business pressure does not override this contract.**

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

- `[Preflight Start] <workflow-name>`
- `[Preflight Warning] <summary>`
- `[Preflight Passed] <workflow-name> | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`
- `[Team Created] <team-name>`
- `[Phase Start] <phase-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Fallback Invoked] <failed-role> -> <fallback-subagent> | Reason: <summary>`
- `[Resume From] <workflow-name> | checkpoint=<checkpoint>`
- `[Checkpoint Saved] <workflow-name> | cursor=<checkpoint>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`
- `[Phase Done] <phase-name> | Outcome: <summary>`
- `[Token Usage] run=<run_id> | used=<N>k | threshold=100k`
- `[Context Advisory] run=<run_id> | recommend=finish-current-gate-then-rollover`
- `[Gate] Context Rollover Required | run=<run_id> | used=<N>k | options=[R|D|F]`
- `[Rollover Accepted] run=<run_id> | handoff=<artifact-path>`
- `[Rollover Declined] run=<run_id> | reason=<user-text>`

## Context Rollover Gate

Between every `[Phase Done]` and the next `[Phase Start]`, inspect cumulative token usage for the run. Emit `[Token Usage]` every phase boundary.

- If `used >= 100k`: emit `[Context Advisory]`. The run continues, but the advisory signals that the next phase should be the last before a rollover.
- If `used >= 140k`: emit `[Gate] Context Rollover Required` and halt. The operator must choose:
  - `R` — Rollover now. Spawn `context-summarizer` as a teammate, then halt for `/clear` plus `/resume-from-rollover <run_id>`.
  - `D` — Defer one phase. Proceed only with the next phase; force rollover immediately after.
  - `F` — Force continue. Emit `[Rollover Declined]` with the operator reason. Degradation risk is accepted and logged.

Threshold constants and the summarizer agent are declared in `runtime-policy.yaml` under `context_management`. Checks fire only at phase boundaries, never mid-phase. Rationale and alternatives: `docs/architecture/0001-context-rollover.md`.

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
- When transitioning from discovery to implementation, produce a digest of the full blueprint — the implementation phase receives the digest plus the full blueprint file path for on-demand access
- Within each phase (discovery, implement), follow the phase-specific progressive disclosure rules defined in the respective skill
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
   - Read `plugins/claude-tech-squad/runtime-policy.yaml` and consult `fallback_matrix.squad.<name>`
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

After every `[Teammate Done]`, run the health check. This evaluates 6 signals: retry_detected, fallback_used, doom_loop_short_circuit, token_budget_pressure, low_confidence_chain, blocking_findings_accumulating.

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

The returned JSON contains `signals_triggered`, `context_enrichment` (text to prepend to the next teammate's prompt), `budget_percent`, and `is_critical`. Use the `context_enrichment` text directly.

If `squad-cli` is not available: evaluate the 6 signals manually from the teammate's `result_contract` and execution metadata.

- Emit: `[Health Check] <name> | signals: <triggered_signals_or_ok>`
- **warning signals**: prepend context enrichment to next teammate's prompt
- **critical signals**: emit `[Health Warning]` and surface to user if action is needed

**Cross-phase health:** In `/squad`, health signals from the discovery phase are carried into the implementation phase. If discovery had retries or low confidence, the implementation phase starts with that context already enriched.

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

Load `plugins/claude-tech-squad/runtime-policy.yaml` before repository recon or team creation. This file is the source of truth for:
- retry budgets
- fallback matrix
- severity policy
- checkpoint/resume rules
- reliability metrics recorded in SEP logs

If the runtime policy file is missing or unreadable, stop the run and surface `[Gate] Runtime Policy Missing`. Do not silently continue with hardcoded defaults.

---

## Execution

### Preflight Gate

Before repository recon and team creation, validate the run contract and emit explicit preflight lines.

Emit `[Preflight Start] squad`

**python3 plugins/claude-tech-squad/bin/squad-cli accelerated preflight** (preferred — saves ~5K tokens):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli preflight --skill squad --policy plugins/claude-tech-squad/runtime-policy.yaml --project-root .
```

This returns a JSON object with all preflight data: `stack`, `ai_feature`, `routing`, `lint_profile`, `docs_lookup_mode`, `policy_version`, `token_budget_max`, `orphaned_discoveries`, `retro_counter`, `resume_from`, and `warnings`. Use the returned values to set all `{{variables}}` for the run.

Then initialize the run state for health tracking and checkpoints:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli init --run-id {{feature_slug}} --skill squad --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
```

If `squad-cli` is not available, fall back to manual preflight: read `runtime-policy.yaml`, detect stack from signal files (manage.py, package.json, go.mod, Cargo.toml, etc.), resolve the routing table, check orphaned discoveries in `ai-docs/.squad-log/`, and read the retro counter.

**Ticket Intake** — If the user's input matches a ticket ID pattern (`[A-Z]+-[0-9]+` for Jira, `#[0-9]+` for GitHub Issues, `LIN-[0-9]+` for Linear):
  1. Read the ticket via the appropriate MCP tool
  2. Extract: title, description, acceptance criteria, priority, subtasks, labels, comments
  3. For Epics: also read child stories via JQL `parent = {{ticket_id}}`
  4. Use the extracted content as the `{{user_request}}` for the entire pipeline
  5. Emit: `[Ticket Read] {{source}} | {{ticket_id}} | type={{issue_type}} | priority={{priority}}`
  6. If MCP is unavailable, ask the user to paste the ticket content — do not block

Emit all warnings from the preflight JSON output, then:
- Emit `[Preflight Passed] squad | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`

### Checkpoint / Resume Rules

Save a checkpoint whenever one of these milestones is completed: `preflight-passed`, `discovery-confirmed`, `implementation-complete`, `release-signed-off`.

**python3 plugins/claude-tech-squad/bin/squad-cli checkpoint** (preferred):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint save --run-id {{feature_slug}} --cursor <checkpoint> --state-dir .squad-state
```

To check for a resumable prior run:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint resume --skill squad --state-dir .squad-state
```

If `squad-cli` is not available: emit `[Checkpoint Saved] squad | cursor=<checkpoint>` and track state manually. On resume, inspect the latest `ai-docs/.squad-log/*-squad-*.md` for the same feature slug.

### Escape Hatch — Skip Forward

At any gate during `/squad`, the user can jump forward to a later phase. This prevents wasting tokens on phases the user doesn't need.

**At every gate, include this option in addition to the normal choices:**

```
[J] Jump forward — skip remaining discovery and go to /implement
    (provide your own context or blueprint path)
```

**Supported jumps:**

| Current phase | Jump to | What the user provides | What is skipped |
|---|---|---|---|
| Discovery (any gate) | Implementation | Blueprint or context summary | Remaining discovery agents |
| Implementation (review/QA gate) | Docs + UAT | Confirmation that code is ready | Remaining review/QA cycles |
| Implementation (any gate) | Release | Confirmation that implementation is done | Remaining implementation gates |

**Rules:**
- Emit `[Escape Hatch] jumping from {{current_phase}} to {{target_phase}} | Reason: user requested`
- Log the skip in the SEP log as `escape_hatch_used: true` with `skipped_phases: [list]`
- The skipped phases are **not** recoverable — if the user wants to go back, they must start a new run
- The health check after the jump must flag: `[Health Warning] phases skipped via escape hatch — downstream quality may be degraded`
- Token savings are immediate — skipped agents are never spawned

### Step 1 — Repository Recon

Read CLAUDE.md and README.md to understand project conventions and constraints. Note any existing architecture patterns.

**Stack, AI, and routing detection** — all resolved by `python3 plugins/claude-tech-squad/bin/squad-cli preflight` in the Preflight Gate. The returned JSON contains `stack`, `ai_feature`, `routing` (with `pm_agent`, `techlead_agent`, `backend_agent`, `frontend_agent`, `reviewer_agent`, `qa_agent`), and `lint_profile`. Use these values directly.

If `squad-cli` was not available and preflight was done manually, detect the stack from signal files:
- `manage.py` + django in requirements = `django`
- `package.json` with react/vue/next/nuxt = `react`/`vue`
- `tsconfig.json` or typescript in devDeps = `typescript`
- `package.json` alone = `javascript`
- `go.mod` = `go`, `Cargo.toml` = `rust`, `pom.xml`/`build.gradle` = `java`, `Gemfile` = `ruby`, `composer.json` = `php`, `*.csproj` = `dotnet`, `mix.exs` = `elixir`
- `pyproject.toml`/`requirements.txt` without manage.py = `python`
- Scan source files for AI library imports (openai, anthropic, langchain, pgvector, etc.) to set `ai_feature`

If `ai_feature: true`: activate the **LLM-enhanced bench** in Phase 1 and Phase 2. Emit: `[AI Detected] LLM/AI features found — activating AI specialist bench`

Emit: `[Stack Detected] {{detected_stack}} | pm={{pm_agent}} | techlead={{techlead_agent}} | backend={{backend_agent}} | frontend={{frontend_agent}} | reviewer={{reviewer_agent}} | qa={{qa_agent}}`

### Step 2 — Create Squad Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "squad"
- `description`: "Full squad run for: {{user_request_one_line}}"

Emit: `[Team Created] squad`

---

### PHASE 0: DELIVERY DOCS

Squad runs the full delivery docs chain inline. Each step reuses existing artifacts when valid.

Emit: `[Phase Start] delivery-docs`

1. **PRD** → `ai-docs/prd-{{feature_slug}}/prd.md`
   - Reuse if the file exists and validates against `templates/prd-template.md`.
   - Otherwise spawn `prd-author` via `Agent(team_name="squad", name="prd-author", subagent_type="claude-tech-squad:prd-author", prompt=<digest>)`.
   - Checkpoint: `prd-produced`.

2. **TechSpec** → `ai-docs/prd-{{feature_slug}}/techspec.md`
   - Reuse if the file exists and validates against `templates/techspec-template.md`.
   - Otherwise spawn `inception-author` via `Agent(team_name="squad", name="inception-author", subagent_type="claude-tech-squad:inception-author", prompt=<digest>)`.
   - Checkpoint: `techspec-produced`.

3. **Tasks** → `ai-docs/prd-{{feature_slug}}/tasks.md` + `<num>_task.md`
   - Reuse if all task files exist and validate against `templates/tasks-template.md` + `templates/task-template.md`.
   - Otherwise spawn `tasks-planner`.
   - Checkpoint: `tasks-produced`.

4. **Work items** → `ai-docs/prd-{{feature_slug}}/work-items.md`
   - Spawn `work-item-mapper`.
   - Checkpoint: `work-items-produced`.

Between each step:

- Pipe `result_contract.metrics` to `render-teammate-card.sh` per the Visual Reporting Contract.
- If any agent returns `confidence: low` with `gaps_count > 0`, open a user gate before continuing:
  ```
  [Gate] Delivery Docs Confidence Low | step: <step> | gaps: <gap_list> | Waiting for user input
  ```
- If `delivery_gates.enabled: true` and `work-item-mapper` reports a BLOCKING finding, stop the pipeline and open a user gate.

Emit: `[Phase Done] delivery-docs`

---

### PHASE 1: DISCOVERY

Emit: `[Phase Start] discovery`

Follow the same teammate sequence as `/discovery` Steps 3–13:

**Sequential chain with gates:**
1. Spawn `pm` (subagent_type: `{{pm_agent}}`) → **Gate 1: Product Definition**
2. Spawn `business-analyst` with PM output
3. Spawn `po` → **Gate 2: Scope Validation**
4. Spawn `planner` → **Gate 3: Technical Tradeoffs**
5. Spawn `architect`
6. Spawn `techlead` (subagent_type: `{{techlead_agent}}`) → **Gate 4: Architecture Direction**
7. Spawn specialist batch in parallel (from TechLead list)
   - If `ai_feature: true`: add `ai-engineer`, `rag-engineer` (if RAG detected), `prompt-engineer` to this batch
8. Spawn quality baseline batch in parallel
9. Spawn `design-principles`
10. Spawn `test-planner`
11. Spawn `tdd-specialist` → **Gate 5: Blueprint Confirmation**
12. If `ai_feature: true`: Spawn `llm-eval-specialist` for eval plan (after blueprint) — no gate, automatic
13. If `ai_feature: true`: Spawn `llm-safety-reviewer` for threat model (after blueprint) — no gate, automatic
14. If `ai_feature: true`: Spawn `llm-cost-analyst` for token cost attribution and model routing analysis (after blueprint) — no gate, automatic

Each spawn: `Agent(team_name=<squad-team>, name=<role>, subagent_type="claude-tech-squad:<subagent>", prompt=...)`

**Phase 1 explicit subagent_type mappings** (name → subagent_type):

Core discovery chain (stack-aware — use routing variables from Step 1):
- `pm` → `{{pm_agent}}` (e.g. `django-pm` for Django, `pm` otherwise)
- `business-analyst` → `business-analyst`
- `po` → `po`
- `planner` → `planner`
- `architect` → `architect`
- `techlead` → `{{techlead_agent}}` (e.g. `tech-lead` for Django, `techlead` otherwise)
- `design-principles` → `design-principles-specialist`
- `test-planner` → `test-planner`
- `tdd-specialist` → `tdd-specialist`
- `llm-eval-specialist` → `llm-eval-specialist`
- `llm-safety-reviewer` → `llm-safety-reviewer`
- `llm-cost-analyst` → `llm-cost-analyst`

Specialist batch (spawned based on TechLead requirements, any subset):
- `backend-arch` → `backend-architect`
- `hexagonal-arch` → `hexagonal-architect`
- `frontend-arch` → `frontend-architect`
- `api-designer` → `api-designer`
- `data-arch` → `data-architect`
- `ux-designer` → `ux-designer`
- `devops` → `devops`
- `ci-cd` → `ci-cd`
- `dba` → `dba`
- `ai-engineer` → `ai-engineer`
- `rag-engineer` → `rag-engineer`
- `integration-engineer` → `integration-engineer`
- `ml-engineer` → `ml-engineer`
- `search-engineer` → `search-engineer`
- `prompt-engineer` → `prompt-engineer`
- `cloud-arch` → `cloud-architect`
- `mobile-dev` → `mobile-dev`

Quality baseline batch (always runs in parallel with specialist batch):
- `security-baseline` → `security-reviewer`
- `privacy-baseline` → `privacy-reviewer`
- `compliance-baseline` → `compliance-reviewer`
- `perf-baseline` → `performance-engineer`
- `observability-baseline` → `observability-engineer`

All agents receive the full accumulated context from prior teammates.
All architecture-sensitive agents also receive `{{architecture_style}}`.
All review-sensitive agents also receive `{{lint_profile}}`.
All agents end with: "Do NOT chain to other agents — the orchestrator handles sequencing."

Emit: `[Phase Done] discovery | Blueprint confirmed`

---

### PHASE 2: IMPLEMENTATION

Emit: `[Phase Start] implementation`

**Sequential with parallel batches:**

1. Spawn `tdd-impl` (subagent_type: `tdd-specialist`) — write first failing tests
2. Spawn implementation batch in parallel (only relevant workstreams):
   - `backend-dev` (subagent_type: `{{backend_agent}}`), `frontend-dev` (subagent_type: `{{frontend_agent}}`), `platform-dev` (subagent_type: `platform-dev`)
3. Spawn `reviewer` (subagent_type: `{{reviewer_agent}}`) — review implementation

   Reviewer prompt must include the implementation diff and this output contract:

   ```
   You are the Reviewer. Review for correctness, simplicity, maintainability,
   TDD compliance, lint compliance, and documentation compliance.
   Flag bugs, regressions, missing tests, and unnecessary complexity.

   **Output contract — you MUST produce ALL of the following before ending your turn:**
   1. A section `## Findings` with in-scope issues (empty if none)
   2. A section `## Pre-existing Findings` for issues found in code NOT changed by this PR — classify each as Major or Minor
   3. A final verdict line: either `APPROVED` or `CHANGES REQUESTED: <item list>`
   4. A `result_contract` block and a `verification_checklist` block

   Do NOT stop mid-turn after reading files. Do NOT chain to other agents.
   ```

   - If CHANGES REQUESTED: retry relevant impl agent(s) — **max 3 review cycles**
   - If the 3rd review still fails: consult `fallback_matrix.squad.reviewer` and run one fallback review pass before surfacing the gate
   - After fallback failure: emit `[Gate] Review Limit Reached` and surface to user: `[A]ccept as-is / [S]kip review / [X]Abort`
4. Spawn `qa` (subagent_type: `{{qa_agent}}`) — run real tests against implementation
   - If FAIL: retry relevant impl agent(s), then re-review and re-qa — **max 2 QA cycles**
   - If the 2nd QA cycle still fails: consult `fallback_matrix.squad.qa` and run one fallback verification pass before surfacing the gate
   - After fallback failure: emit `[Gate] QA Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`
5. Spawn `techlead-audit` (subagent_type: `{{techlead_agent}}`) → **Conformance Gate**: verifica workstreams cobertos, conformidade arquitetural, TDD compliance e rastreabilidade de requisitos
   - If NON-CONFORMANT: retry impl agent(s) for each gap, then re-run reviewer → QA → techlead-audit — **max 2 conformance cycles**
   - If the 2nd conformance cycle still fails: consult `fallback_matrix.squad.techlead-audit` and run one fallback conformance pass before surfacing the gate
   - After fallback failure: emit `[Gate] Conformance Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`
6. Spawn quality bench in parallel (after Conformance CONFORMANT):
   - `security-rev` (subagent_type: `security-reviewer`), `privacy-rev` (subagent_type: `privacy-reviewer`), `perf-eng` (subagent_type: `performance-engineer`), `access-rev` (subagent_type: `accessibility-reviewer`), `integ-qa` (subagent_type: `integration-qa`), `code-quality` (subagent_type: `code-quality`)
   - If `ai_feature: true`: add `llm-safety-reviewer` to quality bench (prompt injection + tool authorization review)
   - If `ai_feature: true`: spawn `llm-eval-specialist` for eval gate (runs `/llm-eval` inline) — if eval score REGRESSED, present to user before UAT
   - **After all bench agents return**, classify findings by severity:
     - **BLOCKING** (must fix): security vulns, PII/data leaks, privacy violations, CI-breaking lint errors, WCAG A/AA failures
     - **WARNING** (should fix): perf regressions, non-critical accessibility, integration risks, code quality debt
   - If BLOCKING issues: emit `[Gate] Quality Bench Blocking Issues | N findings`, spawn the relevant impl agent(s) to fix, re-run only the agents that flagged issues — **max 2 fix cycles**
   - If a bench agent fails structurally: consult `fallback_matrix.squad.<agent-name>` before surfacing the failure gate
   - If blocking persists after 2 cycles: emit `[Gate] Quality Bench Unresolved` → surface `[A]ccept with known issues / [X]Abort`
   - If only WARNINGS: surface summary → `[A]ccept and advance / [F]ix before advancing`
6b. **CodeRabbit Final Review Gate** (deterministic, tool-based — complementar ao LLM reviewer):
   - Run `bash plugins/claude-tech-squad/bin/coderabbit_gate.sh` and capture exit code
   - Exit `0`: emit `[Gate] CodeRabbit Final Review | clean or skipped` → advance to Step 7
   - Exit `2` (findings detected):
     - Re-spawn `reviewer` (subagent_type: `{{reviewer_agent}}`) with the CodeRabbit output as `{{coderabbit_findings}}` and instruction: "Resolva cada finding, aplique apenas o minimo necessario, retorne disposicao por finding (fixed / false-positive-ignored-because-<reason>)."
     - Re-run the gate script after reviewer finishes
     - Repeat — **max 2 remediation cycles**
     - If findings persist after 2 cycles: emit `[Gate] CodeRabbit Final Review Unresolved` → surface `[A]ccept with known issues (document as tech debt in SEP log) / [X]Abort`
   - Exit `1` (CLI error/auth): emit `[Gate Error] CodeRabbit Final Review | <reason>` → surface `[R]etry / [S]kip gate (document as risk) / [X]Abort`
7. Spawn `docs-writer`
8. Spawn `jira-confluence` (subagent_type: `jira-confluence-specialist`)
9. Spawn `pm-uat` (subagent_type: `pm`) → **Gate 6: UAT Approval**
   - If REJECTED: fix gaps and re-run reviewer → QA → techlead-audit → quality bench → UAT — **max 2 UAT cycles**
   - If the 2nd UAT cycle still fails: consult `fallback_matrix.squad.pm` and run one fallback product acceptance pass before surfacing the gate
   - After fallback failure: emit `[Gate] UAT Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`

**Phase 2 explicit subagent_type mappings** (name → subagent_type):

Stack-aware (use routing variables from Step 1):
- `tdd-impl` → `tdd-specialist`
- `backend-dev` → `{{backend_agent}}` (e.g. `django-backend`, `python-developer`, or `backend-dev`)
- `frontend-dev` → `{{frontend_agent}}` (e.g. `django-frontend`, `react-developer`, `vue-developer`, or `frontend-dev`)
- `platform-dev` → `platform-dev`
- `reviewer` → `{{reviewer_agent}}` (e.g. `code-reviewer` for Django, `reviewer` otherwise)
- `qa` → `{{qa_agent}}` (e.g. `qa-tester` for web stacks, `qa` otherwise)
- `techlead-audit` → `{{techlead_agent}}`
- `security-rev` → `security-reviewer`
- `privacy-rev` → `privacy-reviewer`
- `perf-eng` → `performance-engineer`
- `access-rev` → `accessibility-reviewer`
- `integ-qa` → `integration-qa`
- `code-quality` → `code-quality`
- `docs-writer` → `docs-writer`
- `jira-confluence` → `jira-confluence-specialist`
- `pm-uat` → `{{pm_agent}}`

Each spawn: `Agent(team_name=<squad-team>, name=<name>, subagent_type="claude-tech-squad:<subagent>", prompt=...)`

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

## Step 3 — Team Cleanup (before SEP log)

Clean up the team created at Step 2 before writing the SEP log so cleanup status can be recorded:

```
TeamDelete(name="squad")
```

Capture outcome into `{{team_cleanup_status}}` (`success` or `failed: <reason>`). On failure, do not halt — emit a warning and continue:

- On success: emit `[Team Deleted] squad | cleanup complete`
- On failure: emit `[Team Cleanup Warning] squad | <reason>`

---

## Step 4 — Write Execution Log (SEP Runtime Resilience)

### Run Cost Summary and SEP Log

**python3 plugins/claude-tech-squad/bin/squad-cli cost + sep-log** (preferred — uses real token counts collected during the run):

```bash
# Get cost summary
python3 plugins/claude-tech-squad/bin/squad-cli cost --run-id {{feature_slug}} --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state

# Generate SEP log from collected state
python3 plugins/claude-tech-squad/bin/squad-cli sep-log --run-id {{feature_slug}} --output-dir ai-docs/.squad-log --state-dir .squad-state
```

The `cost` command returns `tokens_in`, `tokens_out`, `estimated_cost_usd`, `budget_percent`, and `per_teammate` breakdown. Emit:
```
[Run Summary] /squad | teammates: {{N}} | tokens: {{total_input}}K in / {{total_output}}K out | est. cost: ~${{usd}} | duration: {{elapsed}}
```

The `sep-log` command generates the complete SEP log file with YAML frontmatter from the state collected during the run (all teammate data, checkpoints, health signals, fallbacks, doom loops).

If `squad-cli` is not available: sum tokens manually across all teammates, estimate cost at input x $15/M + output x $75/M, and write the SEP log manually to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-squad-{{run_id}}.md` with full YAML frontmatter. When writing manually, substitute every `{{...}}` placeholder with the captured value — including `{{team_cleanup_status}}` from Step 3 (use `success` or `failed: <reason>`; never leave the literal placeholder).

**Required frontmatter fields (squad):**

```yaml
---
run_id: {{run_id}}
skill: squad
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}       # required — refresh on every edit
final_status: completed | in_flight | aborted
execution_mode: teammates
architecture_style: {{style}}
checkpoints: [preflight-passed, discovery-complete, implement-complete, quality-complete, release-prepared]
teammates_spawned: {{N}}
fallbacks_invoked: []
retry_count: {{N}}
tokens_input: {{actual_or_null}}   # required — actual measurement or null; 0 placeholder forbidden
tokens_output: {{actual_or_null}}  # required — actual measurement or null; 0 placeholder forbidden
estimated_cost_usd: {{usd}}
total_duration_ms: {{ms}}
escape_hatch_used: false
skipped_phases: []
team_cleanup_status: {{team_cleanup_status}}
---
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

---

## Final Output

```
## Squad Complete

### Agent Execution Log
- Team: squad
- Phase: discovery
  - Teammate: pm | Status: completed
  - Teammate: business-analyst | Status: completed
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
  - Teammate: techlead-audit | Status: CONFORMANT
  - Batch: quality-bench | Teammates: [..., code-quality] | Status: completed
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
