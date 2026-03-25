---
name: incident-postmortem
description: Structured post-mortem workflow after a production incident. Reconstructs timeline, identifies root cause and contributing factors, runs 5-whys analysis, produces action items with owners, and generates a post-mortem document ready to share with the team. Trigger with "post-mortem", "postmortem", "retrospectiva do incidente", "análise do incidente", "rca", "root cause analysis".
user-invocable: true
---

# /incident-postmortem — Post-Mortem After Production Incidents

Structured blameless post-mortem workflow. Use after an incident has been resolved to learn what happened, why it happened, and how to prevent recurrence.

**Blameless principle:** This workflow focuses on systems and processes, not individuals. All outputs frame findings in terms of what failed, not who failed.

## When to Use

- After any production incident that caused user impact
- After a near-miss that could have caused impact
- After a `/hotfix` or `/cloud-debug` resolution
- When the user says: "post-mortem", "postmortem", "retrospectiva do incidente", "análise do incidente", "rca", "root cause analysis"

## Execution

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

### Step 4 — Spawn incident-manager for root cause analysis

```
Agent(
  subagent_type = "claude-tech-squad:incident-manager",
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
You are the Incident Manager conducting a blameless post-mortem.

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
skill: incident-postmortem
timestamp: {{ISO8601}}
status: completed
incident_date: {{date}}
incident_severity: P1 | P2 | P3 | P4
duration_minutes: N
action_items_p1: N
action_items_total: N
postmortem_artifact: ai-docs/postmortem-{{date}}-{{slug}}.md
---
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
Emit: `[Post-Mortem Written] ai-docs/postmortem-{{date}}-{{slug}}.md`

### Step 9 — Report to user

Tell the user:
- Root cause (1 sentence)
- Number of action items by priority (P1/P2/P3)
- Path to the post-mortem document
- Suggest: open Jira tickets for P1 action items with `/claude-tech-squad:squad` or manually
- Suggest: schedule a team review of the post-mortem within 48 hours of incident resolution
