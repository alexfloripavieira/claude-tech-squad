---
name: bug-fix
description: Focused bug resolution workflow. Takes a bug report (error message, stack trace, reproduction steps), investigates root cause, writes a failing test that proves the bug, implements the fix, and validates with real tool execution. Trigger with "corrigir bug", "fix bug", "investigar erro", "resolver issue", "bug fix".
user-invocable: true
---

# /bug-fix — Focused Bug Resolution

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

### Step 1 — Bug Intake Gate

Ask the user for:
1. **Symptom**: What is the observed behavior? (error message, stack trace, screenshot)
2. **Expected**: What should happen instead?
3. **Reproduction**: Steps or code to reproduce
4. **Context**: Environment (dev/staging/prod), recent changes if known

Do not proceed until you have at least symptom + expected behavior.

### Step 2 — Root Cause Analysis

Invoke the Agent tool with `subagent_type: "claude-tech-squad:techlead"`.

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
```

If techlead outputs ESCALATE: stop and tell the user to use `/squad` instead.

### Step 3 — Write Failing Test

Invoke the Agent tool with `subagent_type: "claude-tech-squad:tdd-specialist"`.

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
Invoke `subagent_type: "claude-tech-squad:backend-dev"`.

**If the bug is in frontend/UI code:**
Invoke `subagent_type: "claude-tech-squad:frontend-dev"`.

**If the bug spans both:**
Invoke both agents sequentially — backend first, then frontend.

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

Output: list of changed files with a one-line description of each change.
```

### Step 5 — Validate Fix (Real Tool Execution)

Invoke the Agent tool with `subagent_type: "claude-tech-squad:qa"`.

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

### Step 6 — Code Review

Invoke the Agent tool with `subagent_type: "claude-tech-squad:reviewer"`.

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

Output: APPROVED or CHANGES REQUESTED with specific comments.
```

If reviewer requests changes: apply them and repeat Step 5–6 once more.

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
