---
name: refactor
description: This skill should be used when improving existing code structure safely through characterization tests, incremental refactoring steps, and continuous behavior verification. Trigger with "refatorar", "refactor", "limpar código", "remover débito técnico", "reorganizar", "melhorar design". NOT for greenfield implementation (use /implement) or isolated bug fixes (use /bug-fix).
user-invocable: true
---

# /refactor — Safe Incremental Refactoring

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Change observable behavior during a refactor — if behavior must change, escalate to `/squad`
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in any environment
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Remove public API surface (methods, endpoints, exported symbols) without verifying zero callers first
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Proceed with the next refactor step after a test failure — stop and present [F]ix / [S]kip / [A]bort

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Test-guarded refactoring workflow. Prevents big-bang refactors that break behavior silently — every change is backed by tests that prove behavior is preserved.

**Core rule:** Behavior does not change. If the refactor requires a behavior change, that is a feature — use `/squad` instead.

## When to Use

- Cleaning up technical debt without changing external behavior
- Extracting shared logic, renaming for clarity, restructuring modules
- Reducing coupling or improving testability
- When the user says: "refatorar", "refactor", "limpar código", "remover débito técnico", "reorganizar", "melhorar design"

**Escalate to `/squad` if:**
- The refactor requires a behavior change
- The scope touches more than 15 files
- The refactor involves changing a public API contract

## Operator Visibility Contract

Emit these trace lines so the operator can follow the test-guarded refactor and the SEP log can capture state transitions:

- `[Preflight Start] refactor`
- `[Stack Detected] <stack> | impl=<agent> | reviewer=<agent>`
- `[Refactor Plan Confirmed] <N> steps | <total_files> files`
- `[Characterization Tests Locked] <test_command> | <N> tests passing`
- `[Refactor Step <N>/<total>] <description> — PASS` (after each green step)
- `[Refactor Step <N>/<total>] <description> — FAIL — reverting` (rollback path)
- `[Quality Bench] code-quality=<status> | reviewer=<status>`
- `[Team Created] refactor-team`
- `[Team Deleted] refactor-team | cleanup complete` (or `[Team Cleanup Warning]` on failure)
- `[SEP Log Written] ai-docs/.squad-log/<filename>`

## Inter-Teammate Cross-Talk Protocol

Teammates MUST exchange `SendMessage` with each other — not only with the lead — before reporting their `result_contract`. Lead does NOT relay. Required by `runtime-policy.yaml::agent_teams.cross_talk_protocol`. Enforcement is **mode-aware**: `teammate` mode opens a blocking gate on missing pairs; `inline` mode (tmux unavailable) downgrades to warning-only and the pipeline continues. Mode is resolved at preflight by `${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh` (`hard_requirement: true`).

**Required pairs (refactor):**
- `design-principles-specialist` ↔ `tdd-specialist` (refactor plan vs characterization tests)
- `tdd-specialist` ↔ `test-automation-engineer` (test inventory handoff)
- `code-reviewer` ↔ `security-reviewer` (adversarial review of changed diffs)

**Spawn-prompt rule:** every spawn prompt MUST include a `peers:` block listing teammate names this teammate must message before completing.

**Audit:** lead dumps team mailbox to `sep_log.mailbox[]`. A teammate returning `result_contract` with zero outbound `SendMessage` to a required peer triggers the Teammate Failure Protocol with `reason: cross-talk-missing` and opens `[Gate] Cross-Talk Missing | pair: <a>↔<b> | [R]espawn / [A]ccept / [X]Abort`.

## Visual Reporting Contract

- After every teammate returns, pipe its Result Contract `metrics` JSON to `${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh` and print the card inline. Respect `observability.teammate_cards.format` (ascii | compact | silent) from `runtime-policy.yaml`.
- Immediately before writing the SEP log, assemble the pipeline summary JSON (schema identical to `scripts/test-fixtures/pipeline-board-input.json`) and pipe to `${CLAUDE_PLUGIN_ROOT}/scripts/render-pipeline-board.sh`. Respect `observability.pipeline_board.enabled`.
- Renderer failures are non-fatal: log a WARNING in the SEP log and continue.

## Orchestration Contract — Mandatory Phases (CTS hard requirement)

The lead orchestrator MUST execute the four phases below in order on every
run of this skill. Skipping any phase is a contract violation. The SEP log
MUST record `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`,
`language_policy_applied: pt-BR`, and `timeouts_observed: [...]`. `scripts/validate.sh`
greps each dev-flow SKILL.md for the phase tags `CTS-PHASE: skill-init`,
`CTS-PHASE: agent-spawn`, `CTS-PHASE: agent-monitor`, `CTS-PHASE: agent-cleanup`,
and `CTS-PHASE: skill-finalize` to enforce wiring.

### Phase A — Skill Branch Init (CTS-PHASE: skill-init)

Run BEFORE any `Agent(...)` call:

```bash
INIT_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/init-skill-branch.sh refactor)
# parse: skill_branch=<...> base_branch=<...> base_commit=<...> watchdog_pid=<...>
```

- Exit 3 → tree dirty → emit `[Preflight Failed] main worktree dirty` and STOP.
- On success emit `[Skill Branch Created] skill_branch=<...> base_branch=<...> base_commit=<...>`.
- A background watchdog daemon is launched and its pid recorded. The watchdog
  enforces the per-agent and per-skill runtime caps as a last-resort safety
  net. THE WATCHDOG DOES NOT REPLACE THE LEAD'S MONITORING DUTY — see Phase B.1.
- Persist `skill_branch` value for Phases B and D.

### Phase B — Per-Agent Spawn Wrap (CTS-PHASE: agent-spawn)

For EVERY `Agent(...)` invocation in this skill (teammate or inline mode):

```bash
SPAWN_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/spawn-agent-worktree.sh refactor <agent_name> <agent_id>)
# parse: path=<...> branch=<...> base=<...> spawned_at=<epoch>
```

The Agent spawn `prompt` MUST begin with, in this exact order:

1. `language_policy.spawn_prompt_preamble` — literal text from `runtime-policy.yaml::language_policy.spawn_prompt_preamble` (pt-BR mandate).
2. The five worktree fields from `runtime-policy.yaml::agent_worktrees.spawn_prompt_inject.fields_appended_to_every_prompt`:
   - `skill_branch: <...>`
   - `worktree_path: <path>`
   - `branch: <branch>`
   - `base_commit: <base>`
   - `instruction: cd into worktree_path before any Read/Edit/Write/Bash. ...`
3. The role-specific spawn prompt body that this SKILL.md defines below.

Emit `[Worktree Spawned] agent=<...> | path=<...> | branch=<...> | spawned_at=<epoch>`.
Record `spawned_at` per agent — Phase B.1 needs it.

### Phase B.1 — Active Monitoring (CTS-PHASE: agent-monitor) — LEAD'S FIRST-LINE DUTY

This is what the orchestrator exists for. The watchdog is the OS-level
backstop; the lead is the first responder.

For every spawned agent the lead MUST:

1. **Track wall-clock since `spawned_at`.** Cap per agent is
   `runtime-policy.yaml::failure_handling.agent_max_runtime_seconds`
   (default 900s = 15 minutes). Skill-level cap is `skill_max_runtime_seconds`
   (default 7200s = 2 hours).

2. **Never block-wait indefinitely on a single agent.** Between status
   checks, do other work (other teammates' messages, gate handling) or
   sleep in short increments — never sit in an unbounded wait. If your
   runtime offers a polling primitive, use it; otherwise emit a status
   probe every ~120s.

3. **Detect stalls.** A teammate is considered stalled if EITHER:
   - wall-clock since `spawned_at` exceeds the per-agent cap, OR
   - no progress signal (SendMessage, tool call, partial output) for >
     `failure_handling.idle_seconds` (default 300s).

4. **On stall:**
   - Emit `[Teammate Timeout] agent=<...> | reason=<runtime_cap|idle> | age_seconds=<n>`.
   - Send `pkill -f -- "--agent-id <agent>@<skill>"` (or equivalent) to
     terminate the agent process.
   - Run `bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <path>`
     to remove the worktree (merge of partial work optional; merge failure
     non-fatal here).
   - Decrement retry budget. If budget remains and the failure mode is
     recoverable, respawn (Phase B again, fresh `spawned_at`). Otherwise
     open `[Gate] Teammate Failure | agent=<...> | reason=timeout |
     [R]espawn / [S]kip / [X]Abort`.
   - Append `{agent, reason, age_seconds, action}` to the SEP log's
     `timeouts_observed[]`.

5. **Never wait for human input from a subagent.** If a subagent emits a
   recovery prompt ("What should Claude do instead?"), the lead treats it
   as `reason=idle` and triggers the stall handler. Subagents MUST NOT
   block the skill on interactive prompts.

The watchdog daemon spawned in Phase A enforces the same caps independently;
if the lead misses a stall (e.g. it crashed or is itself stuck), the
watchdog kills the agent and writes a `.killed` marker. The lead MUST
inspect `ai-docs/.squad-log/.agents/*.killed` on its next tick and reflect
the kill in the SEP log.

### Phase C — Per-Agent Cleanup (CTS-PHASE: agent-cleanup)

Immediately after the Agent returns its `result_contract` (or after Phase
B.1 stall handling, or on skill abort):

```bash
CLEANUP_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <worktree_path>)
```

- Exit 0 → emit `[Worktree Cleanup] agent=<...> | merged=<true|false> | commits_ahead=<n> | branch_deleted=<branch>`.
- Exit 4 → merge conflict → emit `[Worktree Cleanup Conflict]` and open `[Gate] Worktree Merge Conflict | [R]esolve / [A]bort`. Worktree and branch are preserved until the user resolves.

This phase runs ONCE PER AGENT SPAWN (including timed-out spawns) and is non-skippable.

### Phase D — Skill Finalize (CTS-PHASE: skill-finalize)

After the last agent finishes, after the SEP log is written, and before
returning control to the user:

```bash
FINAL_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/finalize-skill.sh "$skill_branch")
```

- Exit 0 → emit `[Skill Finalized] skill_branch=<...> | orphan_worktrees=0 | orphan_branches=0`. Sentinel is removed; watchdog exits on its next tick.
- Non-zero → STOP and surface the failing invariant to the user. Do NOT mark the skill complete.

`finalize-skill.sh` does NOT push, merge to base, or delete the skill
branch — that is the user's call.

### Cross-Talk & Language Audit (mandatory checks before SEP write)

- Inspect mailbox: every Required Pair declared in this skill's
  `## Inter-Teammate Cross-Talk Protocol` must have at least one outbound
  `SendMessage`. Empty pair → Teammate Failure with `reason: cross-talk-missing`.
- The lead's user-facing output (gate prompts, narrative reports) MUST
  follow `runtime-policy.yaml::language_policy.lead_to_user_preamble` (pt-BR).
- SEP log MUST contain:
  - `language_policy_applied: pt-BR`
  - `cts_phases_completed: [skill-init, agent-spawn, agent-monitor, agent-cleanup, skill-finalize]`
  - `worktrees: [...]` (one entry per agent spawn with `path`, `branch`, `commits_ahead`, `merged`, `final_status`)
  - `timeouts_observed: [...]` (empty list if none — explicit field required)



## Execution

## Teammate Failure Protocol

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role.

**For every teammate spawned — without exception:**

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - Emit: `[Teammate Retry] <name> | Reason: silent failure — re-spawning`
   - Re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails:
   - Emit: `[Gate] Teammate Failure | <name> failed twice`
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

### Step 1 — Refactor Intake Gate

**Ticket Intake:** If the user provides a ticket ID (e.g., `/refactor PROJ-321`), read the ticket first via MCP. Extract target, goal, and constraints from the ticket description. Emit `[Ticket Read]` and skip asking for info already in the ticket.

Ask the user (skip fields already extracted from ticket):
1. **Target**: What code needs to be refactored? (file, module, class, function)
2. **Goal**: What specific improvement? (extract class, rename, reduce coupling, improve testability, remove duplication)
3. **Constraint**: What must NOT change? (public API, external behavior, DB schema)
4. **Risk tolerance**: Is this in a hot path or critical service?

### Step 2 — Stack Command Detection and Specialist Routing

Read project files to detect test command before spawning any agent:

| Signal file | test command |
|---|---|
| `Makefile` with `test:` | `make test` |
| `package.json` scripts | `npm test` |
| `pyproject.toml` | `pytest` |
| `pom.xml` | `mvn test` |
| `build.gradle` | `./gradlew test` |

Store as `{{test_command}}`. CLAUDE.md overrides take priority.

Also detect stack and resolve routing variables:

| Variable | `django` | `react` | `vue` | `typescript` | `javascript` | `python` | `generic` |
|---|---|---|---|---|---|---|---|
| `{{backend_agent}}` | `django-backend` | `backend-dev` | `backend-dev` | `backend-dev` | `backend-dev` | `python-developer` | `backend-dev` |
| `{{frontend_agent}}` | `django-frontend` | `react-developer` | `vue-developer` | `typescript-developer` | `javascript-developer` | `frontend-dev` | `frontend-dev` |
| `{{reviewer_agent}}` | `code-reviewer` | `reviewer` | `reviewer` | `reviewer` | `reviewer` | `reviewer` | `reviewer` |

Emit: `[Stack Detected] {{detected_stack}} | backend={{backend_agent}} | frontend={{frontend_agent}} | reviewer={{reviewer_agent}}`

### Step 3 — Spawn design-principles-specialist for analysis

Use TeamCreate to create a team named "refactor-team". Then spawn each agent using the Agent tool with `team_name="refactor-team"` and a descriptive `name` for each agent.

```
Agent(
  subagent_type = "claude-tech-squad:design-principles-specialist",
  team_name = "refactor-team",
  name = "design-principles-specialist",
  prompt = """
## Refactor Analysis

### Target
{{target_description}}

### Goal
{{refactor_goal}}

### Constraint
{{constraints}}

---
You are the Design Principles Specialist. Analyze the target code and produce:
1. **Current problems** — specific violations (high coupling, low cohesion, SRP violation, duplication, etc.)
2. **Refactor plan** — ordered list of small, safe steps (each step should be independently verifiable)
3. **Risk assessment** — what could break at each step?
4. **Characterization test needs** — what behavior must be covered by tests before refactoring starts?
5. **Definition of done** — how do we know the refactor is complete and correct?

Each step in the plan must be atomic: it either makes things better or can be rolled back cleanly.
Do NOT chain to other agents.
"""
)
```

### Step 4 — Refactor plan confirmation gate

Present the analysis and plan to the user:

```
Refactor analysis complete.

Target: {{target}}
Problems identified: N
Steps planned: N

Step 1: {{step_1_description}} (risk: low/medium/high)
Step 2: {{step_2_description}} (risk: low/medium/high)
...

Characterization tests needed for: {{list}}

Proceed with this plan? [Y/N/modify]
```

**This is a blocking gate.** Do NOT write characterization tests until user confirms the plan.

### Test Gate (Mandatory)

This skill is in `mandatory_test_gate.skills_in_scope` (see `runtime-policy.yaml#mandatory_test_gate`).

Refactor adapts the contract:
- `tdd-specialist` MUST be spawned to confirm characterization tests lock all behavior the refactor will touch — this acts as the pre-impl test contract.
- `test-automation-engineer` writes the characterization tests, runs them green on unmodified code, then re-runs after the refactor completes (post-impl validation pass).
- After the post-impl pass, `hooks/test-gate.sh` evaluates the gate. A `BLOCKING` verdict (e.g., refactor introduced a new untested branch) halts the pipeline.
- No exemption.

### Step 4b — Spawn tdd-specialist (Behavioral Contract)

```
Agent(team_name="refactor-team", name="tdd-specialist", subagent_type="claude-tech-squad:tdd-specialist",
  prompt="Define the behavioral contract this refactor MUST preserve. List the characterization tests that must exist before any refactor step. Hand contract to test-automation-engineer.")
```

### Step 5 — Write characterization tests

Spawn test-automation-engineer to write tests that lock current behavior:

```
Agent(
  subagent_type = "claude-tech-squad:test-automation-engineer",
  team_name = "refactor-team",
  name = "test-automation-engineer",
  prompt = """
## Characterization Tests

### Target
{{target_description}}

### Current behavior to lock
{{characterization_test_needs}}

### Test command
{{test_command}}

### Constraint
Do NOT test implementation details. Test observable behavior only:
- Return values
- Side effects (DB writes, events emitted, external calls made)
- Error cases

---
Write characterization tests that will FAIL if the behavior changes during refactoring.
These tests must pass on the CURRENT code before any refactoring begins.

Run {{test_command}} to confirm all tests pass.

Return:
## Completion Block
- Tests written: N
- Files created/modified: [list]
- Test result: {{test_command}} → PASS/FAIL
Do NOT chain.
"""
)
```

Run `{{test_command}}`. If tests fail on the current code: the characterization tests are wrong. Spawn test-automation-engineer again to fix them. Do NOT proceed to refactoring until all characterization tests pass on unmodified code.

Emit: `[Characterization Tests] N tests written — all PASS on current code`

### Step 6 — Execute refactor steps incrementally

For each step in the refactor plan:

1. Spawn the appropriate implementation agent (backend-dev, frontend-dev, etc.):

```
Agent(
  subagent_type = "claude-tech-squad:{{backend_agent}}",  # or {{frontend_agent}} for frontend steps
  team_name = "refactor-team",
  name = "backend-dev",  # or frontend-dev
  prompt = """
## Refactor Step {{N}} of {{total}}

### Step Description
{{step_description}}

### Constraint
- Do NOT change observable behavior
- Do NOT change public API signatures unless explicitly in the plan
- Keep each step small and independently verifiable

### Test command
{{test_command}}

---
Implement this refactor step.
After implementing, run {{test_command}}.
All characterization tests MUST still pass.

Return:
## Completion Block
- Step: {{N}}
- Files changed: [list]
- Test result: {{test_command}} → PASS/FAIL (N passed)
- Behavior preserved: yes / no (explain if no)
Do NOT chain.
"""
)
```

2. After each step: verify `{{test_command}}` passes.

3. If tests fail after a step:
   - Emit: `[Refactor Step {{N}} FAILED] Characterization tests broke — rolling back`
   - Ask user: `[Gate] Step {{N}} broke tests. Options: [F]ix the step, [S]kip this step, [A]bort refactor`
   - If Fix: spawn implementation agent with failure context
   - If Skip: proceed to next step
   - If Abort: stop here, leave code in last known-good state

Emit per step: `[Refactor Step {{N}}] {{description}} — PASS`

### Step 6b — Test Automation Engineer (Post-Refactor Validation)

```
Agent(team_name="refactor-team", name="test-automation-validate", subagent_type="claude-tech-squad:test-automation-engineer",
  prompt="Re-run characterization tests against the refactored code. Add tests for any newly introduced branches. Report unpaired files in your Result Contract.")
```

Wait for completion. The PostToolUse `hooks/test-gate.sh` then evaluates the gate.

### Step 7 — Spawn reviewer for final review

After all steps complete:

```
Agent(
  subagent_type = "claude-tech-squad:{{reviewer_agent}}",
  team_name = "refactor-team",
  name = "reviewer",
  prompt = """
## Refactor Review

### Goal
{{refactor_goal}}

### Changes made
{{aggregated_diffs}}

### Characterization test results
{{test_results}}

---
Review this refactor for:
1. Does it achieve the stated goal?
2. Are there any remaining code smells or opportunities missed?
3. Did any step accidentally change behavior (check characterization tests carefully)?
4. Is the code simpler and more readable than before?

Return: APPROVED or CHANGES REQUESTED with specific issues.
Do NOT chain.
"""
)
```

If CHANGES REQUESTED: spawn the implementation agent again with the specific feedback. Re-run tests. Re-run reviewer. Repeat until APPROVED.

### Step 7b — Quality Bench

After reviewer APPROVED, spawn specialist reviewers in parallel:

```
Agent(subagent_type="claude-tech-squad:security-reviewer",  team_name="refactor-team", name="security-rev",  prompt="Review this refactor for security issues. Changed code: {{aggregated_diffs}}. Return findings as a checklist. Do NOT chain.")
Agent(subagent_type="claude-tech-squad:privacy-reviewer",   team_name="refactor-team", name="privacy-rev",   prompt="Review this refactor for privacy/PII issues. Changed code: {{aggregated_diffs}}. Return findings as a checklist. Do NOT chain.")
Agent(subagent_type="claude-tech-squad:performance-engineer", team_name="refactor-team", name="perf-eng",    prompt="Review this refactor for performance regressions. Changed code: {{aggregated_diffs}}. Return findings as a checklist. Do NOT chain.")
Agent(subagent_type="claude-tech-squad:code-quality",       team_name="refactor-team", name="code-quality",  prompt="Run lint ({{lint_command}}) on the changed files. Report violations that would fail CI. Return findings as a checklist. Do NOT chain.")
```

Emit: `[Batch Spawned] quality-bench | Teammates: security-rev, privacy-rev, perf-eng, code-quality`

**After all return**, classify findings:
- **BLOCKING** (security vulns, PII leaks, CI-breaking lint): spawn implementation agent with fix mandate, re-run flagging reviewers — max 2 cycles
- **WARNING** only: surface to user `[A]ccept / [F]ix before advancing`

Emit: `[Gate] Quality Bench Complete | Advancing to final test run`

### Step 8 — Final test run

```bash
{{test_command}}
```

Confirm all characterization tests pass. Confirm no new test failures introduced.

### Step 9 — Write SEP log (SEP Contrato 1)

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-refactor-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: refactor
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [preflight-passed, refactor-complete, tests-passed]
fallbacks_invoked: []
target: {{target}}
steps_planned: N
steps_completed: N
steps_skipped: N
characterization_tests_written: N
reviewer_result: APPROVED
test_result: PASS
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Refactor Summary
{{one_paragraph}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 10 — Report to user

Tell the user:
- Steps completed / skipped / failed
- Files changed
- Characterization tests written (N) — these can now serve as regression tests
- Reviewer result
- Test suite result
- Suggestion: commit with message `refactor: {{goal}}`
