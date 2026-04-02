# Execution Trace

This guide explains how to interpret the visible squad execution emitted by `claude-tech-squad`.

Use it when you want to confirm that the plugin is actually orchestrating specialists, not just producing one consolidated answer.

---

## Two Execution Modes

### Inline mode (default)

Agents run as subagents inside the same Claude session. Visibility comes from progress lines emitted in the assistant output.

### Teammate mode (tmux panes)

Each specialist spawns as an independent Claude Code instance in its own tmux pane. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and `CLAUDE_CODE_TEAMMATE_MODE=tmux` in `~/.claude/settings.json`, and Claude Code started inside a tmux session.

See [GETTING-STARTED.md](GETTING-STARTED.md) for setup instructions.

---

## What You Should Expect

### Inline mode trace

A healthy run shows:

```text
[Preflight Start] discovery
[Preflight Passed] discovery | execution_mode=inline | architecture_style=layered | lint_profile=eslint,prettier | docs_lookup_mode=context7 | runtime_policy=5.22.0
[Checkpoint Saved] discovery | cursor=preflight-passed
[Phase Start] discovery
[Agent Start] PM | claude-tech-squad:pm | First-pass product analysis
[Agent Done] PM | Status: completed | Output: scope options and open questions
[Agent Start] Business Analyst | claude-tech-squad:business-analyst | Domain rules
[Agent Done] Business Analyst | Status: completed | Output: 5 domain rules, 2 edge cases
[Agent Blocked] PO | Waiting on: user scope validation (Gate 1)
[Agent Batch Start] specialist-bench | Agents: backend-architect, rag-engineer, prompt-engineer
[Agent Start] Backend Architect | claude-tech-squad:backend-architect | Service design
[Agent Done] Backend Architect | Status: completed | Output: hexagonal layers defined
[Agent Start] RAG Engineer | claude-tech-squad:rag-engineer | Retrieval stack design
[Agent Done] RAG Engineer | Status: completed | Output: chunking + hybrid search plan
[Agent Batch Done] specialist-bench | Outcome: specialist notes ready
```

### Teammate mode trace

```text
[Preflight Start] discovery
[Resume From] discovery | checkpoint=gate-3-approved
[Preflight Passed] discovery | execution_mode=tmux | architecture_style=hexagonal | lint_profile=ruff,mypy | docs_lookup_mode=repo-fallback | runtime_policy=5.22.0
[Team Created] discovery
[Teammate Spawned] pm | pane: pm
[Teammate Spawned] ba | pane: ba
[Fallback Invoked] planner -> claude-tech-squad:techlead | Reason: primary failed twice
[Gate] Scope Validation | Waiting for user input
[Batch Spawned] specialist-bench | Teammates: backend-arch, rag-engineer, prompt-engineer, agent-architect
[Teammate Done] backend-arch | Output: hexagonal layers defined
[Teammate Done] rag-engineer | Output: hybrid search plan ready
[Teammate Done] reviewer | Status: APPROVED
[Teammate Done] qa | Status: PASS
```

---

## How To Read Each Line

### Inline mode lines

`[Phase Start]`
- Marks a new stage: Discovery, Implementation, Release
- If the phase changes with no agent lines after it, the run is incomplete

`[Agent Start]`
- The workflow is handing work to a specific specialist
- Shows role, `subagent_type`, and immediate objective
- This is the strongest proof of real specialist handoff

`[Agent Done]`
- Specialist finished its pass
- Every `Agent Start` should eventually have a matching `Agent Done`

`[Agent Batch Start]` and `[Agent Batch Done]`
- Multiple specialists running in parallel
- Individual `Agent Start` and `Agent Done` lines should appear inside the batch

`[Agent Blocked]`
- Workflow cannot proceed — missing user decision, input, or access
- A blocked line is a visible gate, not a bug

`[Preflight Start]`, `[Preflight Warning]`, `[Preflight Passed]`
- Confirms the workflow validated execution mode, architecture style, lint profile, and docs lookup mode before spawning teammates
- Confirms the workflow also loaded the central runtime policy
- If these lines are missing, the run skipped the runtime contract checks

`[Agent Retry]`
- Workflow looped after review or validation failure
- Healthy when tied to a concrete reason: failed QA, reviewer request, specialist finding

`[Fallback Invoked]`
- The primary teammate failed twice and the workflow invoked the runtime policy fallback matrix
- This is expected in a resilient run and should also appear in the SEP log

`[Resume From]` and `[Checkpoint Saved]`
- The workflow resumed from or persisted a runtime checkpoint
- These lines prove that phase resume is active instead of restarting the whole pipeline blindly

### Teammate mode lines

`[Team Created]`
- A new team was created for this workflow run

`[Teammate Spawned]`
- A specialist was spawned in its own tmux pane
- Shows the pane name and role

`[Gate]`
- Workflow paused for user input at a decision point

`[Batch Spawned]`
- Multiple teammates spawned in parallel
- Each gets its own pane

`[Teammate Done]`
- Teammate finished and returned results to the orchestrator

---

## What A Healthy Run Looks Like

- Phases appear in a sensible order
- Each phase has the expected specialist handoffs
- Starts and completions are balanced
- Batch runs are followed by individual agent lines
- Preflight appears before team or phase creation
- Checkpoint or resume lines appear when a run is resumed or a major gate/phase is cleared
- The final `Agent Execution Log` matches the visible trace
- The final report contains real artifact output, not only the trace
- Specialist outputs include role-specific content plus `result_contract`

---

## What A Suspicious Run Looks Like

These patterns mean the run did not execute as intended:

- Only a final answer appears with no trace lines at all
- There are `Agent Start` lines but no `Agent Done` lines and no blocked reason
- The workflow jumps from Discovery straight to Release with no intermediate activity
- The `Agent Execution Log` lists agents that never appeared in the visible trace
- The output claims a specialist reviewed something but gives no role-specific summary
- Specialist outputs do not include `result_contract`
- A resumed run starts from the beginning with no `[Resume From]` line even though a checkpoint exists
- In teammate mode: no tmux panes open (Claude Code not started inside tmux, or env vars missing)

---

## What To Do If The Trace Looks Wrong

1. Restart Claude Code if you just updated the plugin and have not restarted yet.
2. Re-run with an explicit request for visible execution lines and `Agent Execution Log`.
3. Start with `/claude-tech-squad:discovery` for a small request before using `/claude-tech-squad:squad`.
4. If Jira, Confluence, or another external dependency is part of the task, confirm access is available.
5. If teammate mode panes are not opening: confirm tmux session is active, env vars are set, and Claude Code was started inside tmux.
6. If the trace is still missing, inspect the installed plugin version with `claude plugin list`.

---

## Minimal Smoke Test

Use this prompt after updating the plugin:

```text
/claude-tech-squad:discovery
Run a very small discovery-only smoke test in this repository and show explicit Phase Start, Agent Start, Agent Done, and Agent Execution Log lines.
```

Expected result:

- at least one `[Preflight Start]`
- at least one `[Preflight Passed]` or `[Preflight Warning]`
- at least one `[Phase Start]` or `[Team Created]`
- at least one `[Agent Start]` or `[Teammate Spawned]`
- at least one matching completion line
- a final `Agent Execution Log`

## Static Contract Test

Run:

```bash
bash scripts/smoke-test.sh
bash scripts/dogfood.sh
bash scripts/dogfood-report.sh --schema-only
```

Expected result:

- `claude-tech-squad validation passed`
- `claude-tech-squad smoke test passed`
- `claude-tech-squad dogfood fixtures passed`
- `claude-tech-squad golden run schema passed`
- no stale `code-debugger` references
- main orchestrators contain preflight, ARC, runtime policy, and checkpoint/resume sections

---

## Real Audit Prompt

```text
/claude-tech-squad:squad
Audit the linked Jira story against the current repository implementation. Show explicit visible execution lines for the squad, keep an Agent Execution Log, and deliver matrices for requirements and acceptance criteria with evidence.
```
