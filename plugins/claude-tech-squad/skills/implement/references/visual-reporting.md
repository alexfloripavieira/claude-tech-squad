# Visual Reporting Contract — `/implement`

Detailed rendering rules for teammate cards and pipeline board. The SKILL.md keeps the section header and a short summary; this file holds the full contract.

## Teammate cards

- After every teammate returns, pipe its `result_contract.metrics` JSON to `${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh` and print the card inline.
- Respect `observability.teammate_cards.format` from `runtime-policy.yaml`:
  - `ascii` — full ASCII card
  - `compact` — single-line summary
  - `silent` — suppress card output (still log to SEP)

Input schema matches `scripts/test-fixtures/teammate-card-input.json`.

## Pipeline board

- Immediately before writing the SEP log, assemble the pipeline summary JSON (schema identical to `scripts/test-fixtures/pipeline-board-input.json`) and pipe to `${CLAUDE_PLUGIN_ROOT}/scripts/render-pipeline-board.sh`.
- Respect `observability.pipeline_board.enabled`. When disabled, skip rendering but still emit the JSON to the SEP log.

## Failure handling

- Renderer failures are non-fatal: log a `WARNING` entry in the SEP log under `visual_reporting_warnings` and continue.
- Never block a gate on a renderer failure.

## Cross-references

- Render scripts: `${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh`, `render-pipeline-board.sh`
- Policy keys: `runtime-policy.yaml.observability.teammate_cards`, `observability.pipeline_board`
- ARC fields consumed: `result_contract.metrics`
