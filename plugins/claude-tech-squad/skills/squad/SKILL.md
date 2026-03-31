---
name: squad
description: Run the full technology squad workflow end-to-end with the full specialist bench: discovery, blueprint, design-principles and TDD-first implementation, quality, documentation, Jira/Confluence, reliability, and release preparation.
---

# /squad — Full Technology Squad

Run the complete end-to-end workflow. Every specialist runs as an independent teammate in its own tmux pane. This is the full pipeline: discovery → blueprint → implementation → quality → docs → release.

## Global Safety Contract

**This contract applies to every teammate spawned by this workflow. It covers all phases: discovery, implementation, and release. Violating it requires explicit written user confirmation.**

No teammate may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues, Kafka topics) in production
- Run `tsuru app-remove`, `heroku apps:destroy`, or any equivalent application deletion command
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a workaround
- Deploy to production without a documented and tested rollback plan
- Disable SLO alerting or monitoring as a way to proceed faster
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists
- Deploy to production before staging has been successfully deployed and verified
- Create a version tag or cut a release when CI is FAILING

If any teammate believes a task requires one of these actions, it must STOP immediately and surface the decision to the user before proceeding. **The urgency of a deadline, incident, or business pressure does not override this contract.**

## Core Principle

Do not assume the stack, the conventions, or the product domain. Discover them from the repository and validate technical decisions against current documentation via context7.

## TDD Default Mode

When `/squad` is used for code changes, TDD is the default strategy:

- Do not start implementation before the Test Plan and TDD Delivery Plan are ready
- Implementation agents begin from failing tests
- Use red-green-refactor cycles as the normal execution model

TDD may be relaxed only when:
- The task is documentation-only or release-only
- The repository genuinely has no viable automated test path
- An external constraint makes tests-first impossible for a specific step

If TDD is relaxed, state so explicitly and explain why.

## Teammate Architecture

This workflow creates a single team that persists across all phases. Use the following tool sequence:

1. `TeamCreate` — create the squad team (once, at start)
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist as a teammate
3. `SendMessage` — communicate with running teammates
4. `TaskCreate` + `TaskUpdate` — assign and track work per teammate

**Do NOT use Agent without team_name** — that runs an inline subagent, not a visible teammate pane.

## Operator Visibility Contract

Emit these lines for every teammate action:

- `[Team Created] <team-name>`
- `[Phase Start] <phase-name>`
- `[Teammate Spawned] <role> | pane: <name>`
- `[Teammate Done] <role> | Output: <one-line summary>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Gate] <gate-name> | Waiting for user input`
- `[Batch Spawned] <phase> | Teammates: <comma-separated names>`
- `[Phase Done] <phase-name> | Outcome: <summary>`

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

---

## Execution

### Step 1 — Repository Recon

Read the following files to understand the project:
- README.md, CLAUDE.md, package.json, pyproject.toml, requirements.txt
- List the main directories and identify the tech stack
- Note any existing architecture patterns, conventions, or constraints

**LLM/AI detection (automatic):**

```bash
# Detect AI/LLM usage in the project
grep -rl "openai\|anthropic\|langchain\|llamaindex\|llama_index\|cohere\|huggingface\|transformers\|openai\|chromadb\|pinecone\|weaviate\|pgvector\|faiss\|qdrant" \
  --include="*.py" --include="*.ts" --include="*.js" --include="*.json" \
  --exclude-dir=node_modules --exclude-dir=.venv . 2>/dev/null | head -20

# Detect prompt files
find . -name "*.prompt" -o -name "*system_prompt*" -o -path "*/prompts/*" 2>/dev/null | grep -v node_modules | head -10

# Detect RAG patterns
grep -rl "embedding\|vector_store\|similarity_search\|retriev" \
  --include="*.py" --include="*.ts" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=.venv . 2>/dev/null | head -10

# Detect agent/tool use patterns
grep -rl "tool_call\|function_call\|agent_executor\|AgentExecutor\|tool_use" \
  --include="*.py" --include="*.ts" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=.venv . 2>/dev/null | head -10
```

Default: `ai_feature: false`. If any of the above grep commands returns results, set `ai_feature: true` and activate the **LLM-enhanced bench** in Phase 1 and Phase 2. Emit: `[AI Detected] LLM/AI features found — activating AI specialist bench`
If grep returns no results and detection is ambiguous: emit `[Gate] AI Detection Ambiguous` and ask user: 'Does this task involve LLM/AI features? [Y]es / [N]o'

### Step 2 — Create Squad Team

Call `TeamCreate` (fetch schema via ToolSearch if needed):
- `name`: "squad"
- `description`: "Full squad run for: {{user_request_one_line}}"

Emit: `[Team Created] squad`

---

### PHASE 1: DISCOVERY

Emit: `[Phase Start] discovery`

Follow the same teammate sequence as `/discovery` Steps 3–13:

**Sequential chain with gates:**
1. Spawn `pm` → **Gate 1: Product Definition**
2. Spawn `business-analyst` with PM output
3. Spawn `po` → **Gate 2: Scope Validation**
4. Spawn `planner` → **Gate 3: Technical Tradeoffs**
5. Spawn `architect`
6. Spawn `techlead` → **Gate 4: Architecture Direction**
7. Spawn specialist batch in parallel (from TechLead list)
   - If `ai_feature: true`: add `ai-engineer`, `rag-engineer` (if RAG detected), `prompt-engineer` to this batch
8. Spawn quality baseline batch in parallel
9. Spawn `design-principles`
10. Spawn `test-planner`
11. Spawn `tdd-specialist` → **Gate 5: Blueprint Confirmation**
12. If `ai_feature: true`: Spawn `llm-eval-specialist` for eval plan (after blueprint) — no gate, automatic
13. If `ai_feature: true`: Spawn `llm-safety-reviewer` for threat model (after blueprint) — no gate, automatic

Each spawn: `Agent(team_name=<squad-team>, name=<role>, subagent_type="claude-tech-squad:<subagent>", prompt=...)`

**Phase 1 explicit subagent_type mappings** (name → subagent_type):
- `pm` → `pm`
- `business-analyst` → `business-analyst`
- `po` → `po`
- `planner` → `planner`
- `architect` → `architect`
- `techlead` → `techlead`
- `design-principles` → `design-principles-specialist`
- `test-planner` → `test-planner`
- `tdd-specialist` → `tdd-specialist`
- `llm-eval-specialist` → `llm-eval-specialist`
- `llm-safety-reviewer` → `llm-safety-reviewer`

All agents receive the full accumulated context from prior teammates.
All agents end with: "Do NOT chain to other agents — the orchestrator handles sequencing."

Emit: `[Phase Done] discovery | Blueprint confirmed`

---

### PHASE 2: IMPLEMENTATION

Emit: `[Phase Start] implementation`

**Sequential with parallel batches:**

1. Spawn `tdd-impl` (subagent_type: `tdd-specialist`) — write first failing tests
2. Spawn implementation batch in parallel:
   - `backend-dev`, `frontend-dev`, `platform-dev` (only relevant ones)
3. Spawn `reviewer` — review implementation
   - If CHANGES REQUESTED: retry relevant impl agent(s) — **max 3 review cycles**
   - After 3rd CHANGES REQUESTED: emit `[Gate] Review Limit Reached` and surface to user: `[A]ccept as-is / [S]kip review / [X]Abort`
4. Spawn `qa` — run real tests against implementation
   - If FAIL: retry relevant impl agent(s), then re-review and re-qa — **max 2 QA cycles**
   - After 2nd FAIL: emit `[Gate] QA Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`
5. Spawn `techlead-audit` (subagent_type: `techlead`) → **Conformance Gate**: verifica workstreams cobertos, conformidade arquitetural, TDD compliance e rastreabilidade de requisitos
   - If NON-CONFORMANT: retry impl agent(s) for each gap, then re-run reviewer → QA → techlead-audit — **max 2 conformance cycles**
   - After 2nd NON-CONFORMANT: emit `[Gate] Conformance Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`
6. Spawn quality bench in parallel (after Conformance CONFORMANT):
   - `security-rev` (subagent_type: `security-reviewer`), `privacy-rev` (subagent_type: `privacy-reviewer`), `perf-eng` (subagent_type: `performance-engineer`), `access-rev` (subagent_type: `accessibility-reviewer`), `integ-qa` (subagent_type: `integration-qa`), `code-quality` (subagent_type: `code-quality`)
   - If `ai_feature: true`: add `llm-safety-reviewer` to quality bench (prompt injection + tool authorization review)
   - If `ai_feature: true`: spawn `llm-eval-specialist` for eval gate (runs `/llm-eval` inline) — if eval score REGRESSED, present to user before UAT
   - **After all bench agents return**, classify findings by severity:
     - **BLOCKING** (must fix): security vulns, PII/data leaks, privacy violations, CI-breaking lint errors, WCAG A/AA failures
     - **WARNING** (should fix): perf regressions, non-critical accessibility, integration risks, code quality debt
   - If BLOCKING issues: emit `[Gate] Quality Bench Blocking Issues | N findings`, spawn the relevant impl agent(s) to fix, re-run only the agents that flagged issues — **max 2 fix cycles**
   - If blocking persists after 2 cycles: emit `[Gate] Quality Bench Unresolved` → surface `[A]ccept with known issues / [X]Abort`
   - If only WARNINGS: surface summary → `[A]ccept and advance / [F]ix before advancing`
7. Spawn `docs-writer`
8. Spawn `jira-confluence` (subagent_type: `jira-confluence-specialist`)
9. Spawn `pm-uat` (subagent_type: `pm`) → **Gate 6: UAT Approval**
   - If REJECTED: fix gaps and re-run reviewer → QA → techlead-audit → quality bench → UAT — **max 2 UAT cycles**
   - After 2nd REJECTION: emit `[Gate] UAT Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`

**Phase 2 explicit subagent_type mappings** (name → subagent_type):
- `tdd-impl` → `tdd-specialist`
- `backend-dev` → `backend-dev`
- `frontend-dev` → `frontend-dev`
- `platform-dev` → `platform-dev`
- `reviewer` → `reviewer`
- `qa` → `qa`
- `techlead-audit` → `techlead`
- `security-rev` → `security-reviewer`
- `privacy-rev` → `privacy-reviewer`
- `perf-eng` → `performance-engineer`
- `access-rev` → `accessibility-reviewer`
- `integ-qa` → `integration-qa`
- `code-quality` → `code-quality`
- `docs-writer` → `docs-writer`
- `jira-confluence` → `jira-confluence-specialist`
- `pm-uat` → `pm`

Each spawn: `Agent(team_name=<squad-team>, name=<name>, subagent_type="claude-tech-squad:<subagent>", prompt=...)`

Emit: `[Phase Done] implementation | UAT approved`

---

### PHASE 3: RELEASE

Emit: `[Phase Start] release`

After UAT approval, spawn Release and SRE:

**Release Teammate:**

```
Agent(
  team_name = <team>,
  name = "release",
  subagent_type = "claude-tech-squad:release",
  prompt = """
## Release Preparation

### Full Delivery Package
{{complete_implementation_summary}}

### UAT Result
{{pm_uat_output}}

### Architecture and Breaking Changes
{{architect_output}}

---
You are the Release specialist. Inventory all changes, validate CI/CD and deploy
assumptions, define rollback steps, and identify required communication and monitoring.
Return a release checklist with go/no-go recommendation.
"""
)
```

Emit: `[Teammate Spawned] release | pane: release`

**SRE Teammate (after Release):**

```
Agent(
  team_name = <team>,
  name = "sre",
  subagent_type = "claude-tech-squad:sre",
  prompt = """
## SRE Sign-off

### Release Plan
{{release_output}}

### Architecture
{{architect_output}}

---
You are the SRE specialist. Assess blast radius, SLO impact, rollback readiness,
and canary/phased rollout strategy. Return a final go/no-go recommendation.
"""
)
```

Emit: `[Teammate Spawned] sre | pane: sre`
Emit: `[Phase Done] release | SRE sign-off received`

---

## Final Output

```
## Squad Complete

### Agent Execution Log
- Team: squad
- Phase: discovery
  - Teammate: pm | Status: completed
  - Teammate: business-analyst | Status: completed
  - Teammate: po | Status: completed (Gate 2 passed)
  - Teammate: planner | Status: completed (Gate 3 passed)
  - Teammate: architect | Status: completed
  - Teammate: techlead | Status: completed (Gate 4 passed)
  - Batch: specialist-bench | Teammates: [...] | Status: completed
  - Batch: quality-baseline | Teammates: [...] | Status: completed
  - Teammate: design-principles | Status: completed
  - Teammate: test-planner | Status: completed
  - Teammate: tdd-specialist | Status: completed (Gate 5 passed)
- Phase: implementation
  - Teammate: tdd-impl | Status: failing tests written
  - Batch: implementation | Teammates: [...] | Status: completed
  - Teammate: reviewer | Status: APPROVED
  - Teammate: qa | Status: PASS
  - Teammate: techlead-audit | Status: CONFORMANT
  - Batch: quality-bench | Teammates: [..., code-quality] | Status: completed
  - Teammate: docs-writer | Status: completed
  - Teammate: jira-confluence | Status: completed
  - Teammate: pm-uat | Status: APPROVED (Gate 6 passed)
- Phase: release
  - Teammate: release | Status: completed
  - Teammate: sre | Status: GO

### Product
- User story: [...]
- Acceptance criteria: [...]
- Release slice: [...]

### Architecture
- Overall design: [...]
- Tech lead plan: completed
- Specialist notes: [summary]
- Design guardrails: completed
- Quality baselines: completed
- Test plan: completed
- TDD delivery plan: completed

### Delivery
- Workstreams executed: [...]
- Delivery mode: TDD-first / exception declared
- Review: APPROVED
- QA: PASS
- Specialist reviews: [summary]
- Docs: updated
- Jira / Confluence: updated
- UAT: APPROVED

### Release
- Release plan: completed
- SRE sign-off: GO
- Breaking changes: [...]
- Rollback plan: defined

### Stack Validation
- Docs checked via context7 for: [...]
```
