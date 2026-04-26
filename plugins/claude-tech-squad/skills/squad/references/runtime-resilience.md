# Runtime Resilience Contract — Full Detail

Load `${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml` before repository recon or team creation. This file is the source of truth for:

- retry budgets
- fallback matrix
- severity policy
- checkpoint/resume rules
- reliability metrics recorded in SEP logs

If the runtime policy file is missing or unreadable, stop the run and surface `[Gate] Runtime Policy Missing`. Do not silently continue with hardcoded defaults.

## Operator Visibility lines (full list)

Emit these lines for every teammate action:

- `[Preflight Start] <workflow-name>`
- `[Preflight Warning] <summary>`
- `[Preflight Passed] <workflow-name> | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>`
- `[Team Created] <team-name>`
- `[Phase Start] <phase-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Fallback Invoked] <failed-role> -> <fallback-subagent> | Reason: <summary>`
- `[Resume From] <workflow-name> | checkpoint=<checkpoint>`
- `[Checkpoint Saved] <workflow-name> | cursor=<checkpoint>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`
- `[Phase Done] <phase-name> | Outcome: <summary>`
- `[Token Usage] run=<run_id> | used=<N>k | threshold=100k`
- `[Context Advisory] run=<run_id> | recommend=finish-current-gate-then-rollover`
- `[Gate] Context Rollover Required | run=<run_id> | used=<N>k | options=[R|D|F]`
- `[Rollover Accepted] run=<run_id> | handoff=<artifact-path>`
- `[Rollover Declined] run=<run_id> | reason=<user-text>`

## Teammate Failure Protocol (full)

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role, including the required `result_contract` block.

For every teammate spawned — without exception:

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - **Doom loop check** — before re-spawning, consult `doom_loop_detection` in `runtime-policy.yaml`. Compare the failed output against the prior attempt (if any). If a doom loop pattern is detected (growing_diff, oscillating_fix, or same_error):
     - Emit: `[Doom Loop Detected] <name> | pattern=<rule_name> | retries=<count>`
     - Skip the retry and go directly to step 3 (fallback) — retrying the same agent will waste tokens.
   - If no doom loop detected: Emit `[Teammate Retry] <name> | Reason: silent failure — re-spawning` and re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails (or doom loop was detected in step 2):
   - Read `${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml` and consult `fallback_matrix.squad.<name>`.
   - If a fallback subagent is listed:
     - Emit: `[Fallback Invoked] <name> -> <fallback-subagent> | Reason: primary failed twice`
     - Spawn the fallback once with the same context and an explicit instruction that it is acting as a surrogate for `<name>`.
     - If the fallback returns a valid output, continue and record the event in `fallback_invocations` and `teammate_reliability`.
   - If no fallback exists, or the fallback also fails:
     - Emit: `[Gate] Teammate Failure | <name> failed twice and fallback did not recover`
   - Surface to the user:

```
Teammate <name> failed to return a valid output (attempt 1 and 2).

Options:
- [R] Retry once more with the same prompt
- [S] Skip and continue — downstream quality WILL be degraded (log the risk)
- [X] Abort the run
```

4. **Sequential teammates** (output feeds the next agent): [S] degrades ALL downstream teammates that depend on this output — warn the user explicitly before accepting skip.
5. **Parallel batch teammates**: [S] on one agent does not block the batch, but the missing output must be logged as a risk in the final report.
6. **Do NOT advance to the next step** until every teammate in the current step has returned valid output, been explicitly skipped, or the run has been aborted.

## Inline Health Check

After every `[Teammate Done]`, run the health check. This evaluates 6 signals: retry_detected, fallback_used, doom_loop_short_circuit, token_budget_pressure, low_confidence_chain, blocking_findings_accumulating.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli health \
  --run-id {{feature_slug}} --teammate <name> \
  --tokens-in <N> --tokens-out <N> \
  --status <completed|failed|blocked> --confidence <high|medium|low> \
  --retries <N> --findings-blocking <N> --duration-ms <N> \
  --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml \
  --state-dir .squad-state
```

The returned JSON contains `signals_triggered`, `context_enrichment` (text to prepend to the next teammate's prompt), `budget_percent`, and `is_critical`. Use the `context_enrichment` text directly.

If `squad-cli` is not available: evaluate the 6 signals manually from the teammate's `result_contract` and execution metadata.

- Emit: `[Health Check] <name> | signals: <triggered_signals_or_ok>`
- **warning signals**: prepend context enrichment to next teammate's prompt
- **critical signals**: emit `[Health Warning]` and surface to user if action is needed

**Cross-phase health:** In `/squad`, health signals from the discovery phase are carried into the implementation phase. If discovery had retries or low confidence, the implementation phase starts with that context already enriched.

## Context Rollover Gate

Between every `[Phase Done]` and the next `[Phase Start]`, inspect cumulative token usage for the run. Emit `[Token Usage]` every phase boundary.

- If `used >= 100k`: emit `[Context Advisory]`. The run continues, but the advisory signals that the next phase should be the last before a rollover.
- If `used >= 140k`: emit `[Gate] Context Rollover Required` and halt. The operator must choose:
  - `R` — Rollover now. Spawn `context-summarizer` as a teammate, then halt for `/clear` plus `/resume-from-rollover <run_id>`.
  - `D` — Defer one phase. Proceed only with the next phase; force rollover immediately after.
  - `F` — Force continue. Emit `[Rollover Declined]` with the operator reason. Degradation risk is accepted and logged.

Threshold constants and the summarizer agent are declared in `runtime-policy.yaml` under `context_management`. Checks fire only at phase boundaries, never mid-phase. Rationale and alternatives: `docs/architecture/0001-context-rollover.md`.
