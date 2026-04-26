# Visual Reporting Contract — Full Detail

- After every teammate returns, pipe its Result Contract `metrics` JSON to `${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh` and print the card inline. Respect `observability.teammate_cards.format` (ascii | compact | silent) from `runtime-policy.yaml`.
- Immediately before writing the SEP log, assemble the pipeline summary JSON (schema identical to `scripts/test-fixtures/pipeline-board-input.json`) and pipe to `${CLAUDE_PLUGIN_ROOT}/scripts/render-pipeline-board.sh`. Respect `observability.pipeline_board.enabled`.
- Renderer failures are non-fatal: log a WARNING in the SEP log and continue.
