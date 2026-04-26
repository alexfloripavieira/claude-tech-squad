# Agent Result Contract — Discovery Variant

Discovery teammates (planner, architect, business-analyst, ux-designer, prd-author, inception-author, tasks-planner) are **analysis-class**. Their ARC differs from execution-class teammates in three ways:

1. `evidence.test_command` is replaced by `evidence.artifact_path` pointing to the produced document (PRD, TechSpec, ADR, brief).
2. `files_touched` lists artifact files, not source code.
3. `verification_checklist` includes a `Documentation Standard — Context7 First` check whenever the artifact references a third-party library, framework, or API.

## Required blocks

```yaml
result_contract:
  status: PASS | FAIL | NEEDS_HUMAN
  confidence: low | medium | high
  files_touched: [<artifact paths>]
  evidence:
    artifact_path: "<path to PRD / TechSpec / ADR / brief>"
    word_count: <int>
    sources_used: [<library names verified via Context7>]
  blockers:
    - id: <stable id>
      severity: BLOCKING | WARNING | INFO
      description: <one-line>
  next_action: "<one-line handoff>"

verification_checklist:
  - "[x|FAIL] Artifact follows the canonical template under templates/"
  - "[x|FAIL] All third-party APIs referenced were verified via Context7"
  - "[x|FAIL] Acceptance criteria are testable (Given/When/Then or equivalent)"
  - "[x|FAIL] tool_allowlist respected"
```

## Orchestrator-side validation (used by `/discovery` SKILL.md)

A teammate response is only structurally valid when it contains ALL of:
- the role-specific body requested by that agent
- a plan section (`## Pre-Execution Plan` for execution agents, `## Analysis Plan` for analysis agents)
- a final `result_contract` block
- a final `verification_checklist` block

Required block shape used at runtime by the discovery orchestrator:

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
- `status` must reflect the real execution outcome.
- `blockers`, `artifacts`, `findings` use empty lists when nothing to report.
- `next_action` must identify the single best downstream step.
- `confidence_after_verification` must match `confidence` in `result_contract`.
- Missing `result_contract` OR missing `verification_checklist` means the teammate output is structurally invalid → trigger the Teammate Failure Protocol (`runtime-resilience.md`).

## Cross-references

- Implementation-class ARC: `../../implement/references/arc-schema.md`
- Templates: `templates/prd-template.md`, `templates/techspec-template.md`
- Policy: `plugins/claude-tech-squad/runtime-policy.yaml`
