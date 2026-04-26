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
