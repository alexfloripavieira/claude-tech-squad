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
