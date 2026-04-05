---
name: refactor
description: Safe, test-guarded incremental refactoring workflow. Writes characterization tests to lock current behavior, plans the refactor in small steps, implements incrementally, and verifies behavior is preserved at each step. Trigger with "refatorar", "refactor", "limpar código", "remover débito técnico", "reorganizar", "melhorar design".
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

Ask the user (if not already provided):
1. **Target**: What code needs to be refactored? (file, module, class, function)
2. **Goal**: What specific improvement? (extract class, rename, reduce coupling, improve testability, remove duplication)
3. **Constraint**: What must NOT change? (public API, external behavior, DB schema)
4. **Risk tolerance**: Is this in a hot path or critical service?

### Step 2 — Stack Command Detection

Read project files to detect test command before spawning any agent:

| Signal file | test command |
|---|---|
| `Makefile` with `test:` | `make test` |
| `package.json` scripts | `npm test` |
| `pyproject.toml` | `pytest` |
| `pom.xml` | `mvn test` |
| `build.gradle` | `./gradlew test` |

Store as `{{test_command}}`. CLAUDE.md overrides take priority.

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
  subagent_type = "claude-tech-squad:backend-dev",  # or frontend-dev
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

### Step 7 — Spawn reviewer for final review

After all steps complete:

```
Agent(
  subagent_type = "claude-tech-squad:reviewer",
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
