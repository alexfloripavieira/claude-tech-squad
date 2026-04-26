# Runtime Resilience — `/implement` Deep Dive

Detailed mechanics behind the Runtime Resilience Contract declared in `SKILL.md`. The contract itself stays in `SKILL.md`; this reference explains the policy values, fallback paths, and doom-loop heuristics.

## Retry budget

Source: `runtime-policy.yaml.failure_handling` and `retry_budgets`.

| Phase                        | Max retries | Fallback attempts | Cycle cap |
|------------------------------|-------------|-------------------|-----------|
| TDD failing-tests            | 2           | 1                 | n/a       |
| Implementation batch         | 2           | 1                 | n/a       |
| Reviewer gate                | 2           | 1                 | 3         |
| QA gate                      | 2           | 1                 | 2         |
| TechLead conformance audit   | 2           | 1                 | 2         |
| Quality bench (per lens)     | 1           | 1                 | n/a       |
| PM UAT                       | 1           | 0                 | 2         |

## Fallback matrix

When a primary teammate exhausts its retry budget, the orchestrator invokes the fallback agent declared in `runtime-policy.yaml.fallback_matrix`. Examples:

| Primary             | Fallback                       |
|---------------------|--------------------------------|
| backend-dev         | tech-lead in pair-programming  |
| frontend-dev        | tech-lead in pair-programming  |
| reviewer            | code-reviewer                  |
| qa                  | qa-tester (Playwright path)    |
| docs-writer         | tech-writer                    |
| security-reviewer   | security-engineer              |

If the fallback also fails, the orchestrator emits `[Fallback Exhausted]` and a `NEEDS_HUMAN` ARC, halting the pipeline.

## Doom-loop detection

Source: `runtime-policy.yaml.doom_loop_detection`.

The orchestrator halts and emits `[Doom Loop Detected]` when ANY of the three patterns is observed:

1. **Pattern A — verdict flip:** the same teammate flips between `PASS` and `FAIL` 3 times in a row for the same gate.
2. **Pattern B — root-cause flip:** the techlead's diagnosed root cause differs across 3 consecutive attempts.
3. **Pattern C — drift:** the set of `files_touched` between two consecutive implementation attempts has Jaccard similarity below 0.2 (the dev keeps rewriting different files).

## Cost guardrails

Source: `runtime-policy.yaml.cost_guardrails`.

- Token budget: declared per-skill (default 5 M for `/implement`)
- Warn threshold: 75 % of budget — emits `[Cost Warning]`
- Halt threshold: 100 % of budget — emits `[Cost Halt]` and short-circuits the pipeline with a `NEEDS_HUMAN` verdict

## Auto-advance

Source: `runtime-policy.yaml.auto_advance`.

A gate is auto-advanced (no operator click) only when:

- Auto-advance is enabled globally for the skill
- The gate appears in `auto_advance.eligible_gates`
- All consumed ARCs report `confidence: high`
- Zero `severity: BLOCKING` findings in the consumed ARCs

## Entropy management

Source: `runtime-policy.yaml.entropy_management`.

After every 5 SEP logs, `runtime-policy.yaml` triggers a soft suggestion to run `/factory-retrospective`. Orphan teammates (spawned but not joined) are detected at preflight and force a reset before the run starts.

## Teammate Failure Protocol — full flow

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role (including the required `result_contract` block).

For every teammate spawned — without exception:

1. Wait for the teammate to return structured output.
2. If the return is empty, an error, or structurally invalid:
   - **Doom-loop check** — consult `doom_loop_detection` in `runtime-policy.yaml`. Compare the failed output against the prior attempt. If a doom-loop pattern is detected (`growing_diff`, `oscillating_fix`, or `same_error`):
     - Emit: `[Doom Loop Detected] <name> | pattern=<rule_name> | retries=<count>`
     - Skip the retry; go directly to step 3 (fallback)
   - Else: emit `[Teammate Retry] <name> | Reason: silent failure — re-spawning` and re-spawn once with the identical prompt.
3. If the second attempt also fails (or doom-loop short-circuited step 2):
   - Read `runtime-policy.yaml.fallback_matrix.implement.<name>`
   - If a fallback subagent is listed: emit `[Fallback Invoked] <name> -> <fallback> | Reason: primary failed twice`. Spawn the fallback once with the same context and an explicit instruction that it is acting as a surrogate for `<name>`. If the fallback returns valid output, continue and record `fallback_invocations` + `teammate_reliability` in the SEP log.
   - If no fallback exists, or the fallback also fails: emit `[Gate] Teammate Failure | <name> failed twice and fallback did not recover`. Surface `[R]etry / [S]kip / [X]Abort` to the user.
4. **Sequential teammates** (output feeds the next agent): `[S]` degrades ALL downstream teammates that depend on this output — warn the user explicitly before accepting skip.
5. **Parallel batch teammates**: `[S]` on one agent does not block the batch, but the missing output must be logged as a risk in the final report.
6. Do NOT advance to the next step until every teammate in the current step has returned valid output, been explicitly skipped, or the run aborted.

## Inline Health Check — full signals

After every `[Teammate Done]`, run the 6-signal health check:

1. `retry_detected`
2. `fallback_used`
3. `doom_loop_short_circuit`
4. `token_budget_pressure`
5. `low_confidence_chain`
6. `blocking_findings_accumulating`

Preferred: `python3 plugins/claude-tech-squad/bin/squad-cli health` (deterministic, saves ~2 K tokens per teammate). Returns JSON with `signals_triggered`, `context_enrichment` (text to prepend to next teammate), `budget_percent`, `is_critical`.

Fallback: evaluate the 6 signals manually from the teammate's `result_contract`.

- Emit: `[Health Check] <name> | signals: <triggered_or_ok>`
- **warning signals**: prepend `context_enrichment` to next teammate
- **critical signals**: emit `[Health Warning]` and surface to user

This is especially important in `/implement` because the pipeline is long — a problem detected at review can be communicated to QA before it runs, avoiding wasted cycles.

## Context Rollover Gate

Between every teammate completion and the next teammate spawn, inspect cumulative token usage. Emit `[Token Usage]` at each phase boundary.

| Used tokens | Action |
|---|---|
| `>= 100k` | Emit `[Context Advisory]`. Continue, but plan next teammate as last before rollover. |
| `>= 140k` | Emit `[Gate] Context Rollover Required` and halt for `[R\|D\|F]` operator choice. |

- `R` — Rollover now. Spawn `context-summarizer` as a teammate; halt for `/clear` + `/resume-from-rollover <run_id>`.
- `D` — Defer one phase. Proceed one more teammate, then force rollover.
- `F` — Force continue. Emit `[Rollover Declined]` with reason. Degradation risk accepted and logged.

Thresholds and summarizer agent declared in `runtime-policy.yaml.context_management`. Checks only at boundaries, never mid-teammate.

Rationale: `docs/architecture/0001-context-rollover.md`.
