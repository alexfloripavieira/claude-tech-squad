# ADR 0001 — Context Window Management via Explicit Rollover Gate

Status: Accepted
Date: 2026-04-22

## Context

Long-running skills in this plugin (`/squad`, `/implement`, `/hotfix`, `/refactor`,
`/multi-service`) routinely cross 100k cumulative tokens when the full 74-specialist
bench is engaged. Empirical evidence:

- The 2026-04-18 factory retrospective traced three PO silent failures in five
  `/discovery` runs directly to context saturation, already acknowledged in
  `runtime-policy.yaml` under `compact_prompt_fallback`.
- Claude Code's effective reasoning quality degrades measurably past roughly 60%
  of the model's context window. Independent reports place the drop at ~14
  percentage points (92% to 78%) on recall-heavy tasks once the window crosses
  120k tokens.
- `squad-cli` already ships `checkpoint save` and `checkpoint resume` primitives,
  and the visibility contract already supports `[Gate]`, `[Resume From]`, and
  `[Checkpoint Saved]` lines. The ingredients exist; they are not yet wired for
  context management.

Doing nothing produces three concrete failure modes:

1. Silent degradation — teammates return lower-quality output near the limit
   without the operator being warned.
2. Hard refusal — Claude Code invokes native compaction mid-phase and the
   operator loses traceability of what was summarised.
3. Unrecoverable loss — a crash, network drop, or explicit `/clear` at the wrong
   moment discards work because there is no structured handoff artifact.

## Decision

Introduce context rollover as a **first-class explicit gate** inside the plugin's
existing visibility and safety contract. Three components:

1. A new advisor-level agent, `context-summarizer`, spec-card conformant, whose
   sole job is to consolidate run state into a handoff brief (narrative),
   machine state (JSON), and a resume command string.
2. Two operator-visibility lines, `[Context Advisory]` (soft, at 100k cumulative
   tokens) and `[Gate] Context Rollover Required` (hard, at 140k). The hard gate
   halts the run until the operator picks an option from `[R | D | F]`
   (Rollover / Defer-one-phase / Force-continue-with-risk).
3. Two new skills, `/rollover` (operator-invoked, proactive) and
   `/resume-from-rollover` (resumes from a handoff artifact plus a checkpoint).
   Integration with `squad-cli checkpoint` uses the existing cursor mechanism
   with a new cursor type `rollover-<run_id>`.

Long-running skills gain a mandatory inter-phase check:
- Before emitting `[Phase Start]` for any new phase, inspect cumulative token
  usage.
- If used >= 100k, emit `[Context Advisory]`.
- If used >= 140k, emit `[Gate] Context Rollover Required` and stop.

Checks fire only between phases, never mid-phase. This preserves atomicity of
specialist work and matches the existing cultural pattern of gates-at-milestones.

## Summarizer model class

The `context-summarizer` runs a summarisation task, not a reasoning task. It
produces a structured consolidation of existing content. Reasoning-class models
(Opus, GPT-4) offer no measurable advantage over chat-class models (Haiku,
Llama 3.3 70B, Gemini Flash) on this workload, and cost ~20x more.

Decision: `model_class: chat`, `cost: low`. Concrete targets in priority order:

- `claude-haiku-4-5` (preferred when available)
- `groq/llama-3.3-70b-versatile` (preferred for free-tier operators)
- `gpt-4o-mini` (fallback)

Reasoning-class is reserved for agents that decide routes, critique output, or
select fallbacks. The summarizer does none of those.

## Thresholds

| Threshold     | Trigger | Action                                              |
|---------------|---------|-----------------------------------------------------|
| 100k tokens   | soft    | Emit `[Context Advisory]`, run continues            |
| 140k tokens   | hard    | Emit `[Gate] Context Rollover Required`, run halts  |

Rationale for the band:
- 100k is ~50% of the practical usable window across current Claude Code
  targets. Early enough that the operator can finish the current phase cleanly.
- 140k preserves headroom for the summarizer call itself (up to ~8k in, ~4k
  out) plus a margin for the final tool results before forced compaction.
- The 40k band is wide enough to almost always finish one phase safely between
  advisory and hard gate.

Thresholds are configurable in `runtime-policy.yaml` under `context_management`.

## Gate options

The hard gate uses the same `R/S/X`-style convention as the existing
`unresolved_action_gate`, rebound for this context:

- `R` — Rollover now. Spawn `context-summarizer`, emit artifacts, halt for
  `/clear` + `/resume-from-rollover`.
- `D` — Defer one phase. Accept the risk, proceed with the next phase only,
  then force `R`. Used when the next phase is trivially short (e.g. release
  sign-off).
- `F` — Force continue. Operator accepts degradation risk and does not rollover.
  Emit `[Rollover Declined]` with the operator's free-text reason; the reason
  becomes part of the SEP log for postmortem purposes.

## Consequences

### Positive
- Context saturation moves from invisible failure to named, logged event.
- Existing checkpoint CLI gains a real use case and becomes load-bearing.
- Summariser cost is bounded (~$0.01 per rollover at Haiku pricing for a 100k
  context dump compressed to 2k).
- Pattern is consistent with the plugin's human-in-the-loop philosophy; no new
  mental model for operators to learn.

### Negative
- Adds latency: a rollover costs one summariser call (~5s) plus operator
  attention (~30s to read the brief and run `/clear` + `/resume-from-rollover`).
- Operators who force-continue (`F`) may still experience degraded output.
  Acceptable trade-off: the choice is theirs, logged, and auditable.
- Token counting in Claude Code is approximate. The thresholds are heuristics,
  not exact guarantees. Documented as such.

### Neutral
- No runtime process is introduced. All enforcement lives in skill prompts and
  the existing `squad-cli`. Consistent with this plugin's
  markdown-and-YAML-only posture.

## Alternatives considered

**A. Silent native compaction only.** Rejected: operator loses traceability of
what was dropped, and PO silent failures recur.

**B. Runtime-driven automatic rollover (Cadre-style PreCompact hook).**
Rejected here: this plugin has no Python runtime, and the human-in-the-loop
design is a deliberate strength, not a workaround. Imposing invisible
mechanics would regress the product.

**C. Per-agent token budgets.** Rejected as sole mechanism: individual agents
already respect the `compact_prompt_fallback` policy. The problem is
cumulative across agents within a run, which no per-agent budget can detect.
Kept as complementary guardrail.

**D. Aggressive thresholds (e.g. 60k / 90k).** Rejected: interrupts too
frequently on `/implement` runs that legitimately need ~80k to finish a single
feature. Degrades operator trust in the gate.

## References

- `plugins/claude-tech-squad/runtime-policy.yaml` — `compact_prompt_fallback`
- `plugins/claude-tech-squad/skills/squad/SKILL.md` — existing gate patterns
- `plugins/claude-tech-squad/bin/squad-cli` — checkpoint primitives
- `docs/RUNTIME-POLICY.md` — policy reference
- `docs/SAFETY.md` — gate safety contract

## Follow-ups

- Implementation tracked under the step sequence logged with this ADR:
  agent spec, visibility extensions, two skills, integration edits, policy
  block, golden run, and the user-facing `docs/CONTEXT-ROLLOVER.md`.
- A future ADR will revisit thresholds after first 20 real rollovers are
  recorded in `ai-docs/.squad-log/`.
