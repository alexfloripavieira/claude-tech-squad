# CTS Orchestration Contract — canonical include

This is the canonical definition of the CTS hard-requirement orchestration
contract. Every skill that spawns `Agent(...)` MUST embed (or transclude) this
section. Skills that do NOT spawn agents still inherit the **Language Audit**
clause for user-facing output.

## Orchestration Contract — Mandatory Phases (CTS hard requirement)

The lead orchestrator MUST execute the four phases below in order on every
run of this skill. Skipping any phase is a contract violation. The SEP log
MUST record `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`
plus `language_policy_applied: pt-BR`. `scripts/validate.sh` greps each
dev-flow SKILL.md for the phase tags `CTS-PHASE: skill-init`, `CTS-PHASE: agent-spawn`,
`CTS-PHASE: agent-cleanup`, and `CTS-PHASE: skill-finalize` to enforce wiring.

Both invariants below are HARD REQUIREMENTS sourced from
`runtime-policy.yaml`:

- `language_policy.hard_requirement: true` — pt-BR for all natural-language output.
- `agent_worktrees.hard_requirement: true` — per-agent worktree isolation for every spawn.

### Phase A — Skill Branch Init (CTS-PHASE: skill-init)

Run BEFORE any `Agent(...)` call:

```bash
INIT_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/init-skill-branch.sh <skill-name>)
# parse: skill_branch=<...> base_branch=<...> base_commit=<...>
```

- Exit 3 → tree dirty → emit `[Preflight Failed] main worktree dirty` and STOP.
- On success emit `[Skill Branch Created] skill_branch=<...> base_branch=<...> base_commit=<...>`.
- Persist `skill_branch` value for Phases B and D.

### Phase B — Per-Agent Spawn Wrap (CTS-PHASE: agent-spawn)

For EVERY `Agent(...)` invocation in this skill (teammate or inline mode):

```bash
SPAWN_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/spawn-agent-worktree.sh <skill-name> <agent_name> <agent_id>)
# parse: path=<...> branch=<...> base=<...>
```

The Agent spawn `prompt` MUST begin with, in this exact order:

1. `language_policy.spawn_prompt_preamble` — literal text from
   `runtime-policy.yaml::language_policy.spawn_prompt_preamble` (pt-BR mandate).
2. The five worktree fields from
   `runtime-policy.yaml::agent_worktrees.spawn_prompt_inject.fields_appended_to_every_prompt`:
   - `skill_branch: <...>`
   - `worktree_path: <path>`
   - `branch: <branch>`
   - `base_commit: <base>`
   - `instruction: cd into worktree_path before any Read/Edit/Write/Bash. All file operations are scoped to this worktree. Commit your changes inside this worktree if you want them preserved after cleanup — they will be merged back into skill_branch with --no-ff.`
3. The role-specific spawn prompt body that this SKILL.md defines.

Emit `[Worktree Spawned] agent=<...> | path=<...> | branch=<...>`.

### Phase C — Per-Agent Cleanup (CTS-PHASE: agent-cleanup)

Immediately after the Agent returns its `result_contract` (or after the
final retry budget is exhausted, or on skill abort):

```bash
CLEANUP_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <worktree_path>)
```

- Exit 0 → emit `[Worktree Cleanup] agent=<...> | merged=<true|false> | commits_ahead=<n> | branch_deleted=<branch>`.
- Exit 4 → merge conflict → emit `[Worktree Cleanup Conflict]` and open
  `[Gate] Worktree Merge Conflict | [R]esolve / [A]bort`. Worktree and branch
  are preserved until the user resolves.

This phase runs ONCE PER AGENT SPAWN and is non-skippable, even on teammate failure.

### Phase D — Skill Finalize (CTS-PHASE: skill-finalize)

After the last agent finishes, after the SEP log is written, and before
returning control to the user:

```bash
FINAL_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/finalize-skill.sh "$skill_branch")
```

- Exit 0 → emit `[Skill Finalized] skill_branch=<...> | orphan_worktrees=0 | orphan_branches=0`.
- Non-zero → STOP and surface the failing invariant to the user. Do NOT mark the skill complete.

`finalize-skill.sh` does NOT push, merge to base, or delete the skill
branch — that is the user's call.

### Cross-Talk & Language Audit (mandatory checks before SEP write)

- Inspect mailbox: every Required Pair declared in the skill's
  `## Inter-Teammate Cross-Talk Protocol` must have at least one outbound
  `SendMessage`. Empty pair → Teammate Failure with `reason: cross-talk-missing`.
- Required pairs marked as `adversarial_review` are the pt-BR "advogado do
  diabo" role. The paired teammates MUST challenge assumptions, risks,
  alternatives, missing evidence, and trade-offs directly with each other in
  Portuguese before consensus. The SEP log or final report MUST preserve the
  objection, mitigation, and final decision when the challenge changes scope,
  severity, or implementation direction. The role is not arbitrary blocking:
  objections must be evidence-backed and tied to user impact, safety,
  correctness, maintainability, privacy, security, performance, or accessibility.
- The lead's user-facing output (gate prompts, narrative reports, summaries)
  MUST follow `runtime-policy.yaml::language_policy.lead_to_user_preamble` (pt-BR).
  This applies even to skills that do NOT spawn agents.
- SEP log MUST contain:
  - `language_policy_applied: pt-BR`
  - `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`
  - `worktrees: [...]` (one entry per agent spawn with `path`, `branch`, `commits_ahead`, `merged`, `final_status`)

## Skills without Agent spawns

Skills that do NOT call `Agent(...)` (e.g. dashboard, cost-estimate, from-ticket,
pre-commit-lint, resume-from-rollover) still MUST:

- Apply `language_policy.lead_to_user_preamble` to ALL user-facing output.
- Record `language_policy_applied: pt-BR` in any SEP/audit artifact they write.

Phases A–D are not required when no `Agent(...)` is spawned.
