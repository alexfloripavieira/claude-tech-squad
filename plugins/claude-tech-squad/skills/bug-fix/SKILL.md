---
name: bug-fix
description: Focused bug resolution workflow. Takes a bug report (error message, stack trace, reproduction steps), investigates root cause, writes a failing test that proves the bug, implements the fix, and validates with real tool execution. Trigger with "corrigir bug", "fix bug", "investigar erro", "resolver issue", "bug fix".
user-invocable: true
---

# /bug-fix — Focused Bug Resolution

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in any environment
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a "quick fix"
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Lightweight defect resolution workflow. Faster than `/squad` for isolated bugs — skips discovery/planning phases and goes straight to root cause → failing test → fix → validation.

## When to Use

- Bug with a known reproduction path (error message, stack trace, or clear steps to reproduce)
- Defect in existing behavior (not a feature request)
- Scope contained to 1–5 files

**Escalate to `/squad` if:**
- Root cause investigation reveals an architectural problem
- Fix requires changes to more than 5 files
- The bug exposes a design flaw that requires refactoring

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

### Step 1 — Bug Intake Gate

Ask the user for:
1. **Symptom**: What is the observed behavior? (error message, stack trace, screenshot)
2. **Expected**: What should happen instead?
3. **Reproduction**: Steps or code to reproduce
4. **Context**: Environment (dev/staging/prod), recent changes if known

Do not proceed until you have at least symptom + expected behavior.

### Step 1b — Stack Specialist Routing

Before creating the team, detect the repository stack and resolve agent routing:

| Signal | Detected stack |
|---|---|
| `manage.py` + `django` in requirements | `django` |
| `package.json` with `"react"` | `react` |
| `package.json` with `"vue"` | `vue` |
| `tsconfig.json` or `typescript` in devDeps | `typescript` |
| `package.json` (no react/vue/ts) | `javascript` |
| `pyproject.toml`/`requirements.txt` without `manage.py` | `python` |
| None | `generic` |

Routing variables:

| Variable | `django` | `react` | `vue` | `typescript` | `javascript` | `python` | `generic` |
|---|---|---|---|---|---|---|---|
| `{{backend_agent}}` | `django-backend` | `backend-dev` | `backend-dev` | `backend-dev` | `backend-dev` | `python-developer` | `backend-dev` |
| `{{frontend_agent}}` | `django-frontend` | `react-developer` | `vue-developer` | `typescript-developer` | `javascript-developer` | `frontend-dev` | `frontend-dev` |
| `{{reviewer_agent}}` | `code-reviewer` | `reviewer` | `reviewer` | `reviewer` | `reviewer` | `reviewer` | `reviewer` |
| `{{qa_agent}}` | `qa-tester` | `qa-tester` | `qa-tester` | `qa-tester` | `qa-tester` | `qa` | `qa` |

Emit: `[Stack Detected] {{detected_stack}} | backend={{backend_agent}} | frontend={{frontend_agent}} | reviewer={{reviewer_agent}} | qa={{qa_agent}}`

### Step 2 — Root Cause Analysis

Use TeamCreate to create a team named "bug-fix-team". Then spawn each agent using the Agent tool with `team_name="bug-fix-team"` and a descriptive `name` for each agent.

Invoke the Agent tool with `subagent_type: "claude-tech-squad:techlead"`, `team_name: "bug-fix-team"`, `name: "techlead"`.

Prompt:
```
You are the Tech Lead. A bug has been reported. Perform root cause analysis.

Bug report:
- Symptom: {{symptom}}
- Expected: {{expected}}
- Reproduction: {{reproduction}}
- Context: {{context}}

Tasks:
1. Identify the likely root cause (hypothesis)
2. Identify the exact file(s) and function(s) involved
3. Classify: Is this a logic error, data issue, integration fault, race condition, or configuration problem?
4. Assess scope: Can this be fixed in 1–5 files, or does it require architectural changes?
5. If architectural changes are needed, say ESCALATE and explain why

Output: root cause hypothesis, affected files, fix strategy, scope assessment.

Return your output in EXACTLY this format:
```
## Output from TechLead — Root Cause Analysis

### Root Cause
[1-2 sentences describing the exact cause]

### Affected Files
- [file_path]: [what needs to change]

### Fix Strategy
[approach in 2-3 sentences]

### Scope Assessment
CONTAINED | BROAD

### Escalation
NONE | ESCALATE: [reason]
```
Do NOT chain to other agents.
```

If techlead outputs ESCALATE: stop and tell the user to use `/squad` instead.

### Step 3 — Write Failing Test

Invoke the Agent tool with `subagent_type: "claude-tech-squad:tdd-specialist"`, `team_name: "bug-fix-team"`, `name: "tdd-specialist"`.

Prompt:
```
You are the TDD Specialist. A bug has been identified. Write the failing test that proves it.

Root cause: {{techlead_output}}
Affected files: {{affected_files}}
Fix strategy: {{fix_strategy}}

Tasks:
1. Write a test that FAILS with the current code (proving the bug exists)
2. The test must pass after the fix is applied
3. Place the test in the correct test file following project conventions
4. Use the project's existing test framework and fixtures

Do NOT implement the fix. Only write the failing test.
Output: test file path, test name, the test code.
```

### Step 4 — Implement the Fix

Based on the affected files, invoke the appropriate implementation agent.

**If the bug is in backend/server-side code:**
Invoke `subagent_type: "claude-tech-squad:{{backend_agent}}"`, `team_name: "bug-fix-team"`, `name: "backend-dev"`.

**If the bug is in frontend/UI code:**
Invoke `subagent_type: "claude-tech-squad:{{frontend_agent}}"`, `team_name: "bug-fix-team"`, `name: "frontend-dev"`.

**If the bug spans both:**
Invoke both agents sequentially — backend first, then frontend. Use `subagent_type: "claude-tech-squad:{{backend_agent}}"` and `subagent_type: "claude-tech-squad:{{frontend_agent}}"` respectively.

Prompt template:
```
You are the [Backend/Frontend] Dev. Implement a targeted bug fix.

Root cause: {{techlead_output}}
Affected files: {{affected_files}}
Fix strategy: {{fix_strategy}}
Failing test: {{tdd_output}}

Rules:
- Fix ONLY what is described. Do not refactor surrounding code.
- The failing test must pass after your fix.
- Do not introduce new behavior beyond what is needed to fix the bug.
- Follow the project's coding standards (Hexagonal Architecture, no direct DB JOINs across apps, etc.)
- Verify all library APIs via context7 before using them.

PERFUMARIA GUARD (non-negotiable):
- Do NOT extract helpers, rename variables, reorganize functions, or eliminate duplication unless the duplication itself is the direct cause of the bug.
- Do NOT apply DRY improvements, SRP refactors, or "clean code" suggestions as part of this fix.
- Do NOT improve code that is adjacent to the fix but not part of the bug path.
- If a reviewer later suggests refactoring: defer it. Never implement refactoring under a bug-fix commit.
- The diff must be the smallest possible change that makes the failing test pass.

Safety constraints (non-negotiable):
- Never force-push (`git push --force`) to any branch
- Never skip pre-commit hooks (`git commit --no-verify`)
- Never drop tables, databases, or truncate data without explicit user confirmation
- Never disable authentication or authorization as a fix
- If the fix requires any of the above, STOP and report to the user

Output: list of changed files with a one-line description of each change.
```

### Step 5 — Validate Fix (Real Tool Execution)

Invoke the Agent tool with `subagent_type: "claude-tech-squad:{{qa_agent}}"`, `team_name: "bug-fix-team"`, `name: "qa"`.

Prompt:
```
You are QA. Validate a bug fix.

The failing test from Step 3: {{test_name}} in {{test_file}}
The fix from Step 4: {{changed_files}}

Tasks:
1. Run lint gate first (ruff/eslint) — stop if lint fails
2. Run the specific failing test — it must now PASS
3. Run the full test suite for the affected app/module — zero new failures allowed
4. Report: test that was failing (now passing), full suite result, any regressions

This is a bug fix — no new features. Any new test failures are regressions and must be reported as FAIL.
```

If QA fails: return to Step 4 with the failure details. Retry up to 2 times.

### Lint Gate (after QA PASS)

Run lint using `{{lint_command}}` detected in repository recon. If `{{lint_command}}` was not detected, skip this gate and log the risk.

```
Agent(
  subagent_type = "claude-tech-squad:code-quality",
  team_name = "bug-fix-team",
  name = "code-quality",
  prompt = """
## Code Quality Lint Check

### Lint Command
{{lint_command}}

### Changed Files
{{changed_files}}

### Implementation Output
{{implementation_output}}

---
You are the Code Quality specialist. Run the lint command on changed files.
Return findings as a checklist. Flag any violations that would fail CI.
Do NOT fix — report only.
Do NOT chain to other agents.
"""
)
```

If lint violations found: return to Step 4 with violations list.

### Step 6 — Code Review

Invoke the Agent tool with `subagent_type: "claude-tech-squad:{{reviewer_agent}}"`, `team_name: "bug-fix-team"`, `name: "reviewer"`.

Prompt:
```
You are the Reviewer. Review a targeted bug fix.

Changed files: {{changed_files}}
Root cause: {{techlead_output}}
Fix description: {{fix_description}}

Focus:
1. Does the fix address the root cause (not just the symptom)?
2. Are there edge cases the fix misses?
3. Could the fix introduce regressions in adjacent functionality?
4. Is the fix minimal — no unnecessary refactoring?
5. Lint compliance and TDD compliance gates.

BLOCKER criteria (the ONLY reasons to output CHANGES REQUESTED):
- The fix does not address the root cause
- The fix introduces a crash, regression, or security hole
- A new unguarded exception path could leave shared state (e.g. a message list) in a broken state
- The failing test does not pass

NOT blockers — flag as LOW/NIT only, never as CHANGES REQUESTED:
- DRY violations or duplicated logic
- Helper extraction opportunities
- Variable renaming or reorganization
- Code style or "clean code" improvements
- Performance micro-optimizations

Output: APPROVED or CHANGES REQUESTED. If CHANGES REQUESTED, only list blocker-category findings.
```

If reviewer outputs CHANGES REQUESTED: apply ONLY the blocker findings. Do NOT apply LOW/NIT suggestions. Repeat Step 5–6 once more with the blocker fixes only.

### Step 6b — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-bug-fix-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: bug-fix
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [fix-implemented, reviewer-approved, tests-passed]
fallbacks_invoked: []
bug_description: {{one_line_summary}}
root_cause: {{root_cause}}
files_changed: [list]
test_written: {{test_name}}
test_result: PASS
lint_result: PASS | skipped
reviewer_result: APPROVED
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Fix Summary
{{one_paragraph}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 7 — Report to User

Produce a concise summary:

```markdown
## Bug Fix Summary

**Root Cause:** [one sentence]

**Fix Applied:**
- `path/to/file.py` — [one-line description]

**Test Evidence:**
- Test written: `test_name` in `tests/path/test_file.py`
- Previously: FAIL | Now: PASS
- Full suite: X passed, 0 failed

**Reviewer:** APPROVED

**Next steps:** Review the diff and commit when ready.
```
