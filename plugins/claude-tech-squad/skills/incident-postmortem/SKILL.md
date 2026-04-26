---
name: incident-postmortem
description: This skill should be used when a production incident has already happened and the team needs a structured post-mortem with timeline, root cause, contributing factors, 5-whys, and owned action items. Trigger with "post-mortem", "postmortem", "retrospectiva do incidente", "análise do incidente", "rca", "root cause analysis". NOT for live incident response (use /cloud-debug or /hotfix first).
user-invocable: true
---

# /incident-postmortem — Post-Mortem After Production Incidents

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

**PII Safety:** Incident logs, stack traces, and chat excerpts may contain emails, user IDs, tokens, or credentials. Before passing any artifact to agents: mask tokens (replace with `[REDACTED]`), mask email addresses, never include raw database credentials or API keys. Post-mortem documents written to `ai-docs/` must not contain raw PII.

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Structured blameless post-mortem workflow. Use after an incident has been resolved to learn what happened, why it happened, and how to prevent recurrence.

**Blameless principle:** This workflow focuses on systems and processes, not individuals. All outputs frame findings in terms of what failed, not who failed.

## When to Use

- After any production incident that caused user impact
- After a near-miss that could have caused impact
- After a `/hotfix` or `/cloud-debug` resolution
- When the user says: "post-mortem", "postmortem", "retrospectiva do incidente", "análise do incidente", "rca", "root cause analysis"

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

### Step 1 — Incident Intake Gate

Ask the user for (if not already provided):
1. **Incident summary**: What happened? (1–3 sentences)
2. **Impact**: Who was affected and how? (users, services, duration)
3. **Detection**: How was it detected? (alert, user report, monitoring)
4. **Resolution**: How was it resolved? (hotfix, rollback, config change)
5. **Timeline**: Any known timestamps? (start, detection, mitigation, resolution)

This is a blocking gate. Do NOT proceed until impact and resolution are provided.

### Step 2 — Gather evidence

Collect available artifacts:

```bash
# Recent commits around incident time
git log --oneline --since="{{incident_date}} -2 days" --until="{{incident_date}} +1 day" 2>/dev/null | head -30

# Recent deployments
gh run list --limit 10 --json createdAt,conclusion,workflowName,headCommit 2>/dev/null || echo "GH_NOT_AVAILABLE"

# Hotfix PRs if any
gh pr list --state merged --label hotfix --limit 5 --json number,title,mergedAt 2>/dev/null || echo "GH_NOT_AVAILABLE"
```

Also ask the user to paste any relevant:
- Error messages or stack traces
- Log excerpts
- Alert snapshots
- Chat messages from the incident channel

### Step 3 — Reconstruct timeline

From the evidence and user-provided timestamps, build a structured timeline:

```
Timeline:
HH:MM — [DEPLOY/CHANGE] Description of change that may have triggered incident
HH:MM — [FIRST IMPACT] First evidence of user-facing impact
HH:MM — [DETECTION] How and by whom incident was detected
HH:MM — [RESPONSE START] When the response team engaged
HH:MM — [DIAGNOSIS] Root cause identified
HH:MM — [MITIGATION] Impact reduced (partial fix, rollback, feature flag off)
HH:MM — [RESOLUTION] Full service restoration
HH:MM — [ALL-CLEAR] Monitoring confirmed stable
```

Total duration: detection-to-resolution = X minutes

### Step 4 — Spawn techlead for root cause analysis

Use TeamCreate to create a team named "incident-postmortem-team". Then spawn each agent using the Agent tool with `team_name="incident-postmortem-team"` and a descriptive `name` for each agent.

```
Agent(
  subagent_type = "claude-tech-squad:techlead",
  team_name = "incident-postmortem-team",
  name = "techlead-rca",
  prompt = """
## Post-Mortem Root Cause Analysis

### Incident Summary
{{incident_summary}}

### Timeline
{{reconstructed_timeline}}

### Evidence
{{evidence_artifacts}}

### Impact
{{impact_description}}

---
You are the Tech Lead conducting a blameless post-mortem root cause analysis.

Produce:
1. **Root Cause** — the single technical failure that directly caused the incident (1 sentence)
2. **Contributing Factors** — conditions that made the root cause possible or worse (3–7 items)
3. **5-Whys Analysis** — trace from symptom to root cause through 5 "why" questions
4. **Detection Gap** — why wasn't this caught before it reached users?
5. **Response Assessment** — what slowed down or sped up the response?

Frame everything blameless — focus on systems, processes, tooling, not individuals.
Do NOT chain to other agents.
"""
)
```

### Step 5 — Spawn SRE for reliability gap analysis

```
Agent(
  subagent_type = "claude-tech-squad:sre",
  team_name = "incident-postmortem-team",
  name = "sre",
  prompt = """
## Post-Mortem: Reliability Gap Analysis

### Root Cause
{{root_cause}}

### Contributing Factors
{{contributing_factors}}

### Current SLOs (if known)
{{slo_context}}

---
You are the SRE. Identify:
1. **Observability gaps** — what monitoring or alerting was missing or too slow?
2. **Resilience gaps** — what circuit breakers, retries, or fallbacks were absent?
3. **Runbook gaps** — was there a runbook? Was it accurate?
4. **SLO impact** — was an SLO breached? By how much?
5. **Reliability action items** — specific technical changes to prevent recurrence

Return prioritized action items (P1 = prevents recurrence, P2 = improves response time, P3 = reduces blast radius).
Do NOT chain.
"""
)
```

### Step 6 — Generate action items

Consolidate action items from both agents. For each item:
- Assign a priority: P1 (prevents recurrence) / P2 (improves detection) / P3 (reduces blast radius)
- Assign an owner role (e.g. backend-dev, devops, sre, observability-engineer)
- Set a suggested deadline (P1: this sprint, P2: next sprint, P3: backlog)

### Step 6b — Generate runbook from P1 action items (proactive)

After action items are consolidated, automatically generate an operational runbook for every P1 item. Do NOT ask — generate proactively.

For each P1 action item, spawn sre to produce the runbook step:

```
Agent(
  subagent_type = "claude-tech-squad:sre",
  team_name = "incident-postmortem-team",
  name = "sre-runbook",
  prompt = """
## Runbook Generation

### Incident
{{incident_summary}}

### P1 Action Item
{{p1_action_item}}

### Root Cause
{{root_cause}}

---
You are the SRE. Write an operational runbook section for this action item.
The runbook must be executable by an on-call engineer at 3am under stress.

Format:
## Runbook: {{action_item_title}}

**Trigger:** What symptom or alert fires this runbook
**Severity:** P1/P2/P3
**Expected resolution time:** N minutes

### Pre-conditions
- [ ] {{what_to_verify_before_starting}}

### Steps
1. {{specific_command_or_action}}
2. {{specific_command_or_action}}
3. Verify: {{how_to_confirm_resolution}}

### Rollback
{{how_to_undo_if_steps_make_things_worse}}

### Escalation
If unresolved after {{N}} minutes: escalate to {{role}}

Return the runbook section. Do NOT chain.
"""
)
```

Write all runbook sections to `ai-docs/runbook-{{service_slug}}.md` (append if file exists, create if not):

```markdown
# Operational Runbook — {{service_name}}

> Auto-generated from post-mortem {{incident_slug}}. Review and validate before relying in production.

{{runbook_sections}}
```

Emit: `[Runbook Generated] ai-docs/runbook-{{service_slug}}.md — N procedures added`

### Step 7 — Write post-mortem document

Write to `ai-docs/postmortem-{{YYYY-MM-DD}}-{{slug}}.md`:

```markdown
# Post-Mortem: {{incident_title}}

**Date:** {{incident_date}}
**Severity:** {{P1/P2/P3/P4}}
**Duration:** {{detection_to_resolution}} minutes
**Status:** Resolved

---

## Summary

{{2–3 sentence summary of what happened, impact, and how it was resolved}}

## Impact

- **Users affected:** {{estimate}}
- **Services affected:** {{list}}
- **Duration of user impact:** {{minutes}}
- **SLO breach:** {{yes/no — which SLO, by how much}}

## Timeline

| Time | Event |
|------|-------|
| {{HH:MM}} | {{event}} |

## Root Cause

{{root_cause_one_sentence}}

## Contributing Factors

1. {{factor_1}}
2. {{factor_2}}
3. ...

## 5-Whys

1. **Why** did users see errors? → {{answer}}
2. **Why** did that happen? → {{answer}}
3. **Why** did that happen? → {{answer}}
4. **Why** did that happen? → {{answer}}
5. **Why** did that happen? → **Root cause: {{root_cause}}**

## Detection

- Detected by: {{alert / user report / manual observation}}
- Time to detect: {{minutes from first impact}}
- Gap: {{what would have caught this faster}}

## Response

- Time to mitigate: {{minutes from detection}}
- Time to resolve: {{minutes from detection}}
- What worked well: {{list}}
- What slowed us down: {{list}}

## Action Items

| Priority | Action | Owner | Due |
|----------|--------|-------|-----|
| P1 | {{action}} | {{role}} | {{sprint}} |
| P2 | {{action}} | {{role}} | {{sprint}} |

## Lessons Learned

1. {{lesson_1}}
2. {{lesson_2}}

---
*Blameless post-mortem. Focus is on systems and processes.*
```

### Step 8 — Write SEP log (SEP Contrato 1)

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-incident-postmortem-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
parent_run_id: {{hotfix_run_id_if_known | null}}
skill: incident-postmortem
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [preflight-passed, timeline-built, postmortem-approved]
fallbacks_invoked: []
incident_date: {{date}}
incident_severity: P1 | P2 | P3 | P4
duration_minutes: N
action_items_p1: N
action_items_total: N
runbook_generated: true | false
postmortem_artifact: ai-docs/postmortem-{{date}}-{{slug}}.md
runbook_artifact: ai-docs/runbook-{{service_slug}}.md | null
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
Emit: `[Post-Mortem Written] ai-docs/postmortem-{{date}}-{{slug}}.md`

### Step 8b — Generate pending-implement tracker for P1 action items (mandatory)

If `action_items_p1 > 0`, immediately write a pending-implement tracker **without asking the user**:

```
Write to tasks/pending-implement-postmortem-{{date}}-{{slug}}.md:
# Pending Implementation: Post-Mortem P1 Actions — {{incident_title}}

**Post-Mortem:** ai-docs/postmortem-{{date}}-{{slug}}.md
**Incident date:** {{incident_date}}
**Severity:** {{P1/P2/P3/P4}}

## P1 Action Items (prevents recurrence — implement this sprint)

{{for each P1 action item:}}
- [ ] {{action}} — owner: {{role}} — due: {{sprint}}

## How to implement

For code changes: /implement pointing to this file as blueprint context
For infra changes: /squad with this file as context
For process changes: add to CLAUDE.md directly
```

Emit: `[P1 Tracker Written] tasks/pending-implement-postmortem-{{date}}-{{slug}}.md — {{N}} P1 items`

### Step 9 — Report to user

Tell the user:
- Root cause (1 sentence)
- Number of action items by priority (P1/P2/P3)
- Path to the post-mortem document
- Path to the P1 pending-implement tracker (if created)
- Suggest: open Jira tickets for P1 action items with `/claude-tech-squad:squad` or manually
- Suggest: schedule a team review of the post-mortem within 48 hours of incident resolution
