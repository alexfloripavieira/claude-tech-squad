# Visual Reporting Contract — `/discovery`

## Teammate Cards

After every teammate returns, pipe its Result Contract `metrics` JSON to:

```
${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh
```

Print the rendered card inline in the orchestrator output. Respect `observability.teammate_cards.format` (`ascii | compact | silent`) from `runtime-policy.yaml`.

## Pipeline Board

Immediately before writing the SEP log (Step 13c), assemble the pipeline summary JSON (schema identical to `scripts/test-fixtures/pipeline-board-input.json`) and pipe it to:

```
${CLAUDE_PLUGIN_ROOT}/scripts/render-pipeline-board.sh
```

Respect `observability.pipeline_board.enabled`.

## Failure Handling

Renderer failures are non-fatal: log a WARNING in the SEP log and continue. Do not abort the run because the visualization step failed.

## Operator Visibility Lines

The orchestrator MUST emit these lines for every teammate action:

- `[Preflight Start] <workflow-name>`
- `[Preflight Warning] <summary>`
- `[Preflight Passed] <workflow-name> | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`
- `[Team Created] <team-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Fallback Invoked] <failed-role> -> <fallback-subagent> | Reason: <summary>`
- `[Resume From] <workflow-name> | checkpoint=<checkpoint>`
- `[Checkpoint Saved] <workflow-name> | cursor=<checkpoint>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`
- `[Batch Completed] <phase> | N/N agents returned`

These lines are the ground-truth signal for `/dashboard` and `/factory-retrospective` parsers.
