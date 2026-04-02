---
name: security-audit
description: Runs a full security audit on the project, detecting the stack (Python/JS), executing static analysis tools (bandit, pip-audit, npm audit), scanning for hardcoded secrets, and producing a structured severity report. Trigger with "auditar seguranca", "security audit", "checar vulnerabilidades", "scan de seguranca".
user-invocable: true
---

# /security-audit — Security Audit with Static Analysis

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
- Disable or bypass authentication/authorization as a workaround
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

**Additional constraint for security audit:** Findings containing CVEs, tokens, or credentials must be written only to `ai-docs/.squad-log/` (never to git-tracked files without redaction). Never echo raw secrets to terminal output.

Detects the project stack, runs real security analysis tools, scans for hardcoded secrets, and produces a structured report with findings categorized by severity.

## When to Use

- Periodic security maintenance
- Before releases or deployments
- After adding new dependencies
- When the user says: "auditar seguranca", "security audit", "checar vulnerabilidades", "scan de seguranca"

## Execution

Follow these steps exactly:

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

### Step 1 — Detect project stack

Read the following files to determine the project stack:

- `pyproject.toml`, `requirements.txt`, `Pipfile` — Python project
- `package.json`, `yarn.lock`, `pnpm-lock.yaml` — JavaScript/Node project

Record which stacks are present. A project can be both Python and JS.

### Step 2 — Run static analysis tools via Bash

Execute the appropriate tools based on the detected stack. Capture all output for later analysis.

**Python static analysis (if Python detected):**
```bash
bandit -r . --exclude .venv,node_modules,migrations,tests -f text 2>/dev/null || echo "TOOL_NOT_AVAILABLE: bandit"
```

**Python dependency vulnerabilities (if Python detected):**
```bash
pip-audit 2>/dev/null || safety check 2>/dev/null || echo "TOOL_NOT_AVAILABLE: pip-audit/safety"
```

**JavaScript audit (if JS detected):**
```bash
npm audit 2>/dev/null || echo "TOOL_NOT_AVAILABLE: npm audit"
```

**Secrets scan (always run):**

Use Grep to search for patterns that indicate hardcoded secrets:
- Patterns: `password\s*=\s*["'][^"']+["']`, `api_key\s*=\s*["']`, `secret\s*=\s*["']`, `token\s*=\s*["'][^"']+["']`, `AWS_SECRET_ACCESS_KEY`, `PRIVATE.KEY`
- Exclude: `.env.template`, `.env.example`, `*.md`, `node_modules/`, `.venv/`, `migrations/`, `tests/`, `*.pyc`

### Step 3 — Invoke security reviewer agent

Use TeamCreate to create a team named "security-audit-team". Then spawn the agent using the Agent tool with `team_name="security-audit-team"` and a descriptive `name`.

Use the Agent tool with `subagent_type: "claude-tech-squad:security-reviewer"`, `team_name: "security-audit-team"`, `name: "security-reviewer"`.

Prompt:
```
You are the Security Reviewer agent. Analyze the following security scan outputs and produce a structured assessment.

Project stack: {{detected_stack}}

Bandit output:
{{bandit_output}}

Dependency audit output:
{{dep_audit_output}}

npm audit output:
{{npm_audit_output}}

Secrets scan findings:
{{secrets_output}}

For each finding, classify severity as Critical / High / Medium / Low.
Include file:line references when available.
Identify false positives where obvious.
Recommend specific remediation for each finding.
```

### Step 4 — Produce structured report

Generate a markdown report with the following structure:

```markdown
# Security Audit Report — YYYY-MM-DD

## Summary
- Critical: N findings
- High: N findings
- Medium: N findings
- Low: N findings
- Tools executed: [list]
- Tools not available: [list]

## Critical Findings
### [Finding title]
- **File:** path/to/file:line
- **Tool:** bandit / pip-audit / npm audit / secrets scan
- **Description:** ...
- **Remediation:** ...

## High Findings
...

## Medium Findings
...

## Low Findings
...

## Recommendations
1. Immediate actions (Critical/High)
2. Short-term improvements (Medium)
3. Process improvements (tooling, CI integration)

## Tools Coverage
| Tool | Status | Findings |
|------|--------|----------|
```

### Step 4b — Write Remediation Tasks (SEP Contrato 2)

Immediately after producing the structured report, write a companion remediation tasks file.

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/security-remediation-YYYY-MM-DD.md`:

```markdown
# Security Remediation Tasks — YYYY-MM-DD

> Auto-generated by /security-audit. Check off items as they are fixed.
> Re-run /security-audit after completing Phase 1 to verify closure.

## Phase 1 — Immediate (Critical + High)
- [ ] [CRIT-1] {{finding_title}} — {{file}}:{{line}}
- [ ] [HIGH-1] {{finding_title}} — {{file}}:{{line}}

## Phase 2 — Short-term (Medium)
- [ ] [MED-1] {{finding_title}} — {{file}}:{{line}}

## Phase 3 — When Convenient (Low)
- [ ] [LOW-1] {{finding_title}} — {{file}}:{{line}}

## Audit Metadata
- Audit date: YYYY-MM-DD
- Full report: ai-docs/security-audit-YYYY-MM-DD.md
- Status: open
```

Also write the execution log:

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-security-audit-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: security-audit
timestamp: {{ISO8601}}
status: completed
findings_critical: N
findings_high: N
findings_medium: N
findings_low: N
remediation_artifact: ai-docs/security-remediation-YYYY-MM-DD.md
---

## Findings Gerados
{{list_critical_and_high_findings_one_line_each}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
Emit: `[Remediation Tasks Written] ai-docs/security-remediation-YYYY-MM-DD.md`

### Step 5 — Save report

Create the `ai-docs/` directory if it does not exist. Write the report to:
```
ai-docs/security-audit-YYYY-MM-DD.md
```

Use the current date for the filename.

### Step 6 — Report to user

Tell the user:
- Total findings by severity
- Top 3 most critical issues with file references
- Which tools ran successfully and which were not available
- Path to the saved report
