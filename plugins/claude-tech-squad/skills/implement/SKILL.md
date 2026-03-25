---
name: implement
description: Run build and quality for any software project based on a prior discovery document. Supports a full specialist bench across implementation, quality, operations, and delivery artifacts.
---

# /implement — Build & Quality

Run implementation and quality validation using the Discovery & Blueprint Document produced by `/discovery`.
Each specialist runs as an independent teammate in its own tmux pane.

## Global Safety Contract

**This contract applies to every teammate spawned by this workflow. Violating it requires explicit written user confirmation.**

No teammate may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in production
- Run `tsuru app-remove`, `heroku apps:destroy`, or any equivalent application deletion command
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a workaround
- Deploy to production without a documented and tested rollback plan
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists
- Deploy to production before staging has been successfully deployed and verified

If any teammate believes a task requires one of these actions, it must STOP and surface the decision to the user before proceeding. The urgency of an implementation deadline does not override this contract.

## TDD Execution Rule

If the discovery package came from `/squad`, or if the package explicitly marks TDD as required, treat TDD as mandatory:

- Implementation starts from failing tests, not from direct production code edits
- The TDD Delivery Plan becomes the default execution sequence
- Exceptions must be stated explicitly

## Teammate Architecture

This workflow creates a team and spawns each specialist as a real teammate (separate tmux pane). Use the following tool sequence:

1. `TeamCreate` — create the implementation team
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist as a teammate
3. `SendMessage` — communicate with running teammates
4. `TaskCreate` + `TaskUpdate` — assign and track work per teammate

**Do NOT use Agent without team_name** — that runs an inline subagent, not a visible teammate pane.

## Operator Visibility Contract

Emit these lines for every teammate action:

- `[Team Created] <team-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <review or validation failure>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`

---

## Required Input

This command expects a Discovery & Blueprint Document (from `/discovery` or `/squad`).
If not available, ask the user to run `/discovery` first or paste the blueprint.

---

## Execution

### Step 0 — Stack Command Detection (SEP Stack-Agnostic)

Before any teammate is spawned, detect the project's real commands. Read the following files (whichever exist) and extract the canonical commands:

| Signal file | test command | migrate command | lint command | build command |
|---|---|---|---|---|
| `Makefile` with `test:` target | `make test` | detect from targets | `make lint` | `make build` |
| `package.json` scripts | `npm test` or `npm run test` | n/a | `npm run lint` | `npm run build` |
| `pyproject.toml` with pytest | `pytest` | n/a | `ruff check .` | n/a |
| `pom.xml` | `mvn test` | `mvn flyway:migrate` | `mvn checkstyle:check` | `mvn package` |
| `build.gradle` | `./gradlew test` | n/a | `./gradlew lint` | `./gradlew build` |

Store as `{{project_commands}}` and inject into every implementation agent prompt. No agent should ever infer commands — they always receive the detected commands.

If a `CLAUDE.md` exists, read its commands block and use those values, which override all detected values above.

### Step 1 — Validate Blueprint

Confirm the Discovery & Blueprint Document is present.
If missing, stop and ask the user to provide it.

### Step 2 — Create Implementation Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "implement"
- `description`: "Implementation run for: {{feature_or_task_one_line}}"

Emit: `[Team Created] implement`

### Step 3 — TDD Specialist Teammate (Failing Tests First)

Spawn TDD Specialist to produce the first failing tests before any production code:

```
Agent(
  team_name = <team>,
  name = "tdd-specialist",
  subagent_type = "claude-tech-squad:tdd-specialist",
  prompt = """
## TDD — First Failing Tests

### TDD Delivery Plan
{{tdd_delivery_plan}}

### Test Plan
{{test_plan}}

### Architecture
{{architecture}}

---
You are the TDD Specialist. Write the first failing tests for the first delivery slice.
Use red-green-refactor cycles. Write tests using the repository's real test stack.
Do NOT write production code — only the failing tests.
Return the failing test files and run instructions.
"""
)
```

Emit: `[Teammate Spawned] tdd-specialist | pane: tdd-specialist`

Wait for TDD Specialist to complete. Confirm failing tests are in place before proceeding.

### Step 4 — Implementation Batch (Parallel)

Spawn implementation agents in parallel based on the TechLead's workstream plan.
Only spawn agents for workstreams that apply to this task.

```
# Spawn all relevant implementation agents in parallel
Agent(team_name=<team>, name="backend-dev",  subagent_type="claude-tech-squad:backend-dev",  prompt=...)
Agent(team_name=<team>, name="frontend-dev", subagent_type="claude-tech-squad:frontend-dev", prompt=...)
Agent(team_name=<team>, name="platform-dev", subagent_type="claude-tech-squad:platform-dev", prompt=...)
```

Emit: `[Batch Spawned] implementation | Teammates: <list>`

Each implementation agent prompt must include:
- TechLead execution plan (their specific workstream)
- Architecture decisions
- Failing test files from TDD Specialist
- Relevant specialist notes (backend-arch, frontend-arch, api-designer, etc.)
- Design principles guardrails
- Project commands: `{{project_commands}}` — use these exact commands, never infer
- Instruction: "Implement until the failing tests pass. Follow TDD. When done, return a summary of files changed and test results. Do NOT chain to other agents."

**SEP Contrato 4 — Task Status Protocol:**
Each implementation agent must also:
1. Before starting: confirm which task slice it is implementing
2. After completing: verify `{{test_command}}` passes
3. Return a structured completion block:
```
## Completion Block
- Task: {{task_name}}
- Status: completed
- Files changed: [list]
- Tests run: {{test_command}} → PASS/FAIL
- Test count: N passed, M failed
```
The orchestrator uses this block to track which tasks are done before spawning Reviewer.

Wait for all implementation teammates to complete.

### Step 5 — Reviewer Teammate

Spawn Reviewer with implementation output:

```
Agent(
  team_name = <team>,
  name = "reviewer",
  subagent_type = "claude-tech-squad:reviewer",
  prompt = """
## Code Review

### Files Changed
{{implementation_batch_output}}

### Architecture and Design Guardrails
{{architecture_and_design_principles}}

### Test Plan
{{test_plan}}

---
You are the Reviewer. Review for correctness, simplicity, maintainability,
TDD compliance, lint compliance, and documentation compliance.
Flag bugs, regressions, missing tests, and unnecessary complexity.
Return: APPROVED or CHANGES REQUESTED with specific items.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] reviewer | pane: reviewer`

If reviewer returns CHANGES REQUESTED:
- Emit: `[Teammate Retry] <impl-agent> | Reason: <review item>`
- Spawn the relevant implementation agent again with the review feedback
- Repeat Step 5 until APPROVED

### Step 6 — QA Teammate

Spawn QA after reviewer approval:

```
Agent(
  team_name = <team>,
  name = "qa",
  subagent_type = "claude-tech-squad:qa",
  prompt = """
## QA Validation

### Implementation Output
{{approved_implementation}}

### Acceptance Criteria
{{acceptance_criteria}}

### Test Plan
{{test_plan}}

---
You are QA. Run real test commands against the implementation.
Validate all acceptance criteria. Check for regressions.
Return: PASS or FAIL with detailed failure diagnosis.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] qa | pane: qa`

If QA returns FAIL:
- Emit: `[Teammate Retry] <impl-agent> | Reason: <qa failure>`
- Spawn the relevant implementation agent with QA failure details
- Repeat Steps 5–6 until QA PASS

### Step 7 — Quality Bench (Parallel)

After QA PASS, spawn quality specialist reviewers in parallel:

```
Agent(team_name=<team>, name="security-rev",  subagent_type="claude-tech-squad:security-reviewer",      prompt=...)
Agent(team_name=<team>, name="privacy-rev",   subagent_type="claude-tech-squad:privacy-reviewer",       prompt=...)
Agent(team_name=<team>, name="perf-eng",      subagent_type="claude-tech-squad:performance-engineer",   prompt=...)
Agent(team_name=<team>, name="access-rev",    subagent_type="claude-tech-squad:accessibility-reviewer", prompt=...)
Agent(team_name=<team>, name="integ-qa",      subagent_type="claude-tech-squad:integration-qa",         prompt=...)
```

Emit: `[Batch Spawned] quality-bench | Teammates: <list>`

Only spawn reviewers relevant to this project. Each receives the full implementation output.
Instruction per reviewer: "Review from your specialist lens. Return findings as a checklist. Do NOT chain."

**Load test agent (conditional):** Spawn if the implementation adds or modifies HTTP endpoints, message queues, batch jobs, or any operation that processes variable input volume:

```
Agent(team_name=<team>, name="load-test", subagent_type="claude-tech-squad:performance-engineer",
  prompt="""
## Load Test Plan

### New/Modified Endpoints
{{endpoints_or_operations}}

### Current baseline (if known)
{{existing_throughput_or_latency_slos}}

---
You are the Performance Engineer. Produce a load test plan for these endpoints:
1. Baseline test: expected normal load (target RPS/concurrent users)
2. Stress test: 3x normal load — what breaks first?
3. Spike test: sudden 10x burst — does it recover?
4. Identify: slowest query, highest memory operation, bottleneck under load
5. Acceptance criteria: p99 latency < Xms, error rate < 0.1% at normal load

If load testing tools are available (k6, locust, Artillery, JMeter), provide ready-to-run scripts.
Return findings as a checklist. Do NOT chain.
""")
```

### Step 8 — Docs Writer Teammate

Spawn Docs Writer with the complete delivery package:

```
Agent(
  team_name = <team>,
  name = "docs-writer",
  subagent_type = "claude-tech-squad:docs-writer",
  prompt = """
## Documentation Update

### Implementation Output
{{approved_implementation}}

### Architecture Decisions
{{architecture}}

### Quality Review Findings
{{quality_bench_output}}

---
You are the Docs Writer. Update technical docs, migration notes, operator guidance,
changelog inputs, and developer-facing usage notes for this change.
Return a documentation delta or updated files.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] docs-writer | pane: docs-writer`

### Step 9 — Jira/Confluence Teammate

Spawn Jira/Confluence Specialist:

```
Agent(
  team_name = <team>,
  name = "jira-confluence",
  subagent_type = "claude-tech-squad:jira-confluence-specialist",
  prompt = """
## Jira and Confluence Update

### Delivery Package
{{full_implementation_summary}}

### Documentation Delta
{{docs_writer_output}}

---
You are the Jira/Confluence Specialist. Update Jira tickets and Confluence pages
for this delivery. Create subtasks, add comments, update status, and publish
documentation as appropriate.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] jira-confluence | pane: jira-confluence`

### Step 9b — Coverage Gate

Before spawning PM for UAT, check test coverage delta.

```bash
# Detect coverage tool from project stack
# Python
coverage report --fail-under=0 2>/dev/null || pytest --cov --cov-report=term-missing 2>/dev/null || echo "COVERAGE_NOT_AVAILABLE"
# JS
npx nyc report --reporter=text 2>/dev/null || npx vitest run --coverage 2>/dev/null || echo "COVERAGE_NOT_AVAILABLE"
```

If coverage data is available:
- Compute delta: coverage after implementation vs coverage reported in blueprint (if present) or vs current `main`
- If delta < 0 (coverage dropped): emit `[Gate] Coverage Drop | Waiting for user input` and present:

```
Coverage dropped: {{before}}% → {{after}}% (delta: {{delta}}%)

Affected files without new test coverage:
{{uncovered_files}}

Options:
- [C] Continue to UAT anyway
- [T] Add tests first (re-runs QA after)
```

Block UAT until user decides. If [T]: spawn QA again with coverage gap as context.
If coverage tool is not available or delta >= 0: proceed silently.

### Step 10 — PM UAT Gate

Spawn PM for UAT validation:

```
Agent(
  team_name = <team>,
  name = "pm-uat",
  subagent_type = "claude-tech-squad:pm",
  prompt = """
## UAT Validation

### Original Acceptance Criteria
{{acceptance_criteria}}

### Implementation Evidence
{{qa_output}}

### Quality Reviews
{{quality_bench_output}}

---
You are the PM performing UAT. Validate that each acceptance criterion has concrete
evidence of fulfillment from the QA and implementation output.
Return: APPROVED or REJECTED with specific gaps.
"""
)
```

Emit: `[Teammate Spawned] pm-uat | pane: pm-uat`
Emit: `[Gate] UAT | Waiting for user input`

Present PM UAT output to user.

**If PM returns REJECTED:**

Do NOT end the workflow. Extract the specific gaps from PM output and present to the user:

```
UAT REJECTED — PM identified the following gaps:
1. {{gap_1}}
2. {{gap_2}}

Options:
- [R] Re-queue: fix the gaps and re-run UAT
- [S] Skip: mark as REJECTED and close the run
```

If user chooses [R]:
- Emit: `[Teammate Retry] pm-uat | Reason: UAT REJECTED — re-queuing implementation`
- Increment `retry_count`
- Spawn the relevant implementation agents with the rejection gaps as context (same format as Step 4, prepend `## UAT Rejection Feedback\n{{gaps}}` to the prompt)
- After fixes, re-run Steps 5–10 (review → QA → quality bench → docs → UAT)

Implementation is complete when user approves UAT or chooses [S].

### Step 11 — Write Execution Log (SEP Contrato 1)

After UAT gate resolves, write the structured execution log.

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-implement-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
parent_run_id: {{discovery_run_id_if_known | null}}
skill: implement
timestamp: {{ISO8601}}
status: completed | failed
feature_slug: {{feature_slug}}
blueprint_source: {{blueprint_path}}
gates_cleared: [tdd, review, qa, coverage, uat]
gates_blocked: []
retry_count: {{total_reviewer_and_qa_retries}}
load_test_run: true | false | skipped
teammates: [tdd-specialist, backend-dev?, frontend-dev?, reviewer, qa, security-rev?, docs-writer, jira-confluence, pm-uat]
uat_result: APPROVED | REJECTED
---

## Output Digest
{{one_paragraph_summary_of_what_was_implemented}}

## Completion Blocks
{{aggregated_completion_blocks_from_all_implementation_agents}}

## Findings Gerados
{{list_of_findings_from_quality_bench_if_any}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

---

## Output: Implementation Report

```
## Implementation Complete

### Agent Execution Log
- Team: implement
- Teammate: tdd-specialist | Status: completed | Output: failing tests written
- Batch: implementation | Teammates: [...] | Status: completed
- Teammate: reviewer | Status: APPROVED
- Teammate: qa | Status: PASS
- Batch: quality-bench | Teammates: [...] | Status: completed
- Teammate: docs-writer | Status: completed
- Teammate: jira-confluence | Status: completed
- Teammate: pm-uat | Status: [APPROVED/REJECTED]

### Build
- Workstreams executed: [...]
- Files changed: [...]
- TDD cycle: completed
- Review: APPROVED
- QA: PASS

### Quality
- Security: [summary]
- Privacy: [summary]
- Performance: [summary]
- Accessibility: [summary]
- Integration QA: [summary]
- Documentation: updated
- Jira / Confluence: updated
- UAT: [APPROVED/REJECTED]

### Evidence
- Tests run: [...]
- Acceptance criteria validated: [...]
- Outstanding issues: [...]
```
