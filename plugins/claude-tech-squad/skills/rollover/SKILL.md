---
name: rollover
description: This skill should be used when an in-flight run needs proactive context rollover before the context window becomes a problem, producing a handoff brief, machine state, and resume command. Trigger with "/rollover", "rollover now", "fazer rollover", "consolidar contexto", "preparar para /clear". NOT for resuming an existing rollover artifact (use /resume-from-rollover).
user-invocable: true
---

# /rollover — Proactive Context Rollover

## Global Safety Contract

**This contract applies to this workflow. Violating it requires explicit written user confirmation.**

No operation may, under any circumstances:
- Delete or overwrite SEP log files — logs are audit trails, treat them as read-only
- Discard the previous run's checkpoint state without confirming the new rollover artifact is persisted
- Execute `/clear` on behalf of the operator — that is an operator action only
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Consolidates the current run's state into three artifacts and prepares the operator to run `/clear` and resume cleanly. This is a **single-agent** skill — one teammate (`context-summarizer`) is spawned, no code is written, and no workflow phase is skipped.

See `docs/architecture/0001-context-rollover.md` for the decision record.

## When to Use

- Before a planned break (lunch, end of day) in the middle of a long run.
- When `[Context Advisory]` has been emitted and the operator wants to rollover before the hard gate fires.
- When output quality appears to be degrading even though no gate has fired.
- After a large phase completes and the next phase is expected to be expensive.
- When the user says: "rollover now", "fazer rollover", "consolidar contexto", "preparar para /clear".

**Do not use** if a teammate is currently running. Wait for `[Teammate Done]` or `[Phase Done]` first. Rollover between teammates is safe; rollover mid-teammate loses work.

## Execution

The orchestrator drives the skill directly and spawns one teammate.

### Step 1 — Resolve the active run

Read `ai-docs/.squad-log/` for the most recent SEP log with an in-progress status, or accept an explicit `<run_id>` argument from the operator.

If no active run is found, stop and inform the operator:

```
[Rollover Error] No active run detected in ai-docs/.squad-log/.
Pass run_id explicitly: /rollover <run_id>
```

Emit: `[Rollover Requested] run=<run_id> | reason=operator_requested`

### Step 2 — Snapshot the checkpoint

Save a checkpoint with cursor `rollover-pending` so the summarizer sees a consistent state:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli checkpoint save \
  --run-id <run_id> \
  --cursor rollover-pending \
  --state-dir .squad-state
```

If `squad-cli` is unavailable, emit `[Checkpoint Saved] rollover | cursor=rollover-pending` manually and record which SEP log file represents the current state.

Emit: `[Checkpoint Saved] rollover | cursor=rollover-pending`

### Step 3 — Spawn the summarizer

Spawn `context-summarizer` as a teammate, not an inline subagent, so the operator sees it:

```
TeamCreate if no active team
Agent with subagent_type=claude-tech-squad:context-summarizer, team_name=<current>, name=summarizer
```

Prompt the teammate with:

- `run_id` — the active run identifier
- `skill` — the skill currently executing (e.g. `/squad`, `/implement`)
- Path to the run's SEP log(s)
- Path to the checkpoint state directory
- Paths to any phase output artifacts already produced
- Reason: `operator_requested`

Emit: `[Teammate Spawned] context-summarizer | pane: summarizer`

### Step 4 — Validate summarizer output

The summarizer returns a `result_contract` listing three artifacts. Before declaring success, verify:

1. `ai-docs/.squad-log/rollover-<run_id>-brief.md` exists and is non-empty.
2. `ai-docs/.squad-log/rollover-<run_id>.json` exists, parses as JSON, and contains required top-level keys: `schema_version`, `run_id`, `completed_phases`, `open_decisions`, `invariants`, `next_action`, `checkpoint_cursor`.
3. The summarizer's `verification_checklist.confidence_after_verification` is `high` or `medium`. If `low`, surface it to the operator as a warning before proceeding.

If any check fails, emit `[Teammate Retry] context-summarizer | Reason: rollover artifact invalid` and retry once with the compact-prompt fallback per `runtime-policy.yaml`.

### Step 5 — Emit acceptance and operator handoff

Emit: `[Rollover Accepted] run=<run_id> | handoff=ai-docs/.squad-log/rollover-<run_id>-brief.md`

Then print the operator handoff block exactly:

```
==============================================
Rollover prepared for run <run_id>.

Artifacts:
- Handoff brief: ai-docs/.squad-log/rollover-<run_id>-brief.md
- Machine state: ai-docs/.squad-log/rollover-<run_id>.json

To resume cleanly:
  1. Run  /clear
  2. Run  /resume-from-rollover <run_id>

You can safely close this session. All work is persisted.
==============================================
```

Stop. Do not spawn another teammate. Do not attempt `/clear` on the operator's behalf — `/clear` is a CLI command that only the operator can execute.

## Result Contract

```yaml
result_contract:
  status: completed | needs_input | blocked | failed
  confidence: high | medium | low
  blockers: []
  artifacts:
    - ai-docs/.squad-log/rollover-<run_id>-brief.md
    - ai-docs/.squad-log/rollover-<run_id>.json
  findings: []
  next_action: "/resume-from-rollover <run_id>"
```

## Failure Modes

- **Summarizer fails twice** — fall back to the `compact_prompt_fallback` variant declared in `runtime-policy.yaml`. If that also fails, surface `[Gate] Rollover Summarizer Failed` and ask the operator to record the state manually before `/clear`.
- **Active run cannot be identified** — ask the operator for `run_id` explicitly. Do not pick a run heuristically.
- **`squad-cli` missing** — degrade gracefully; record the SEP log path as an informal cursor in the JSON under `checkpoint_cursor: "sep-log:<path>"`.
- **Operator invokes `/rollover` mid-teammate** — stop with `[Rollover Deferred] reason=teammate_running` and instruct the operator to wait for `[Teammate Done]`.

## Observability

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-rollover-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: rollover
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: teammate
architecture_style: n/a
checkpoints: [rollover-pending, summarizer-done, artifacts-validated]
fallbacks_invoked: []
rollover_reason: operator_requested | automatic_hard | automatic_soft_deferred
tokens_at_rollover_approx: {{tokens_cumulative}}
summarizer_model: {{model_id}}
summarizer_duration_ms: {{duration}}
artifact_brief_path: {{brief_path}}
artifact_state_path: {{state_path}}
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Outcome
Rollover artifacts produced for run {{run_id}}. Operator handed off to /clear + /resume-from-rollover.
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

## Cost Note

The summarizer runs on a chat-class model per ADR 0001. Expected cost per rollover: approximately $0.01 at current Haiku-tier pricing for a 100k-token input compressed to a 2k-token brief. If cost exceeds $0.10, the summarizer is misrouted to a reasoning-class model — investigate the teammate configuration.
