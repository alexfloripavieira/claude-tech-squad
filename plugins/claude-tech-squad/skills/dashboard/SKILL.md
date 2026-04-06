---
name: dashboard
description: Instant pipeline health dashboard. Reads SEP logs from ai-docs/.squad-log/, aggregates run status per skill, flags hotfixes without a post-mortem, and saves a snapshot to ai-docs/dashboard-snapshot.md. No agents spawned — zero latency. Trigger with "dashboard", "status da esteira", "pipeline health", "resumo de execuções", "squad status".
user-invocable: true
---

# /dashboard — Instant Pipeline Health Status

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Delete or overwrite SEP log files — logs are audit trails, treat them as read-only
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute dynamic shell injection or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Reads the last 30 SEP logs and produces a structured health summary of the squad pipeline. No agents are spawned — this is a zero-latency status check, not an AI analysis. For deep pattern analysis and improvement recommendations, use `/factory-retrospective`.

## When to Use

- Quick status check before starting a new session
- After a multi-run sprint to see overall health at a glance
- When you want to know which skills had failures or blocked gates recently
- To detect hotfixes that are waiting for a post-mortem
- When the user says: "dashboard", "status da esteira", "pipeline health", "resumo de execuções", "squad status"

**Use `/factory-retrospective` instead when:**
- You want AI-generated recommendations on how to improve the process
- You need deep pattern analysis across many runs (retry root causes, fallback triggers)
- You want the tech lead to analyze bottlenecks and suggest workflow changes

## Execution

This skill reads files only. No Agent tool calls. No TeamCreate. The orchestrator executes all steps directly.

### Step 1 — Discover SEP logs

```bash
ls ai-docs/.squad-log/ 2>/dev/null | grep -v ".gitkeep" | sort -r | head -30
```

If the directory is empty or only contains `.gitkeep`:

```
No SEP logs found in ai-docs/.squad-log/.

This means no skills have been run yet in this session, or logs were cleared.
Run a skill (e.g., /discovery, /squad, /hotfix) and then run /dashboard again.
```

Emit: `[Dashboard] Found N SEP logs — reading last 30`

### Step 2 — Read and parse each log

For each file found in Step 1, read its YAML frontmatter and extract:

| Field | Used for |
|---|---|
| `skill` | Group runs by skill |
| `timestamp` | Sort chronologically, show last run date |
| `final_status` | Count: completed / aborted / failed |
| `fallbacks_invoked` | Count fallback events |
| `checkpoints` | Show checkpoint coverage |
| `findings_critical` | Flag high-risk runs |
| `findings_high` | Flag high-risk runs |
| `run_id` | Match hotfixes to post-mortems |
| `postmortem_recommended` | Detect hotfixes awaiting post-mortem |
| `parent_run_id` | Match post-mortems to their parent hotfix |

If a field is absent from a log, treat it as `null` / `0` / empty — do not error.

### Step 3 — Aggregate per skill

Build a per-skill summary table:

| Skill | Total runs | Completed | Aborted/Failed | Last run | Blocked gates | Fallbacks |
|---|---|---|---|---|---|---|
| discovery | N | N | N | YYYY-MM-DD | N | N |
| implement | N | N | N | YYYY-MM-DD | N | N |
| squad | N | N | N | YYYY-MM-DD | N | N |
| hotfix | N | N | N | YYYY-MM-DD | N | N |
| ... | | | | | | |

**Success rate** = completed / total × 100. Flag any skill with success rate below 70% as `⚠ LOW`.

**Blocked gates** = count runs where `checkpoints` includes a gate that was paused (use `gate` or `blocked` in checkpoint names as signal). Flag skills with > 2 blocked gates as `⚠ FREQUENT GATES`.

### Step 4 — Detect hotfixes awaiting post-mortem

From SEP logs with `skill: hotfix`:
1. Collect all `run_id` values where `postmortem_recommended: true`
2. Collect all `parent_run_id` values from SEP logs with `skill: incident-postmortem`
3. Hotfixes awaiting post-mortem = hotfix run_ids NOT in any incident-postmortem `parent_run_id`

For each pending hotfix, show: `run_id`, `timestamp`, one-line summary from the log.

### Step 5 — Build and display the dashboard

Emit the dashboard as a fenced markdown block:

```markdown
## Squad Pipeline Dashboard — {{ISO8601 timestamp}}

### Run Health by Skill
| Skill | Runs | Completed | Failed/Aborted | Success% | Last run | Flags |
|---|---|---|---|---|---|---|
| /discovery | N | N | N | N% | YYYY-MM-DD | |
| /implement | N | N | N | N% | YYYY-MM-DD | |
| /squad | N | N | N | N% | YYYY-MM-DD | |
| ... | | | | | | |

### Hotfixes Awaiting Post-Mortem
{{list of pending hotfixes with run_id and timestamp, or "None — all hotfixes have associated post-mortems"}}

### Recent Activity (last 5 runs across all skills)
| Timestamp | Skill | Status | Notes |
|---|---|---|---|
| {{timestamp}} | {{skill}} | {{status}} | {{one-line note}} |

### Summary
- Total runs analyzed: N
- Overall success rate: N%
- Skills with low success rate (<70%): {{list or "None"}}
- Hotfixes awaiting post-mortem: N
- Snapshot saved: ai-docs/dashboard-snapshot.md
```

### Step 6 — Save dashboard snapshot

```bash
mkdir -p ai-docs
```

Write the dashboard output to `ai-docs/dashboard-snapshot.md`, overwriting any previous snapshot. Include the timestamp at the top.

Emit: `[Dashboard Snapshot] ai-docs/dashboard-snapshot.md`

### Step 7 — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-dashboard-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: dashboard
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [logs-read, aggregation-complete, snapshot-written]
fallbacks_invoked: []
logs_analyzed: N
skills_covered: N
hotfixes_pending_postmortem: N
---

## Dashboard Summary
Analyzed {{N}} SEP logs. Overall success rate: {{N}}%. {{N}} hotfixes awaiting post-mortem.
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
