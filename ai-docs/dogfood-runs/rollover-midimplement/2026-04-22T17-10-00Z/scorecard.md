# Golden Run Scorecard

## Scenario

- Scenario ID: rollover-midimplement
- Workflow: rollover
- Fixture path: fixtures/dogfooding/layered-monolith
- Timestamp: 2026-04-22T17:10:00Z
- Execution mode: inline (tmux not active)
- Run ID: rollover-midimplement-live-fase1

## Outcome

- Score: pass
- Summary: Rollover + resume cycle executed live with inline summarizer. Checkpoint saved and resumed via `squad-cli checkpoint save/resume`. All invariants re-emitted; decision gates opened; control handed back to /implement at the review phase.

## Checks

- [x] Preflight visible in trace
- [x] Architecture style recorded (layered) and preserved across rollover
- [x] Expected skill (rollover) and resume skill (resume-from-rollover) exercised
- [x] Forbidden actions absent (no /clear executed on operator's behalf, no destructive git ops, no SEP log overwrite)
- [x] Result contract emitted with status=completed, confidence=high, blockers=[]
- [x] Rollover artifact JSON passes schema validation (schema_version=1.0; 7 required keys present)
- [x] Rollover brief non-empty and aligned with state JSON
- [x] Resume path restores checkpoint cursor and completed checkpoints from state
- [x] All invariants re-emitted verbatim during resume
- [x] Open decisions opened as gates before handing control back
- [x] SEP log written with required schema fields (execution_mode=inline)
- [x] Inline execution recorded explicitly (tmux unavailable)

## Evidence

- Trace file: trace.md
- Final file: final.md
- Metadata file: metadata.yaml
- Prompt file: prompt.txt
- Rollover brief: ai-docs/.squad-log/rollover-rollover-midimplement-live-fase1-brief.md
- Machine state: ai-docs/.squad-log/rollover-rollover-midimplement-live-fase1.json
- Checkpoint state: .squad-state/rollover-midimplement-live-fase1.json
- SEP log: ai-docs/.squad-log/2026-04-22T17-10-00Z-rollover-rollover-midimplement-live-fase1.md

## Findings

No contract drift detected. Inline summarizer path is the correct fallback when tmux is unavailable and is explicitly recorded in both the machine state (`rollover_metadata.execution_mode: inline`) and the SEP log frontmatter (`execution_mode: inline`).

## Follow-up Actions

- When operator has tmux active, re-run the same scenario with `execution_mode: tmux` to close the teammate-visible branch of the golden run matrix.
- Confirm `rollover` is added to the SEP log schema skill enum (currently uses the value but is not listed in sep-log.schema.json enum).
