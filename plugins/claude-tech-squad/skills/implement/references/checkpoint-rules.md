# Checkpoint / Resume Rules — `/implement`

Detailed checkpoint flow. The SKILL.md keeps the canonical header `### Checkpoint / Resume Rules` and a short summary; this file enumerates each checkpoint and the resume contract.

## Checkpoint sequence

In order of emission:

1. `preflight-passed`
2. `commands-confirmed`
3. `blueprint-validated`
4. `tasks-produced`
5. `work-items-produced`
6. `tdd-ready`
7. `implementation-batch-complete`
8. `reviewer-approved`
9. `qa-pass`
10. `conformance-pass`
11. `quality-bench-cleared`
12. `coderabbit-clean`
13. `docs-complete`
14. `uat-approved`

## Save mechanism

Preferred: `python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli checkpoint`.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli checkpoint save \
  --run-id {{feature_slug}} --cursor <checkpoint> \
  --state-dir .squad-state
```

Fallback (squad-cli unavailable): emit `[Checkpoint Saved] implement | cursor=<checkpoint>` and persist run state under `.squad-state/{{feature_slug}}/checkpoints.json` manually.

## Resume rule

On a fresh `/implement` invocation matching an existing `feature_slug`, `squad-cli preflight` returns `resume_from: <checkpoint>`. The orchestrator emits `[Resume From] implement | checkpoint=<checkpoint>` and skips ahead to the step immediately after the checkpoint, replaying digests from already-captured agent outputs.

## State directory layout

```
.squad-state/
  {{feature_slug}}/
    checkpoints.json          # current cursor + history
    teammate-outputs/         # captured agent outputs (one file per teammate)
    digests/                  # pre-computed Progressive Disclosure digests
    health/                   # inline health-check JSON per phase
```

## Cross-references

- Resume command: `/claude-tech-squad:resume-from-rollover`
- Policy: `runtime-policy.yaml.checkpoint_resume`
- Preflight: `squad-cli preflight` returns `resume_from`
