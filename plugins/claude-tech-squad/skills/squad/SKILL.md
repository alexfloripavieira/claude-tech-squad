---
name: squad
description: This skill should be used when delivering an end-to-end feature or epic that needs the full pipeline (discovery → blueprint → TDD implementation → quality → docs → reliability → release). Trigger with "rodar squad completa", "feature completa", "/squad", "epic delivery", "full pipeline", "tech squad workflow", "end-to-end delivery", "rodar a esteira completa", "entrega completa". Uses every specialist as independent teammate with reviewer/QA/conformance/UAT gates and SEP log capture. NOT for planning-only (use /discovery), build-only (use /implement), or single-file fixes (use /bug-fix).
user-invocable: true
---

# /squad — Full Technology Squad

Run the complete end-to-end workflow. Every specialist runs as an independent teammate in its own tmux pane. Pipeline: discovery → blueprint → implementation → quality → docs → release.

Heavy reference material lives under `references/`. This SKILL.md is the orchestration spine; consult the referenced files for the full specifications.

## Global Safety Contract

This contract applies to every teammate. Violating it requires explicit written user confirmation. No teammate may, under any circumstances:

- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation.
- Delete cloud resources (S3 buckets, databases, clusters, queues, Kafka topics) in production.
- Run `tsuru app-remove`, `heroku apps:destroy`, or any equivalent application deletion command.
- Merge to `main`, `master`, or `develop` without an approved pull request.
- Force-push to any protected branch.
- Remove secrets or environment variables from production.
- Destroy infrastructure via `terraform destroy` or equivalent.
- Disable or bypass authentication/authorization as a workaround.
- Deploy to production without a documented and tested rollback plan.
- Disable SLO alerting or monitoring.
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization.
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands.
- Apply migrations or schema changes to production without first verifying a backup exists.
- Deploy to production before staging has been successfully deployed and verified.
- Create a version tag or cut a release when CI is FAILING.

If a teammate believes a task requires one of these actions, STOP and surface the decision to the user. Deadline pressure does not override this contract.

## Core Principle

Do not assume the stack, conventions, or product domain. Discover them from the repository and validate technical decisions via context7.

## TDD Default Mode

When `/squad` is used for code changes, TDD is the default. Implementation begins from failing tests; use red-green-refactor as the normal model. TDD may be relaxed only when the task is documentation-only or release-only, the repository has no viable automated test path, or an external constraint makes tests-first impossible. If relaxed, state so explicitly and explain why.

## Teammate Architecture

This workflow creates a single team that persists across all phases:

1. `TeamCreate` — create the squad team (once, at start).
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist as a teammate.
3. `SendMessage` — communicate with running teammates.
4. `TaskCreate` + `TaskUpdate` — assign and track work.

Do NOT use `Agent` without `team_name` — that runs an inline subagent, not a visible teammate pane.

## Operator Visibility Contract

Emit explicit lifecycle lines for every preflight, team create, phase, teammate spawn/done/retry, fallback, gate, checkpoint, batch, token usage, and rollover event.

> See `references/runtime-resilience.md` for the full list of operator visibility lines and emission rules.

## Context Rollover Gate

At every phase boundary, emit `[Token Usage]`. At `>=100k` emit `[Context Advisory]`; at `>=140k` emit `[Gate] Context Rollover Required` and halt with options `[R|D|F]`.

> See `references/runtime-resilience.md` for full rollover thresholds, options, and the `context_management` policy keys.

## Progressive Disclosure — Context Digest Protocol

Detailed reference docs live under `references/`. Do not forward full upstream agent output to every downstream agent. Produce a context digest (max 500 tokens) between sequential phases.

Digest format:

```markdown
## Context Digest — {{source_agent}} ({{phase}})

**Key decisions:** {{bullet_list}}
**Artifacts produced:** {{file_list}}
**Open questions:** {{list_or_none}}
**Blockers:** {{list_or_none}}
**Architecture style:** {{style}}
**Full output reference:** available on request from orchestrator
```

When transitioning from discovery to implementation, produce a digest of the full blueprint — the implementation phase receives the digest plus the full blueprint file path for on-demand access. The orchestrator tracks token consumption per teammate and logs it in the SEP log.

## Teammate Failure Protocol

A teammate has failed silently if it returns empty, an error, or output that does not match the expected format (including the required `result_contract`). Re-spawn once after a doom-loop check; if it still fails, consult `fallback_matrix.squad.<name>` in `runtime-policy.yaml`; if no fallback (or fallback also fails), open a user gate with `[R]etry / [S]kip / [X]Abort`. Do not advance until every teammate in the current step has returned valid output, been explicitly skipped, or the run aborted.

> See `references/runtime-resilience.md` for the full protocol, doom-loop semantics, and skip-degradation rules.

## Inline Health Check

After every `[Teammate Done]`, run `python3 plugins/claude-tech-squad/bin/squad-cli health` (preferred) and inject the returned `context_enrichment` text into the next teammate's prompt. Emit `[Health Check] <name> | signals: ...`. Critical signals trigger a `[Health Warning]` and may surface to the user. Cross-phase health is carried from discovery into implementation.

> See `references/runtime-resilience.md` for the 6 signals, full CLI invocation, and manual fallback evaluation.

## Agent Result Contract (ARC)

A teammate response is structurally valid only when it contains the role-specific body, a plan section (`## Pre-Execution Plan` or `## Analysis Plan`), a final `result_contract` block, and a final `verification_checklist` block. Missing either YAML block triggers the Teammate Failure Protocol.

> See `references/arc-schema.md` for the full schema, validation rules, and required field semantics.

## Visual Reporting Contract

After every teammate returns, pipe its Result Contract `metrics` JSON to `plugins/claude-tech-squad/scripts/render-teammate-card.sh`. Before writing the SEP log, assemble the pipeline summary JSON and pipe to `plugins/claude-tech-squad/scripts/render-pipeline-board.sh`. Renderer failures are non-fatal — log a WARNING and continue. Respect `observability.teammate_cards.format` and `observability.pipeline_board.enabled` in `runtime-policy.yaml`.

> See `references/visual-reporting.md` for the full contract.

## Runtime Resilience Contract

Load `plugins/claude-tech-squad/runtime-policy.yaml` before repository recon or team creation. It is the source of truth for retry budgets, fallback matrix, severity policy, checkpoint/resume rules, and reliability metrics in SEP logs. If the file is missing or unreadable, halt and surface `[Gate] Runtime Policy Missing` — never silently use hardcoded defaults.

> See `references/runtime-resilience.md` for the full operator visibility list, failure protocol, health check, and rollover gate.

---

## Execution

### Preflight Gate

Before recon and team creation, validate the run contract. Emit `[Preflight Start] squad`.

```bash
python3 plugins/claude-tech-squad/bin/squad-cli preflight --skill squad --policy plugins/claude-tech-squad/runtime-policy.yaml --project-root .
python3 plugins/claude-tech-squad/bin/squad-cli init --run-id {{feature_slug}} --skill squad --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
```

The first call returns JSON with `stack`, `ai_feature`, `routing`, `lint_profile`, `docs_lookup_mode`, `policy_version`, `token_budget_max`, `orphaned_discoveries`, `retro_counter`, `resume_from`, and `warnings`. Use those values to set every `{{variable}}`. If `squad-cli` is unavailable, fall back to manual preflight (read `runtime-policy.yaml`, detect stack from signal files, resolve routing, check orphans, read retro counter).

**Ticket Intake** — If the user input matches `[A-Z]+-[0-9]+`, `#[0-9]+`, or `LIN-[0-9]+`: read the ticket via the appropriate MCP tool, extract title/description/acceptance criteria/priority/subtasks, for Epics also read child stories via JQL `parent = {{ticket_id}}`, use the extracted content as `{{user_request}}`, and emit `[Ticket Read] {{source}} | {{ticket_id}} | type={{issue_type}} | priority={{priority}}`. If MCP is unavailable, ask the user to paste the ticket — do not block.

Emit all preflight warnings, then `[Preflight Passed] squad | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`.

### Checkpoint / Resume Rules

Save checkpoints at `preflight-passed`, `discovery-confirmed`, `implementation-complete`, `release-signed-off`:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint save --run-id {{feature_slug}} --cursor <checkpoint> --state-dir .squad-state
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint resume --skill squad --state-dir .squad-state
```

Without `squad-cli`: emit `[Checkpoint Saved] squad | cursor=<checkpoint>` and inspect the latest `ai-docs/.squad-log/*-squad-*.md` for resume.

### Escape Hatch — Skip Forward

At any gate, the user may jump forward (Discovery → Implementation, Implementation review/QA → Docs+UAT, Implementation → Release). Include `[J] Jump forward` in every gate's options. Emit `[Escape Hatch] jumping from {{current_phase}} to {{target_phase}} | Reason: user requested`. Log `escape_hatch_used: true` and `skipped_phases` in the SEP log. Skipped phases are not recoverable in the same run; emit `[Health Warning] phases skipped via escape hatch — downstream quality may be degraded`.

### Step 1 — Repository Recon

Read `CLAUDE.md` and `README.md`. Stack, AI, and routing detection are resolved by the preflight CLI; use the returned `stack`, `ai_feature`, `routing` (with `pm_agent`, `techlead_agent`, `backend_agent`, `frontend_agent`, `reviewer_agent`, `qa_agent`), and `lint_profile` directly.

If `squad-cli` was unavailable, detect stack from signal files (`manage.py` + django → `django`; `package.json` with react/vue/next/nuxt → `react`/`vue`; `tsconfig.json` → `typescript`; `go.mod` → `go`; `Cargo.toml` → `rust`; `pom.xml`/`build.gradle` → `java`; `Gemfile` → `ruby`; `composer.json` → `php`; `*.csproj` → `dotnet`; `mix.exs` → `elixir`; `pyproject.toml`/`requirements.txt` without manage.py → `python`). Scan source for AI library imports (openai, anthropic, langchain, pgvector) to set `ai_feature`.

If `ai_feature: true` activate the LLM-enhanced bench in Phases 1 and 2 and emit `[AI Detected] LLM/AI features found — activating AI specialist bench`.

Emit: `[Stack Detected] {{detected_stack}} | pm={{pm_agent}} | techlead={{techlead_agent}} | backend={{backend_agent}} | frontend={{frontend_agent}} | reviewer={{reviewer_agent}} | qa={{qa_agent}}`.

### Step 2 — Create Squad Team

Call `TeamCreate` with `name="squad"` and a one-line description. Emit `[Team Created] squad`.

---

### PHASE 0: DELIVERY DOCS

Emit `[Phase Start] delivery-docs`. Each step reuses existing artifacts when valid against its template.

1. **PRD** → `ai-docs/prd-{{feature_slug}}/prd.md` (reuse if validates against `templates/prd-template.md`; else spawn `prd-author`). Checkpoint `prd-produced`.
2. **TechSpec** → `ai-docs/prd-{{feature_slug}}/techspec.md` (reuse or spawn `inception-author`). Checkpoint `techspec-produced`.
3. **Tasks** → `ai-docs/prd-{{feature_slug}}/tasks.md` + `<num>_task.md` (reuse or spawn `tasks-planner`). Checkpoint `tasks-produced`.
4. **Work items** → `ai-docs/prd-{{feature_slug}}/work-items.md` (spawn `work-item-mapper`). Checkpoint `work-items-produced`.

Spawns use `Agent(team_name="squad", name=<role>, subagent_type="claude-tech-squad:<role>", prompt=<digest>)`. Between steps: pipe metrics to `render-teammate-card.sh`. If any agent returns `confidence: low` with `gaps_count > 0`, open `[Gate] Delivery Docs Confidence Low | step: <step> | gaps: <gap_list>`. If `delivery_gates.enabled: true` and `work-item-mapper` reports a BLOCKING finding, halt and open a user gate.

Emit `[Phase Done] delivery-docs`.

---

### PHASE 1: DISCOVERY

Emit `[Phase Start] discovery`. Follow the `/discovery` Steps 3–13 sequence with Gates 1–5 (Product Definition, Scope Validation, Technical Tradeoffs, Architecture Direction, Blueprint Confirmation). Spawn the specialist batch and quality baseline batch in parallel after Gate 4. If `ai_feature: true`, add `ai-engineer`, `rag-engineer` (when RAG detected), and `prompt-engineer` to the specialist batch, and after the blueprint spawn `llm-eval-specialist`, `llm-safety-reviewer`, and `llm-cost-analyst` automatically.

> See `references/gates-catalog.md` for the full Phase 1 gate sequence and `references/teammate-roster.md` for every `name → subagent_type` mapping (core chain, specialist batch, quality baseline batch).

All architecture-sensitive agents receive `{{architecture_style}}`; review-sensitive agents receive `{{lint_profile}}`. Every prompt ends with: "Do NOT chain to other agents — the orchestrator handles sequencing."

Emit `[Phase Done] discovery | Blueprint confirmed`.

---

### Test Gate (Mandatory)

This skill is in `mandatory_test_gate.skills_in_scope` (see `runtime-policy.yaml#mandatory_test_gate`).

Contract:
- `tdd-specialist` MUST be spawned before any dev agent.
- `test-automation-engineer` MUST be spawned after dev agents and before reviewer agents.
- After `test-automation-engineer` completes, the PostToolUse hook `hooks/test-gate.sh` evaluates the gate. A `BLOCKING` verdict halts the pipeline; the operator decides skip+debt, write manual, or abort.
- No exemption is available for this skill. Any pipeline producing a new or modified production file without a paired test will block.

Canonical pre-impl invocation:

```
Agent(team_name=<team>, name="tdd-specialist", subagent_type="claude-tech-squad:tdd-specialist",
  prompt="Write the first failing tests for the upcoming implementation slice using red-green-refactor. Do NOT write production code.")
```

Canonical post-impl invocation:

```
Agent(team_name=<team>, name="test-automation-engineer", subagent_type="claude-tech-squad:test-automation-engineer",
  prompt="Validate test coverage for files modified in the implementation phase. Add edge-case and regression tests. Pair every new/modified production file with a test. Report unpaired files in your Result Contract.")
```

---

### PHASE 2: IMPLEMENTATION

Emit `[Phase Start] implementation`. Sequential with parallel batches:

1. `tdd-impl` writes the first failing tests.
2. Implementation batch in parallel: `backend-dev`, `frontend-dev`, `platform-dev` (only relevant workstreams).
3. `reviewer` — max 3 review cycles, then fallback, then `[Gate] Review Limit Reached`.
4. `qa` — max 2 QA cycles, then fallback, then `[Gate] QA Limit Reached`.
5. `techlead-audit` — Conformance Gate; max 2 cycles, then fallback, then `[Gate] Conformance Limit Reached`.
6. Quality bench in parallel after CONFORMANT: `security-rev`, `privacy-rev`, `perf-eng`, `access-rev`, `integ-qa`, `code-quality` (+ `llm-safety-reviewer` and `llm-eval-specialist` if `ai_feature: true`). Classify findings BLOCKING vs WARNING; max 2 fix cycles.
6b. **CodeRabbit Final Review Gate** — `bash plugins/claude-tech-squad/bin/coderabbit_gate.sh`; on exit 2 re-spawn `reviewer` with `{{coderabbit_findings}}` (max 2 remediation cycles); on exit 1 surface `[Gate Error] CodeRabbit Final Review`.
7. `docs-writer`.
8. `jira-confluence` (subagent_type `jira-confluence-specialist`).
9. `pm-uat` — Gate 6 UAT Approval; max 2 UAT cycles, then fallback, then `[Gate] UAT Limit Reached`.

> See `references/gates-catalog.md` for the full reviewer output contract, severity classifications, fallback semantics, and CodeRabbit gate handling. See `references/teammate-roster.md` for every `name → subagent_type` mapping.

Emit `[Phase Done] implementation | UAT approved`.

---

### PHASE 3: RELEASE

Emit `[Phase Start] release`. After UAT approval spawn:

```
Agent(team_name=<team>, name="release", subagent_type="claude-tech-squad:release",
  prompt="Release Preparation. Inventory changes, validate CI/CD and deploy assumptions, define rollback steps, identify communication and monitoring. Return release checklist with go/no-go.")
```

Then SRE:

```
Agent(team_name=<team>, name="sre", subagent_type="claude-tech-squad:sre",
  prompt="SRE Sign-off. Assess blast radius, SLO impact, rollback readiness, canary/phased rollout strategy. Return final go/no-go.")
```

Both prompts must include `{{complete_implementation_summary}}`, `{{pm_uat_output}}`, and `{{architect_output}}` from prior phases.

Emit `[Teammate Spawned] release | pane: release`, `[Teammate Spawned] sre | pane: sre`, `[Phase Done] release | SRE sign-off received`.

---

## Team Cleanup (before SEP log)

Call `TeamDelete(name="squad")`. Capture `{{team_cleanup_status}}` (`success` or `failed: <reason>`). On success emit `[Team Deleted] squad | cleanup complete`; on failure emit `[Team Cleanup Warning] squad | <reason>` and continue.

---

## Write Execution Log (SEP Runtime Resilience)

```bash
python3 plugins/claude-tech-squad/bin/squad-cli cost --run-id {{feature_slug}} --policy plugins/claude-tech-squad/runtime-policy.yaml --state-dir .squad-state
python3 plugins/claude-tech-squad/bin/squad-cli sep-log --run-id {{feature_slug}} --output-dir ai-docs/.squad-log --state-dir .squad-state
```

Emit `[Run Summary] /squad | teammates: {{N}} | tokens: {{total_input}}K in / {{total_output}}K out | est. cost: ~${{usd}} | duration: {{elapsed}}` and `[SEP Log Written] ai-docs/.squad-log/{{filename}}`.

The SEP log is written to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-squad-{{run_id}}.md` with the frontmatter `skill: squad` plus `run_id`, `timestamp`, `last_updated_at`, `final_status`, `execution_mode: teammates`, `architecture_style`, `checkpoints`, `teammates_spawned`, `fallbacks_invoked`, `retry_count`, `tokens_input`, `tokens_output`, `estimated_cost_usd`, `total_duration_ms`, `escape_hatch_used`, `skipped_phases`, `team_cleanup_status`. `tokens_input` and `tokens_output` must be the actual measurement or `null` — `0` is forbidden as a placeholder.

SEP log frontmatter skeleton (full template in `references/sep-log-template.md`):

```yaml
---
skill: squad
run_id: {{feature_slug}}
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}
final_status: {{success|partial|failed}}
execution_mode: teammates
tokens_input: {{actual_or_null}}
tokens_output: {{actual_or_null}}
teammate_token_breakdown: {}
estimated_cost_usd: {{actual_or_null}}
total_duration_ms: {{measured}}
---
```

`tokens_input` / `tokens_output` must be the actual measurement or `null` — `0` placeholders are forbidden. `teammate_token_breakdown` is a map `{teammate_name: {tokens_in, tokens_out, cost_usd}}`.

> See `references/sep-log-template.md` for the complete frontmatter, manual cost-estimation fallback, and the Final Output template (`## Squad Complete` block with Agent Execution Log, Product, Architecture, Delivery, Release, Stack Validation sections).
