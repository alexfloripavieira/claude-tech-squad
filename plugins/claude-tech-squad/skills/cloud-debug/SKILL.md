---
name: cloud-debug
description: Debugs production or staging incidents by collecting logs, analyzing stack traces, evaluating blast radius, and producing a structured diagnosis with action plan. Trigger with "debug producao", "cloud debug", "investigar erro em producao", "incident", "sistema fora", "analisar logs".
user-invocable: true
---

# /cloud-debug — Production/Staging Incident Debug

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in production
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a workaround
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists
- Restart or kill production services without explicit user confirmation

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

**PII Safety:** Logs collected during debugging may contain emails, user IDs, tokens, or other PII. Before passing any log content to agents: strip or mask tokens (replace with `[REDACTED]`), mask email addresses in stack traces, and never log raw database credentials or API keys. Agents must not store PII in their responses.

Collects available logs, analyzes error patterns and stack traces, evaluates blast radius, and produces a structured diagnosis with prioritized action plan.

## When to Use

- Production or staging incidents
- Investigating errors reported by users
- Analyzing unexpected behavior in deployed environments
- When the user says: "debug producao", "cloud debug", "investigar erro em producao", "incident", "sistema fora", "analisar logs"

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

### Step 1 — Gather symptom description (mandatory gate)

Ask the user:
```
What is the observed symptom or error? Please provide:
1. What is happening (or not happening)?
2. When did it start (approximate time)?
3. Which environment (production / staging / homolog)?
4. Any error messages, URLs, or screenshots available?
```

Do NOT proceed until the user provides at least item 1. This is a blocking gate.

### Step 2 — Collect logs

Run the following log collection commands via Bash. Capture all output.

**Docker logs (if available):**
```bash
docker compose logs --tail=200 --no-color 2>/dev/null || echo "DOCKER_LOGS_NOT_AVAILABLE"
```

**Application-specific logs (if Docker available):**
```bash
docker compose logs --tail=200 --no-color django 2>/dev/null || echo "DJANGO_LOGS_NOT_AVAILABLE"
docker compose logs --tail=100 --no-color celery 2>/dev/null || echo "CELERY_LOGS_NOT_AVAILABLE"
docker compose logs --tail=100 --no-color frontend 2>/dev/null || echo "FRONTEND_LOGS_NOT_AVAILABLE"
```

**Local log files (search for common locations):**

Use Glob to find log files:
```
**/logs/*.log
**/log/*.log
**/*.log
```

Read the last 100 lines of any log files found.

### Step 3 — Extract error patterns

Use Grep to search collected logs and codebase for:
- Stack traces: `Traceback`, `Error`, `Exception`, `FATAL`, `CRITICAL`
- HTTP errors: `500`, `502`, `503`, `504`, `400`, `403`, `404`
- Connection issues: `ConnectionRefused`, `TimeoutError`, `ConnectionReset`
- Memory/resource issues: `MemoryError`, `OOM`, `killed`
- The specific error terms from the user's symptom description

### Step 4 — Invoke observability engineer agent

Use the Agent tool with `subagent_type: "claude-tech-squad:observability-engineer"`.

Prompt:
```
You are the Observability Engineer agent. Analyze the following logs and error patterns from a {{environment}} incident.

User-reported symptom:
{{symptom_description}}

Collected logs:
{{logs_summary}}

Error patterns found:
{{error_patterns}}

Produce:
1. Timeline of events based on log timestamps
2. Error classification (application / infrastructure / external dependency)
3. Correlation between different error signals
4. Metrics to check if monitoring is available (Grafana/Prometheus queries)
```

### Step 5 — Invoke SRE agent for blast radius

Use the Agent tool with `subagent_type: "claude-tech-squad:sre"`.

Prompt:
```
You are the SRE agent. Evaluate the blast radius and impact of this incident.

Symptom: {{symptom_description}}
Observability analysis: {{observability_output}}

Evaluate:
1. Which services/users are affected?
2. Is the issue isolated or spreading?
3. Current severity level (SEV1-4)
4. Is immediate mitigation needed (rollback, restart, scale)?
5. Communication needs (stakeholders to notify)
```

### Step 6 — Invoke tech lead for fix proposal

Use the Agent tool with `subagent_type: "claude-tech-squad:techlead"`.

Prompt:
```
You are the Tech Lead agent. Propose a fix and action plan for this incident.

Symptom: {{symptom_description}}
Observability analysis: {{observability_output}}
SRE assessment: {{sre_output}}

Produce:
1. Root cause hypothesis (ranked by likelihood)
2. Immediate fix (to stop the bleeding)
3. Short-term fix (proper solution)
4. Long-term fix (prevent recurrence)
5. Specific code changes or configuration needed
6. Verification steps to confirm the fix works
```

### Step 7 — Produce diagnosis report

Present to the user:

```markdown
# Incident Diagnosis

## Symptom
{{user_description}}

## Root Cause Hypothesis
1. [Most likely] ...
2. [Possible] ...

## Blast Radius
- **Severity:** SEV-N
- **Affected services:** ...
- **Affected users:** ...

## Action Plan

### Immediate (do now)
1. ...

### Short-term (next hours/day)
1. ...

### Long-term (prevent recurrence)
1. ...

## Verification Steps
1. ...

## Evidence
- Relevant log excerpts
- Error patterns found
- Timeline of events
```

Do NOT save this report to a file automatically. Present it directly to the user for immediate action. Offer to save it if the user wants a record.
