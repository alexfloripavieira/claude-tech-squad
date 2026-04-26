---
name: resume-from-rollover
description: This skill should be used when resuming a long-running workflow from a rollover handoff artifact, restoring invariants and returning control to the original skill. Trigger with "/resume-from-rollover <run_id>", "resumir rollover", "retomar run". NOT for creating the rollover artifact in the first place (use /rollover).
user-invocable: true
---

# /resume-from-rollover — Resume From Rollover Handoff

## Global Safety Contract

**This contract applies to this workflow. Violating it requires explicit written user confirmation.**

No operation may, under any circumstances:
- Modify or delete the rollover artifacts being read — they are audit trail
- Silently skip any invariant declared in the handoff JSON — invariants must be re-emitted and acknowledged
- Resume past the `next_action` declared in the handoff without operator confirmation
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Resume a run whose invariants conflict with the current repository state — stop and surface the conflict

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Reconstructs a run's state from a rollover handoff artifact and gives control back to the originating skill. This is a **zero-teammate** skill — the orchestrator reads artifacts, re-establishes context, confirms with the operator, and then re-enters the originating skill at its documented resume point.

See `docs/architecture/0001-context-rollover.md` for the decision record.

## When to Use

- After `/rollover` followed by `/clear` — this is the canonical resume path.
- After an unplanned session loss (crash, disconnect) if a `rollover-<run_id>.json` exists.
- After a hard `[Gate] Context Rollover Required` was accepted with `R`.

**Do not use** if no rollover artifact exists for the run. Use `squad-cli checkpoint resume` directly in that case.

## Execution

### Step 1 — Accept the run_id

The operator must pass `<run_id>` as an argument. If missing, list the most recent rollover artifacts and ask:

```bash
ls -t ai-docs/.squad-log/rollover-*.json | head -5
```

Do not guess. If multiple rollovers exist for the same run_id, use the most recent by file mtime, but name the choice to the operator.

### Step 2 — Load the handoff artifacts

Read both artifacts:

- `ai-docs/.squad-log/rollover-<run_id>.json`
- `ai-docs/.squad-log/rollover-<run_id>-brief.md`

Validate the JSON:

- `schema_version` is `1.0` (or later with backward-compatible reader)
- Required keys present: `run_id`, `skill`, `completed_phases`, `open_decisions`, `invariants`, `next_action`, `checkpoint_cursor`
- `run_id` inside the JSON matches the operator's argument

If validation fails, stop and emit:

```
[Resume Error] Rollover artifact invalid for run=<run_id>.
Path: ai-docs/.squad-log/rollover-<run_id>.json
Reason: <schema-violation-detail>
```

Do not attempt to repair the artifact.

### Step 3 — Load the checkpoint

If `checkpoint_cursor` is non-null, restore it:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli checkpoint resume \
  --skill <skill-from-json> \
  --state-dir .squad-state
```

If `squad-cli` is unavailable and `checkpoint_cursor` is `"sep-log:<path>"`, fall back to reading that SEP log.

### Step 4 — Re-emit the invariants

Print the preflight line using the invariants from the JSON exactly:

```
[Preflight Passed] <skill> | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>
[Resume From] <skill> | checkpoint=<cursor> | rollover=<run_id>
```

### Step 5 — Print the handoff brief

Print the contents of `rollover-<run_id>-brief.md` inline. This gives the operator a chance to review state before any teammate is spawned.

### Step 6 — Open decisions gate

If `open_decisions` in the JSON is non-empty, stop and open a gate for each unresolved item:

```
[Gate] Rollover Open Decision | id=<id> | description=<short>
Waiting for operator resolution (options: accept-current-state | override | abort).
```

Do not resume past this gate without an explicit resolution. Resolutions are appended to the SEP log as `[Decision Resolved] id=<id> | choice=<...>`.

### Step 7 — Confirm the next action

Ask the operator:

```
Resume <skill> at next_action.type=<type>, target=<target>?
  y — proceed
  n — abort, do not resume
  modify — let the operator override the next action
```

Do not proceed on silence. On `y`, re-enter the originating skill at the named next action. On `modify`, accept a replacement next action from the operator, log it as `[Next Action Overridden]`, and resume from there. On `n`, emit `[Resume Declined]` and stop.

### Step 8 — Hand control back

Emit:

```
[Resume Accepted] run=<run_id> | skill=<skill> | next=<next_action.target>
```

Then invoke the named next action. For `next_action.type=spawn_teammate`, spawn the target teammate. For `open_gate`, open the named gate. For `run_command`, execute it under the usual safety contract.

From this point, the originating skill owns the run again. This skill exits.

## Result Contract

```yaml
result_contract:
  status: completed | needs_input | blocked | failed
  confidence: high | medium | low
  blockers: []
  artifacts: []
  findings: []
  next_action: "handed back to <skill>"
```

## Failure Modes

- **Handoff JSON missing** — operator invoked this skill without a prior `/rollover`. Instruct to use `squad-cli checkpoint resume` directly or start over.
- **Invariants conflict with current repo state** — the repository has changed between rollover and resume in a way that violates a locked invariant (e.g. `architecture_style=hexagonal` but the hexagonal scaffold was reverted). Stop with `[Gate] Invariant Conflict`. Do not force resume.
- **Checkpoint file missing but JSON intact** — resume is still possible but with lower fidelity. Emit `[Resume Warning] checkpoint_missing` and proceed only after operator confirmation.
- **Operator aborts with `n`** — exit cleanly, leave artifacts in place for later inspection. Do not delete them.

## Observability

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-resume-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: resume-from-rollover
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: {{invariant_architecture_style}}
checkpoints: [artifacts-loaded, invariants-reemitted, operator-confirmed, control-handed-back]
fallbacks_invoked: []
rollover_run_id: {{run_id}}
handoff_brief_path: {{brief_path}}
handoff_state_path: {{state_path}}
invariants_reemitted: {{count}}
open_decisions_resolved: {{count}}
next_action_type: {{type}}
next_action_target: {{target}}
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Outcome
Run {{run_id}} resumed from rollover artifact. Control handed back to {{skill}} at {{next_action_target}}.
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

## Relationship to Other Skills

- **Upstream:** `/rollover` produces the artifacts this skill consumes.
- **Downstream:** any long-running skill (`/squad`, `/implement`, `/hotfix`, `/refactor`, `/multi-service`) can be the resume target.
- **Complement:** `squad-cli checkpoint resume` is used under the hood in step 3.
