# Agent Result Contract (ARC) — Full Schema

A teammate response is only structurally valid when it contains ALL of:

- the role-specific body requested by that agent
- a plan section (`## Pre-Execution Plan` for execution agents, `## Analysis Plan` for analysis agents)
- a final `result_contract` block
- a final `verification_checklist` block

## Required blocks

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

## Validation rules

- `status` must reflect the real execution outcome.
- `blockers`, `artifacts`, and `findings` use empty lists when there is nothing to report.
- `next_action` must identify the single best downstream step.
- `confidence_after_verification` must match `confidence` in `result_contract`.
- Missing `result_contract` OR missing `verification_checklist` means the teammate output is structurally invalid and must trigger the Teammate Failure Protocol.
