# Runtime Resilience Contract — `/discovery`

This file expands the contract referenced from `SKILL.md`. The orchestrator MUST load `${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml` before creating the discovery team. That file is the source of truth for retry budgets, fallback matrix, severity policy, checkpoint/resume rules, and reliability metrics recorded in SEP logs.

If `runtime-policy.yaml` is missing or unreadable: stop the run and surface `[Gate] Runtime Policy Missing`. Do not silently continue with hardcoded defaults.

## Teammate Failure Protocol

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role (including the required `result_contract` block).

For every teammate spawned — without exception:

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - **Doom loop check** — before re-spawning, consult `doom_loop_detection` in `runtime-policy.yaml`. Compare the failed output against the prior attempt. If a doom loop pattern is detected (`growing_diff`, `oscillating_fix`, or `same_error`):
     - Emit: `[Doom Loop Detected] <name> | pattern=<rule_name> | retries=<count>`
     - Skip the retry and go directly to step 3 (fallback) — retrying the same agent will waste tokens.
   - If no doom loop detected: emit `[Teammate Retry] <name> | Reason: silent failure — re-spawning` and re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails (or doom loop was detected in step 2):
   - Read `${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml` and consult `fallback_matrix.discovery.<name>`.
   - If a fallback subagent is listed:
     - Emit: `[Fallback Invoked] <name> -> <fallback-subagent> | Reason: primary failed twice`
     - Spawn the fallback once with the same context and an explicit instruction that it is acting as a surrogate for `<name>`.
     - If the fallback returns valid output, continue and record the event in `fallback_invocations` and `teammate_reliability`.
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

4. **Sequential teammates** (output feeds the next agent): `[S]` degrades ALL downstream teammates that depend on this output — warn the user explicitly before accepting skip.
5. **Parallel batch teammates**: `[S]` on one agent does not block the batch, but the missing output must be logged as a risk in the final report.
6. **Do NOT advance** to the next step until every teammate in the current step has returned valid output, been explicitly skipped, or the run has been aborted.

## Inline Health Check

After every `[Teammate Done]`, run the health check (6 signals). Preferred deterministic path saves ~2K tokens per teammate:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli health \
  --run-id {{feature_slug}} --teammate <name> \
  --tokens-in <N> --tokens-out <N> \
  --status <completed|failed|blocked> --confidence <high|medium|low> \
  --retries <N> --findings-blocking <N> --duration-ms <N> \
  --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml \
  --state-dir .squad-state
```

Returns JSON with `signals_triggered`, `context_enrichment`, `budget_percent`, `is_critical`. Use `context_enrichment` directly as prepended text for the next teammate.

If `squad-cli` is not available: evaluate the 6 signals manually.

- Emit: `[Health Check] <name> | signals: <triggered_signals_or_ok>`
- **warning signals**: prepend context to next teammate
- **critical signals**: emit `[Health Warning]` and surface to user

## Context Rollover Gate

Between every teammate completion and the next teammate spawn, inspect cumulative token usage. Emit `[Token Usage]` at each phase boundary.

- If `used >= 100k`: emit `[Context Advisory]`. Continue, but plan the next teammate as the last before rollover.
- If `used >= 140k`: emit `[Gate] Context Rollover Required` and halt for operator choice `[R|D|F]`:
  - `R` — Rollover now. Spawn `context-summarizer` as a teammate; then halt for `/clear` + `/resume-from-rollover <run_id>`.
  - `D` — Defer one phase. Proceed one more teammate only, then force rollover.
  - `F` — Force continue. Emit `[Rollover Declined]` with operator reason. Degradation risk accepted and logged.

Thresholds and summarizer agent declared in `runtime-policy.yaml` under `context_management`. Checks only at boundaries, never mid-teammate. Rationale: `docs/architecture/0001-context-rollover.md`.

## Checkpoint / Resume Rules — Detail

Discovery checkpoints (in order): `preflight-passed`, `gate-1-approved`, `gate-2-approved`, `gate-3-approved`, `gate-4-approved`, `specialist-bench-complete`, `quality-baseline-complete`, `blueprint-confirmed`.

Preferred path (deterministic, persists to `.squad-state/`):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli checkpoint save \
  --run-id {{feature_slug}} --cursor <checkpoint> --state-dir .squad-state
```

Manual fallback: emit `[Checkpoint Saved] discovery | cursor=<checkpoint>` and track state manually in the run notes.

Resume rule: when re-entering an existing run id, the orchestrator reads the latest cursor and skips all gates strictly before that cursor. Auto-advance is governed by `runtime-policy.yaml.auto_advance.eligible_gates`.
