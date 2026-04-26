# Gate Catalog — `/implement`

Reference of every gate in the `/implement` pipeline, what it consumes, what it emits, and the operator escape hatch.

| Step | Gate                                  | Consumes (ARC fields)                  | Emits                            | Auto-advance? |
|------|---------------------------------------|----------------------------------------|----------------------------------|---------------|
| 0    | Preflight Gate                        | runtime-policy.yaml, fixture state     | preflight_pass                   | No            |
| 1    | Validate Blueprint                    | discovery output, PRD, TechSpec        | blueprint_ack                    | No            |
| 3    | TDD Failing-Tests Gate                | tdd-specialist `result_contract`       | tdd_red_state                    | No            |
| 4    | Implementation Batch                  | per-dev `result_contract`              | code_green                       | No            |
| 5    | Reviewer Gate                         | reviewer `result_contract`             | review_findings                  | Conditional   |
| 5b   | Pre-existing Findings Triage          | reviewer `pre_existing_findings`       | triage_decision                  | Operator only |
| 6    | QA Gate                               | qa `result_contract`                   | qa_verdict                       | Conditional   |
| 6b   | TechLead Conformance Audit            | full chain `result_contract`           | conformance_verdict              | No            |
| 7    | Quality Bench (parallel)              | 5+ specialist `result_contract`s       | quality_bench_findings           | No            |
| 7b   | Quality Bench Issue Resolution        | dev `result_contract`                  | quality_clear                    | No            |
| 7c   | CodeRabbit Final Review Gate          | reviewer `result_contract`             | final_review_clear               | No            |
| 8    | Docs Writer Gate                      | docs-writer `result_contract`          | docs_updated                     | Conditional   |
| 9    | Jira/Confluence Update                | jira-confluence `result_contract`      | tickets_updated                  | Conditional   |
| 9b   | Coverage Gate                         | qa `evidence.coverage_percent`         | coverage_pass                    | No            |
| 10   | PM UAT Gate                           | pm `result_contract`                   | uat_verdict                      | Operator only |
| 11   | SEP Log Write                         | full run trace                         | sep_log_path                     | Always        |

## Auto-advance eligibility

A gate is auto-advance-eligible only when ALL the following are true (per `runtime-policy.yaml.auto_advance`):

- All teammate ARCs report `confidence: high`
- Zero `severity: BLOCKING` findings
- The gate appears in `auto_advance.eligible_gates`

## Operator-only gates

Gates marked **Operator only** above always require explicit human acknowledgement and cannot be auto-advanced.

## Failure routing

When a gate fails and retries are exhausted, the orchestrator consults `runtime-policy.yaml.fallback_matrix` to choose a fallback agent, then `runtime-policy.yaml.severity_policy` to decide whether to halt or continue with a `WARNING` recorded in the SEP log.

## Cycle caps

Values must match `retry_budgets` in `runtime-policy.yaml`:

| Phase | Cycle cap | Operator-gate prompt on cap |
|---|---|---|
| Reviewer | 3 | `[A]ccept / [S]kip / [X]Abort` |
| QA | 2 | `[A]ccept / [X]Abort` |
| Conformance | 2 | `[A]ccept / [X]Abort` |
| Quality-bench fix | 2 | `[A]ccept with known issues / [X]Abort` |
| CodeRabbit final review | 2 | `[A]ccept with known issues / [X]Abort` |
| UAT | 2 | `[A]ccept / [X]Abort` |

After hitting a cycle cap and exhausting one fallback pass, the orchestrator emits `[Gate] <Name> Limit Reached` and surfaces the prompt above.

## Reviewer gate — output contract

The reviewer must produce ALL of:

1. `## Findings` — in-scope issues (empty list if none)
2. `## Pre-existing Findings` — issues found in code NOT changed by this PR, each classified Major or Minor
3. Final verdict line: `APPROVED` or `CHANGES REQUESTED: <items>`
4. `result_contract` + `verification_checklist` blocks

Reviewer must NOT stop mid-turn after reading files and must NOT chain to other agents.

## Pre-existing Findings Triage Gate (Step 5b)

After reviewer APPROVED:

- If reviewer flagged any **Major** pre-existing findings: emit `[Gate] Pre-existing Findings | N Major issue(s)` and surface `[T]icket / [S]kip / [X]Abort`. `[T]` spawns `jira-confluence-specialist` to create one Jira subtask per Major finding.
- Only Minor or none: auto-advance.

Records `pre_existing_findings_triaged: ticketed | skipped | none` in SEP log.

## Conformance Audit (Step 6b — mandatory, never skippable)

After QA PASS, spawn `techlead` for a conformance audit. Returns `CONFORMANT` or `NON-CONFORMANT`.

Audit checks:
1. Workstream coverage
2. Architecture conformance vs `{{architecture_style}}`
3. TDD compliance
4. Requirements traceability
5. Technical debt introduced

NON-CONFORMANT path: re-spawn responsible impl agents with each gap as context, re-run reviewer + QA + audit. Cycle cap = 2 (then one fallback pass, then `[Gate] Conformance Limit Reached`).

## Quality Bench Issue Resolution (Step 7b)

Findings classified by severity:

- **BLOCKING**: OWASP Top 10, data/PII leaks, privacy violations, failing tests, lint errors blocking CI, broken accessibility (WCAG A/AA)
- **WARNING**: performance regressions, non-critical accessibility gaps, integration risks, code quality debt
- **INFO**: style, optional improvements, low-priority refactors

BLOCKING path: spawn impl agents per affected domain with prompt template:

```
## Blocking Issue Fix
### Original Implementation: {{approved_implementation}}
### Blocking Issues to Fix: {{blocking_findings_for_this_domain}}
---
Fix ONLY the listed issues. For each fix: Issue → Root Cause → Change Made.
```

Re-spawn only the bench agents that flagged blocking issues. Cycle cap = 2 → `[Gate] Quality Bench Unresolved`.

WARNING/INFO path: surface `[A]ccept and advance / [F]ix before advancing`.

## Coverage Gate (Step 9b)

Detect coverage tool from stack (`coverage`/`pytest --cov` for Python; `nyc`/`vitest --coverage` for JS). If delta < 0 from blueprint baseline (or `main`): emit `[Gate] Coverage Drop`, surface `[C]ontinue / [T]ests-first`. `[T]` re-runs QA after new tests.

If tool unavailable or delta ≥ 0: silent advance.

## UAT Gate (Step 10 — operator only)

PM validates each AC against QA evidence + conformance + quality bench. Returns `APPROVED` or `REJECTED` with specific gaps.

REJECTED path: present gaps, surface `[R]e-queue / [S]kip`. `[R]` re-runs Steps 5–10 with `## UAT Rejection Feedback` prepended. Cycle cap = 2 → fallback `pm` pass → `[Gate] UAT Limit Reached`.
