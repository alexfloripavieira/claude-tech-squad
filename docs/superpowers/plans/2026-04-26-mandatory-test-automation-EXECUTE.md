# Execution Prompt — Mandatory Test Automation

Copy the block below into a new session at the repository root (`/home/alex/claude-tech-squad`). It is self-contained: the new session has no prior context.

---

```
You are executing a pre-approved implementation plan in the claude-tech-squad repository.

CONTEXT TO LOAD FIRST (read in this order, do not skip):
1. /home/alex/claude-tech-squad/CLAUDE.md — project rules, validation commands, commit conventions, change-class taxonomy.
2. /home/alex/claude-tech-squad/docs/superpowers/specs/2026-04-26-mandatory-test-automation-design.md — the approved design spec. Sections 4–10 define the three pillars (A enforcement, B runtime gate, C bootstrap) and the rollout sequence.
3. /home/alex/claude-tech-squad/docs/superpowers/plans/2026-04-26-mandatory-test-automation.md — the implementation plan with 25 bite-sized tasks across Phases A, B, C plus a D1 follow-up.

EXECUTION MODE: subagent-driven.
- Use the superpowers:subagent-driven-development skill.
- Dispatch one fresh subagent per Task in the plan, in order (A1 → A2 → ... → A9, then B1 → ... → B8, then C1 → ... → C6).
- Between subagent runs, you (the orchestrator) review the diff, run the validation commands the Task lists, and only proceed when green.
- D1 is a post-shadow follow-up — do NOT run it as part of this execution. Stop after Task C6.

PHASE GATES — do not cross between phases until the gate passes:
- After Task A9: run `bash scripts/validate.sh && bash scripts/smoke-test.sh`. Both must pass. Tag with `git tag --no-sign mandatory-test-automation-pr-a`. Stop and report to the user. Do not auto-open the PR.
- After Task B8: run `bash scripts/validate.sh && bash scripts/smoke-test.sh && bash scripts/dogfood.sh`. All must pass. Tag with `mandatory-test-automation-pr-b`. Stop and report.
- After Task C6: run all three validation commands. Tag with `mandatory-test-automation-pr-c`. Stop and report.

NON-NEGOTIABLE RULES (from CLAUDE.md):
- Conventional Commits only. Allowed prefixes: feat:, fix:, docs:, refactor:, chore:, test:.
- NEVER use emojis or icons in commits, PRs, or documentation.
- NEVER mention "Claude", "AI", "GPT", "LLM", "Copilot", "Anthropic", or "Co-Authored-By <AI>" in any commit, PR, or doc.
- NEVER auto-push or auto-open a PR — stop at the phase gate and let the user decide.
- NEVER edit files marked "must NOT be edited manually" in CLAUDE.md (CHANGELOG.md, marketplace.json, plugin.json, docs/MANUAL.md). The release pipeline owns them.
- NO docstrings in functions or methods. NO inline comments inside method bodies. Code must be self-documenting.
- Run validation commands the plan specifies — do not skip or simulate them.
- If any validation fails, STOP and report. Do not "fix forward" by editing unrelated code.

OPERATING DISCIPLINE:
- For every Task, read its full body in the plan before dispatching the subagent. The subagent prompt MUST include: the Task number, the exact files to create/modify, every Step in order, and the literal code/commands the plan specifies.
- After each subagent finishes, run `git status` and `git log -1 --stat` to verify the change is what the plan asked for. If a subagent skipped a Step, redispatch with a corrected prompt.
- Use the TaskCreate / TaskUpdate tools (one task per plan Task) to track progress.
- Self-verify before claiming completion: open the modified file, confirm the change is present, run the test/validation step the plan calls out.
- If a Step in the plan turns out to be wrong (e.g., file path drift, existing API mismatch), STOP. Report to the user with the specific evidence (file path, grep output, error message) and propose a correction. Do not silently adapt the plan.

START NOW with Task A1: "Add mandatory_test_gate to runtime-policy.yaml". Dispatch the first subagent.
```

---

## How to use

1. Open a new Claude Code session at the repo root.
2. Paste the entire block between the triple backticks above.
3. The session will load context, then begin executing Task A1 via a subagent.
4. The session will pause at each phase gate (after A9, B8, C6). You decide whether to open a PR for that phase before letting it continue.

## Verifying it ran correctly

After each phase, the artifacts should match the plan exactly:

| Phase | Artifacts to verify |
|---|---|
| A | `runtime-policy.yaml` has `mandatory_test_gate:` block; `validate.sh` has `validate_test_gate_contract`; 5 SKILL.md have `### Test Gate (Mandatory)` (or Exemption Protocol for hotfix); `docs/SKILL-CONTRACT.md` has new section. Tag `mandatory-test-automation-pr-a` exists. |
| B | `plugins/claude-tech-squad/bin/squad_cli/test_gate.py` exists with `check_paired_tests`, `evaluate_gate`, `detect_test_infra`; pytest suite green; `hooks/test-gate.sh` exists and is executable; `settings-template.json` references it; SEP log schema documents `test_gate` block. Tag `mandatory-test-automation-pr-b` exists. |
| C | `preflight.py` has `check_test_infra`; `task_memory.py` exposes `TaskMemory` class; `skills/test-bootstrap/SKILL.md` exists; `fixtures/dogfooding/no-test-infra/` exists and is registered in `scenarios.json`. Tag `mandatory-test-automation-pr-c` exists. |

If anything in the table is missing after a phase, a Step was skipped — investigate the SEP log for that run and redispatch the missing Task.
