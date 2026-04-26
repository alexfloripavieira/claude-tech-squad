# Live Capture Attempts

Date: 2026-04-22
Claude Code: 2.1.117
Plugin: claude-tech-squad v5.52.0

## Attempt 1 — layered-monolith

Command shape:

```bash
claude -p --plugin-dir plugins/claude-tech-squad --max-budget-usd 1.00 --permission-mode dontAsk --allowedTools Read,Grep,Glob,Bash < ai-docs/dogfood-runs/layered-monolith/2026-04-22T12-00-00Z/prompt.txt
```

Outcome:

- Connected to Claude Code successfully after sandbox network escalation.
- Produced visible `/discovery` trace lines.
- Produced a layered-monolith blueprint.
- Did not write SEP artifacts because editing tools were disabled.
- Did not emit a `result_contract` block, so the existing validated contract-replay artifact remains the canonical `final.md`.

Key trace lines observed:

```text
[Preflight Start] discovery
[Preflight Passed] discovery | execution_mode=inline-demo | architecture_style=layered-monolith (preserved) | lint_profile=repo-default | docs_lookup_mode=context7-first | runtime_policy=loaded
[Team Created] discovery
[Minimal Specialist Set] Selected: backend-architect, api-designer, dba, security-reviewer, test-planner, tdd-specialist
[Batch Completed] specialist-bench | 6/6 returned
[Gate] implement-bridge | Next: `/implement ai-docs/audit-log-filters/blueprint.md`
[Team Deleted] discovery | cleanup complete
```

## Attempt 2 — hexagonal-billing

Command shape:

```bash
cat ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T12-10-00Z/prompt.txt ai-docs/dogfood-runs/live-capture-instructions.md | claude -p --plugin-dir plugins/claude-tech-squad --max-budget-usd 1.50 --permission-mode dontAsk --allowedTools Read,Grep,Glob,Bash
```

Outcome:

- Connected to Claude Code successfully.
- Blocked before full execution.
- Claude Code identified three faithful-run blockers:
  - non-interactive `claude -p` cannot resolve operator gates;
  - teammate runtime is not available as a real tmux/team host in this capture mode;
  - no-edit mode prevents required SEP log, ADR, and implementation artifacts.

This is useful evidence: live capture should not be represented as complete unless it runs in an interactive or tmux session with explicit gate decisions and permission to write `ai-docs/`.

## Required Adjustment

To convert the five `local-contract-replay` golden runs into true live golden runs:

1. Run Claude Code interactively, not `claude -p`, for workflows with gates.
2. Load the local plugin with `--plugin-dir plugins/claude-tech-squad`.
3. Allow writes to `ai-docs/` so SEP logs and rollover artifacts are real.
4. Answer every gate explicitly and copy the visible trace into each `trace.md`.
5. Preserve `result_contract` evidence in each `final.md`.
6. Run:

```bash
bash scripts/dogfood-report.sh
bash scripts/smoke-test.sh
```
