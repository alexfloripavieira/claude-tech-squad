# Context Rollover

Long runs of `/squad`, `/implement`, `/hotfix`, `/refactor`, and `/multi-service`
accumulate tokens across many specialist teammates. Past roughly 100k cumulative
tokens, Claude Code's output quality starts degrading. Past 140k, degradation
becomes severe. **Context rollover** is the plugin's mechanism to consolidate
state, clear the session, and resume without losing decisions, pending work, or
locked invariants.

Rollover is an explicit operator gate, not a silent automatic behavior. You
always see it happen.

Formal decision record: `docs/architecture/0001-context-rollover.md`.

---

## The short version

- At **100k tokens** the orchestrator emits `[Context Advisory]`. Keep going,
  but plan to rollover after the current phase.
- At **140k tokens** the orchestrator emits `[Gate] Context Rollover Required`
  and halts. You pick `R`, `D`, or `F`.
- You can also rollover at any time with `/rollover` (proactive), regardless of
  token count.
- After rollover: run `/clear`, then `/resume-from-rollover <run_id>`.

---

## How the gate works

Between every phase boundary, long-running skills emit:

```
[Token Usage] run=<run_id> | used=<N>k | threshold=100k
```

If `N >= 100`:

```
[Context Advisory] run=<run_id> | recommend=finish-current-gate-then-rollover
```

The run keeps going. No action required. Treat this as your two-minute warning.

If `N >= 140`, the run halts:

```
[Gate] Context Rollover Required | run=<run_id> | used=<N>k | options=[R|D|F]
```

Your choices:

| Option | Meaning                       | When to use                                                              |
|--------|-------------------------------|--------------------------------------------------------------------------|
| `R`    | Rollover now                  | Default. Safe. Costs about a dollar's worth of summariser time.          |
| `D`    | Defer one phase               | Next phase is trivially short (release sign-off, a single confirmation). |
| `F`    | Force continue (accept risk)  | You're 95% done and the final phase is about to write an output artifact. |

`F` is logged with your free-text reason and shows up in post-mortems. Use it
deliberately, not out of habit.

---

## Proactive rollover (`/rollover`)

You don't have to wait for the gate. Invoke `/rollover` whenever:

- You're about to take a break and want a clean resume point.
- The next phase is expensive and you want headroom.
- You suspect output quality has started slipping but no gate has fired.
- You're operating in a shared session and want to snapshot state before
  handing off to another operator.

Rollover takes one summariser call (chat-class model, ~5 seconds) and writes
three artifacts. See below.

---

## What rollover produces

Three artifacts, all under `ai-docs/.squad-log/`:

1. **Handoff brief** — `rollover-<run_id>-brief.md`. Human-readable. ≤ 2000
   tokens. Lists completed phases, open decisions, locked invariants, and the
   next action.
2. **Machine state** — `rollover-<run_id>.json`. Structured. Consumed by
   `/resume-from-rollover`. Schema v1.0. See the agent file for the full
   schema.
3. **Resume command** — a one-line string: `/resume-from-rollover <run_id>`.
   Printed to the terminal; copy-paste into the next session.

---

## Resuming (`/resume-from-rollover <run_id>`)

After rollover:

1. Run `/clear` to drop the current session's context.
2. Run `/resume-from-rollover <run_id>`.

The resume skill:

1. Loads the machine state JSON.
2. Loads the checkpoint (via `squad-cli checkpoint resume` or the SEP log
   fallback).
3. Re-emits the preflight invariants so the new session picks up the locked
   architecture style, lint profile, execution mode, and test strategy
   without re-deriving them.
4. Prints the handoff brief inline so you can review state before anything
   runs.
5. Opens gates for any unresolved open decisions the summariser flagged.
6. Confirms the next action with you, then hands control back to the
   originating skill.

If invariants have drifted between rollover and resume (e.g. the repository
state no longer matches the architecture style locked at preflight), resume
stops with `[Gate] Invariant Conflict`. Do not force-resume past that gate —
investigate.

---

## Cost

A rollover costs roughly **$0.01** per invocation at current Haiku-tier
pricing: ~100k input tokens compressed to ~2k output tokens. Budgeted in
`runtime-policy.yaml` under `context_management.cost_budget_usd_per_rollover:
0.10` — if a rollover costs more than 10 cents, the summariser has been
misrouted to a reasoning-class model and that's a configuration bug.

---

## What rollover does *not* do

- It does not run `/clear` for you. `/clear` is a CLI command; only you can
  invoke it.
- It does not compact the native Claude Code context window. It produces an
  artifact you resume from after `/clear`.
- It does not resolve open decisions. It surfaces them. You resolve.
- It does not re-execute phases. Completed work stays completed. Resume
  continues from the named next action.
- It does not fire mid-teammate. If a teammate is running, rollover is
  deferred to the next phase boundary.

---

## Observability

Every rollover writes one SEP log entry:

```
ai-docs/.squad-log/<timestamp>-rollover-<run_id>.md
```

Every resume writes one:

```
ai-docs/.squad-log/<timestamp>-resume-<run_id>.md
```

These feed the normal dashboard (`/dashboard`) and post-mortem
(`/incident-postmortem`) flows.

---

## Configuration

All thresholds and agent bindings live under `context_management:` in
`plugins/claude-tech-squad/runtime-policy.yaml`:

```yaml
context_management:
  enabled: true
  advisory_threshold_tokens: 100000
  hard_rollover_threshold_tokens: 140000
  summarizer_agent: context-summarizer
  summarizer_model_class: chat
  summarizer_model_preference:
    - claude-haiku-4-5
    - groq/llama-3.3-70b-versatile
    - gpt-4o-mini
  rollover_gate_options:
    R: rollover-now
    D: defer-one-phase
    F: force-continue-with-risk
```

Thresholds are heuristics — Claude Code's token counting is approximate. The
100k/140k band has ~40k headroom which is wide enough to finish one phase
safely between advisory and hard gate.

---

## Troubleshooting

**"Rollover was triggered at the wrong moment."**
Rollover only fires at phase boundaries. If it fired inside a teammate, that
teammate violated the contract — file it.

**"I lost the handoff artifact."**
Check `ai-docs/.squad-log/rollover-<run_id>-brief.md` and
`rollover-<run_id>.json`. They are not deleted by `/clear`. If both are
genuinely gone, fall back to `squad-cli checkpoint resume` for partial
recovery.

**"Resume says invariant conflict."**
The repo changed between rollover and resume in a way that violates a locked
invariant (architecture style, lint profile, etc.). Don't force it. Either
reconcile the repo state manually or start a fresh run.

**"I invoked `/rollover` but no run is active."**
Pass an explicit `run_id`: `/rollover <run_id>`. The skill doesn't guess.

**"The summariser costs $0.50, not $0.01."**
Check `context_management.summarizer_model_class` — it should be `chat`. If
it's `reasoning`, fix the policy.

---

## Related

- ADR: `docs/architecture/0001-context-rollover.md`
- Runtime policy: `docs/RUNTIME-POLICY.md`
- Safety contract: `docs/SAFETY.md`
- Operator playbook: `docs/OPERATIONAL-PLAYBOOK.md`
