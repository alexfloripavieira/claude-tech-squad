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

## Cross-references

- Implementation-class ARC: `../../implement/references/arc-schema.md`
- Templates: `templates/prd-template.md`, `templates/techspec-template.md`
- Policy: `plugins/claude-tech-squad/runtime-policy.yaml`
