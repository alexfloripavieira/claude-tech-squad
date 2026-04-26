# Agent Result Contract (ARC) — Reference Schema

Canonical schema every teammate spawned by `/implement` must return. Skills enforce this mechanically via the Teammate Failure Protocol.

## Required blocks

```yaml
result_contract:
  status: PASS | FAIL | NEEDS_HUMAN
  confidence: low | medium | high
  files_touched: [<paths>]
  evidence:
    test_command: "<exact command run, including args>"
    test_output_path: "<path or inline excerpt; mandatory for status: PASS>"
    coverage_percent: <number, when applicable>
  blockers:
    - id: <stable id>
      severity: BLOCKING | WARNING | INFO
      description: <one-line>
      file: <path:line>
  next_action: "<one-line handoff for the orchestrator>"

verification_checklist:
  - "[x|FAIL] <role-specific check 1>"
  - "[x|FAIL] <role-specific check 2>"
  - "[x|FAIL] tool_allowlist respected"
  - "[x|FAIL] No destructive operation executed without explicit user approval"
```

## Status semantics

| status        | Orchestrator action                                                  |
|---------------|----------------------------------------------------------------------|
| PASS          | Advance to next gate                                                 |
| FAIL          | Retry per `runtime-policy.yaml.failure_handling` (max 2 retries)     |
| NEEDS_HUMAN   | Halt and surface to operator                                          |

## Confidence semantics

| confidence | Auto-advance eligible?                              |
|-----------|------------------------------------------------------|
| high      | Yes, if `auto_advance` policy and zero BLOCKING      |
| medium    | Operator gate required                               |
| low       | Operator gate + `NEEDS_HUMAN` recommended            |

## Severity classification

- **BLOCKING** stops the pipeline immediately
- **WARNING** is logged into the SEP log but does not stop the run
- **INFO** is informational only

See also `runtime-policy.yaml.severity_policy` for the global mapping.

## Failure modes (Teammate Failure Protocol)

Any of these are treated as silent failure and trigger the retry/fallback budget:

- Missing `result_contract` block
- Missing `verification_checklist` block
- `status: PASS` with no `evidence.test_command` and no `test_output_path`
- `status` value not in the enumeration
- Empty response or response that does not parse as the expected handoff format

## Cross-references

- Runtime retry/fallback rules: `references/runtime-resilience.md`
- Gate catalog (which gates use which ARC fields): `references/gates-catalog.md`
- Policy file: `plugins/claude-tech-squad/runtime-policy.yaml`
