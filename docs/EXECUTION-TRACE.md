# Execution Trace

This guide explains how to interpret the visible squad execution emitted by `claude-tech-squad`.

Use it when you want to confirm that the plugin is actually orchestrating specialists, not just producing one consolidated answer.

## What You Should Expect

A healthy run usually shows:

- a phase transition with `[Phase Start]`
- one or more explicit handoffs with `[Agent Start]`
- matching completions with `[Agent Done]`
- batch markers when specialists run in parallel
- a final `Agent Execution Log`

Example:

```text
[Phase Start] Discovery
[Agent Start] PM | claude-tech-squad:pm | First-pass product analysis
[Agent Done] PM | Status: completed | Output: scope options and open questions
[Agent Batch Start] Specialist Design Bench | Agents: Backend Architect, Frontend Architect
[Agent Start] Backend Architect | claude-tech-squad:backend-architect | Service design review
[Agent Done] Backend Architect | Status: completed | Output: API and domain boundaries
[Agent Start] Frontend Architect | claude-tech-squad:frontend-architect | UI architecture review
[Agent Done] Frontend Architect | Status: completed | Output: state and composition plan
[Agent Batch Done] Specialist Design Bench | Outcome: architecture slices ready
```

## How To Read Each Line

`[Phase Start]`

- means the workflow has moved into a new stage such as Discovery, Blueprint, Build, Quality, or Release
- if the phase changes with no agent lines after it, the run is incomplete or the output was interrupted

`[Agent Start]`

- means the workflow is handing work to a specific specialist
- the line should tell you the role, the `subagent_type`, and the immediate objective
- this is the strongest visible proof that the plugin is orchestrating a real specialist handoff

`[Agent Done]`

- means that specialist finished its pass
- the summary should be short, concrete, and tied to the role that ran
- every `Agent Start` should eventually have a matching `Agent Done`, unless the run is blocked or interrupted

`[Agent Batch Start]` and `[Agent Batch Done]`

- mean that multiple specialists are being run as a parallel bench
- you should still see the individual `Agent Start` and `Agent Done` lines for the agents inside the batch
- the batch summary should explain what the grouped run achieved

`[Agent Blocked]`

- means the workflow cannot proceed cleanly
- common reasons: missing user decisions, missing discovery input, inaccessible Jira or Confluence context, failing test setup, or unresolved review feedback
- a blocked line is not a bug by itself; it is a visible gate

`[Agent Retry]`

- means the workflow intentionally looped after review or validation failure
- this is healthy when it is tied to a concrete reason such as failed QA, a reviewer request, or a critical specialist finding

## What A Healthy Run Looks Like

Signs that the trace is behaving correctly:

- phases appear in a sensible order
- each phase has the expected specialist handoffs
- starts and completions are balanced
- batch runs are followed by individual agent lines
- the final `Agent Execution Log` matches the visible trace above it
- the final report still contains the real artifact output, not only the trace

## What A Suspicious Run Looks Like

These patterns usually mean the run did not execute as intended:

- only a final answer appears, with no trace lines at all
- there are `Agent Start` lines but no `Agent Done` lines and no blocked reason
- the workflow jumps from Discovery straight to Release with no intermediate specialist activity
- the `Agent Execution Log` lists agents that never appeared in the visible trace
- the output claims a specialist reviewed something but gives no role-specific summary

## What To Do If The Trace Looks Wrong

1. Restart Claude Code if you just updated the plugin and have not restarted yet.
2. Re-run with an explicit request for visible execution lines and `Agent Execution Log`.
3. Start with `/claude-tech-squad:discovery` for a small request before using `/claude-tech-squad:squad`.
4. If Jira, Confluence, or another external dependency is part of the task, confirm access is available.
5. If the trace is still missing, inspect the installed plugin version with `claude plugin list`.

## Minimal Smoke Test

Use this prompt after updating the plugin:

```text
/claude-tech-squad:discovery
Run a very small discovery-only smoke test in this repository and show explicit Phase Start, Agent Start, Agent Done, and Agent Execution Log lines.
```

Expected result:

- at least one `Phase Start`
- at least one `Agent Start`
- at least one matching `Agent Done`
- a final `Agent Execution Log`

## Real Audit Prompt

For a real multi-role audit:

```text
/claude-tech-squad:squad
Audit the linked Jira story against the current repository implementation. Show explicit visible execution lines for the squad, keep an Agent Execution Log, and deliver matrices for requirements and acceptance criteria with evidence.
```
