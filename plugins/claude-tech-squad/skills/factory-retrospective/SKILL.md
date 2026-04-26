---
name: factory-retrospective
description: This skill should be used when reviewing recent squad executions to identify retry patterns, common failures, and workflow/prompt improvements from logs. Trigger with "retrospectiva da factory", "factory retrospective", "melhorar a squad", "revisar processo", "lessons learned". NOT for post-mortems on a single production incident (use /incident-postmortem).
user-invocable: true
---

# /factory-retrospective — Agent Factory Self-Improvement Retrospective

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Apply changes to `CLAUDE.md` or skill files without the user approving them at the gate in Step 6
- Delete or overwrite SEP log files — logs are audit trails, treat them as read-only
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Analyzes recent agent execution logs, identifies patterns of failure, retry loops, and inefficiencies, then produces actionable recommendations to improve the agent factory workflow.

## When to Use

- After multiple squad executions to review quality trends
- When agent outputs are frequently rejected or require rework
- For periodic process improvement
- When the user says: "retrospectiva da factory", "factory retrospective", "melhorar a squad", "revisar processo", "lessons learned"

## Execution

Follow these steps exactly:

### Step 1 — Discover execution logs (SEP-aware)

**Primary source — SEP structured logs:**

```bash
ls ai-docs/.squad-log/ 2>/dev/null | sort -r | head -30 || echo "NO_SEP_LOGS"
```

Read all files in `ai-docs/.squad-log/` (newest first). Parse the YAML frontmatter of each file to extract:
- `skill`, `timestamp`, `status`, `retry_count`, `gates_blocked`, `findings_*`, `uat_result`, `implement_triggered`
- `runtime_policy_version`, `checkpoint_cursor`, `completed_checkpoints`, `resume_from`, `fallback_invocations`, `teammate_reliability`

**Orphaned discovery detection:**
From SEP logs with `skill: discovery`, collect all where `implement_triggered: false`. These are discoveries that were never implemented.

**Remediation gap detection:**
Find remediation files and check for unchecked items:
```bash
grep -l "^- \[ \]" ai-docs/security-remediation-*.md ai-docs/dependency-remediation-*.md 2>/dev/null
```
Count `- [ ]` vs `- [x]` lines per file to compute remediation completion rate.

**Previous retrospective follow-up:**
Find the most recent factory-retrospective report:
```bash
LAST_RETRO=$(ls ai-docs/factory-retrospective-*.md 2>/dev/null | sort -r | head -1)
echo "Last retro: ${LAST_RETRO:-NONE}"
```

If a prior retrospective exists:
1. Read it and extract all numbered recommendations (R1, R2, etc.) with their priority
2. For each recommendation, check if it was implemented:
   - If it references a CLAUDE.md rule: grep for the rule text in CLAUDE.md
   - If it references a skill file change: check the skill file for the described change
   - If it references a process change: check tasks/todo.md or tasks/lessons.md
3. Compute `retro_implementation_rate = implemented / total_recommendations`
4. List unimplemented HIGH priority recommendations as `RETRO_DEBT`
5. Include this as a dedicated metric in Step 5 report: "Previous Retro Implementation Rate"

This ensures the retrospective process itself is accountable — recommendations that are repeatedly ignored across retros are escalated in priority.

**Fallback source — inferred artifacts (when no SEP logs exist):**

```bash
find ai-docs/ -name "*.md" -newer ai-docs/.last-retro 2>/dev/null | head -20 || find ai-docs/ -name "*.md" -type f 2>/dev/null | sort -t/ -k3 | tail -10 || echo "NO_LOGS_FOUND"
```

Also search for: `tasks/todo.md`, `tasks/lessons.md`

Use Glob: `ai-docs/*.md`, `tasks/*.md`

### Step 2 — Analyze execution patterns

**If SEP logs exist**, compute these metrics directly from frontmatter:

**Retry and failure rates:**
- Retry rate per skill: average `retry_count` grouped by `skill` field — identify which skills exhaust retry budgets most
- Skills with `gates_blocked` most often: count `gates_blocked` entries per skill and sort descending
- `uat_result: REJECTED` rate: `REJECTED` count / total `/implement` runs
- `final_status: aborted` without reason: logs where `final_status` is `aborted` but the log body has no explanation of why — flag these for follow-up
- `final_status: failed` rate per skill: group failed runs by `skill` to find reliability hotspots

**Fallback and reliability analysis:**
- Fallback rate per agent: parse all `fallbacks_invoked` arrays across logs, count per `primary_agent` and per `fallback_agent` — output top 5 agents that trigger fallback most
- Low reliability teammates: entries in `teammate_reliability` marked `fallback-used`, `skipped-with-risk`, or `unresolved` — sorted by frequency across all runs
- Runs using fallback agents: `length(fallbacks_invoked) > 0` as fraction of total runs, broken down by skill

**Checkpoint and resume patterns:**
- Most frequent checkpoint where runs stop: count occurrences of each `checkpoint_cursor` value — this shows where pipelines most commonly pause or fail
- Resume frequency: count runs where `resume_from` is not `none` — high values indicate the pipeline is frequently interrupted
- Checkpoint progression rate: for each skill, compute the average number of completed `checkpoints` entries — short lists may indicate early termination

**Run chain and continuity:**
- Orphaned discoveries: SEP logs with `skill: discovery` and `implement_triggered: false` — discoveries that were never implemented
- Hotfixes without post-mortem: `skill: hotfix` logs with `postmortem_recommended: true` that have no matching `skill: incident-postmortem` log with `parent_run_id` pointing to that hotfix `run_id` — flag each unresolved hotfix by `run_id`
- Run chains: group logs by `parent_run_id` to reconstruct discovery → implement → hotfix → postmortem chains — identify broken chains

**Observability gaps:**
- Runs without SEP log: compare agent invocations in narrative logs (`ai-docs/*.md`) against `.squad-log/` entries — skills or runs that produced no SEP log indicate missing C1 contract compliance
- Skills missing from .squad-log: if a skill directory exists in `plugins/claude-tech-squad/skills/` but has no corresponding `.squad-log/` entries (i.e., never been run), flag it as unvalidated in production

**Developer satisfaction analysis:**
- Parse `developer_feedback.score` from each SEP log
- Compute average satisfaction per skill: group by `skill`, average `score` (exclude `skipped`)
- Correlate satisfaction with retries: do runs with `retry_count > 1` have lower scores?
- Correlate satisfaction with fallbacks: do runs with `fallback_invocations > 0` have lower scores?
- Correlate satisfaction with duration: do longer runs have lower scores?
- Flag skills with average score < 2.5 as `LOW SATISFACTION`
- Collect all `developer_feedback.comment` entries and group by theme

**Audit and remediation:**
- Open remediation items: `- [ ]` count across all remediation files in `ai-docs/`
- Finding resolution rate: `- [x]` / (`- [x]` + `- [ ]`) per audit file
- Cost risk releases: `skill: release` logs where cost-optimizer returned RISK (check log body)

**If only fallback artifacts exist**, infer patterns from file content:

**Retry patterns:**
- Use Grep to find: `retry`, `attempt`, `try again`, `failed`, `rejected`, `redo`, `cycle`
- Count how many times build/review cycles repeated per execution

**Blocked gates:**
- Search for: `blocked`, `waiting`, `gate`, `approval needed`, `user input required`
- Identify which gates blocked most frequently

**Rejected outputs:**
- Search for: `rejected`, `not acceptable`, `redo`, `revision needed`, `does not meet`
- Identify which agents had outputs rejected

**Common errors:**
- Search for: `error`, `failed`, `exception`, `could not`, `unable to`
- Categorize by error type

### Step 3 — Analyze project rules

Read `CLAUDE.md` from the project root (if it exists). Look for:
- Rules that are frequently violated (cross-reference with error patterns)
- Rules that are ambiguous or contradictory
- Missing rules that would have prevented observed failures

### Step 4 — Invoke tech lead for synthesis

Use TeamCreate to create a team named "factory-retrospective-team". Then spawn the agent using the Agent tool with `team_name="factory-retrospective-team"` and a descriptive `name`.

Use the Agent tool with `subagent_type: "claude-tech-squad:techlead"`, `team_name: "factory-retrospective-team"`, `name: "techlead"`.

Prompt:
```
You are the Tech Lead agent running a factory retrospective. Synthesize the following execution data into improvement recommendations.

Execution logs analyzed: {{log_count}} files
Date range: {{date_range}}

## Retry & Failure Analysis
{{retry_patterns}}

## Blocked Gates
{{blocked_gates}}

## Fallback Rate per Agent (top 5)
{{fallback_patterns}}

## Checkpoint Stopping Points (most common checkpoint_cursor values)
{{checkpoint_patterns}}

## Run Chain Gaps
- Orphaned discoveries (implement_triggered: false): {{orphaned_discovery_count}}
- Hotfixes without postmortem: {{hotfix_no_postmortem_count}} (run_ids: {{hotfix_no_postmortem_ids}})
- Broken chains: {{broken_chain_count}}

## Observability Gaps
- Runs without SEP log: {{missing_sep_log_count}}
- Skills never validated in production: {{unvalidated_skills}}
- Runs with final_status=aborted without explanation: {{aborted_without_reason_count}}

## Rejected Outputs & UAT
{{rejected_outputs}}
UAT rejection rate: {{uat_rejection_rate}}

## Common Errors
{{common_errors}}

## CLAUDE.md Rule Conflicts
{{rule_conflicts}}

Produce actionable recommendations organized by category:

1. **Reliability improvements** (based on retry rates, fallback rates, and failure hotspots):
   - For each skill with retry_count > 1 average: specific prompt or gate change to reduce retries
   - For each agent with high fallback rate: root cause and fix recommendation

2. **Pipeline continuity improvements** (based on checkpoint stops, orphaned runs, missing chains):
   - For each frequently stopped checkpoint: why runs stop there and how to reduce stops
   - For each orphaned discovery: whether it needs a follow-up /implement or should be closed

3. **Observability improvements** (based on missing SEP logs, aborted runs without reason):
   - For each skill missing from .squad-log: confirm SEP log instruction is present
   - For aborted runs without logged reason: what context should be captured on abort

4. **Agent quality improvements** (based on rejected outputs and low reliability teammates):
   - For each rejected agent: specific prompt change to reduce rejection rate
   - For each low reliability teammate: whether to adjust prompts or update fallback_matrix

5. **Rule and process improvements** (based on CLAUDE.md conflicts and workflow structure):
   - Rule additions, removals, or clarifications
   - Gate reordering or new gate proposals

Priority ranking: high (fix within next sprint) / medium (fix within 2 sprints) / low (nice to have)
```

### Step 5 — Present findings and recommendations

Present to the user:

```markdown
# Factory Retrospective — YYYY-MM-DD

## Execution Summary
- Logs analyzed: N SEP log files
- Period: [earliest timestamp] → [latest timestamp]
- Skills executed: [comma-separated skill names]
- Total retry cycles: N (avg N per run)
- Final status breakdown: completed=N, failed=N, partial=N, aborted=N

## Pipeline Health Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Retry rate (avg/run) | N | < 1.0 | 🟢 / 🔴 |
| Fallback rate | N% | < 15% | 🟢 / 🔴 |
| UAT rejection rate | N% | < 20% | 🟢 / 🔴 |
| Orphaned discoveries | N | 0 | 🟢 / 🔴 |
| Hotfixes without postmortem | N | 0 | 🟢 / 🔴 |
| Runs without SEP log | N | 0 | 🟢 / 🔴 |
| Aborted without reason | N | 0 | 🟢 / 🔴 |
| Prev retro implementation rate | N% | > 70% | 🟢 / 🔴 |
| Retro debt (unimpl HIGH items) | N | 0 | 🟢 / 🔴 |
| Remediation completion rate | N% | > 50% | 🟢 / 🔴 |

## Previous Retro Follow-up
| # | Recommendation | Priority | Status |
|---|---------------|----------|--------|
| R1 | [title] | high/med/low | implemented / not implemented / partially |

**Implementation rate:** N/M (X%)
**Retro debt (unimplemented HIGH):** [list or "none"]

## Patterns Identified

### Pattern 1: [title]
- **Evidence:** [log excerpts, run_ids]
- **Impact:** high / medium / low
- **Root cause:** [specific cause]

### Pattern 2: ...

## Actionable Recommendations

### Category 1 — Reliability (retry & fallback hotspots)
| # | Skill / Agent | Finding | Recommended Change | Priority |
|---|---|---|---|---|
| 1 | skill-name | avg retry_count=N | [specific prompt or gate change] | high |

### Category 2 — Pipeline Continuity (orphaned runs, broken chains)
| # | Finding | Action | Owner |
|---|---|---|---|
| 1 | N orphaned discoveries | [list run_ids, decide: implement or close] | operator |

### Category 3 — Observability (missing SEP logs, aborted runs)
| # | Skill | Gap | Fix |
|---|---|---|---|
| 1 | skill-name | no SEP log entry found | verify SEP log instruction in SKILL.md |

### Category 4 — Agent Quality (rejected outputs, low reliability teammates)
| # | Agent | Issue | Prompt Change |
|---|---|---|---|

### Category 5 — Rules & Process (CLAUDE.md conflicts, gate improvements)
| # | Change | Action | Rationale |
|---|---|---|---|
```

### Step 6 — Interactive approval gate (mandatory)

Ask the user:
```
Which recommendations do you want to implement?
- [A] All recommendations
- [N] None (just save the report)
- [1,3,5] Specific recommendations by number
```

Do NOT proceed with changes until the user responds. This is a blocking gate.

### Step 7 — Apply approved changes

For each approved recommendation:
- If it modifies `CLAUDE.md`: apply the edit using the Edit tool
- If it adds a new process rule: append to `CLAUDE.md` or the appropriate config file
- If it documents a lesson: append to `tasks/lessons.md`

**Mandatory — HIGH priority tracking (runs regardless of user approval selection):**

After applying approved changes, write all `priority: high` recommendations that were NOT approved to `tasks/todo.md` as pending checkboxes so they are not silently dropped:

```
Append to tasks/todo.md (create if missing):

## Factory Retrospective — {{YYYY-MM-DD}} — Pending HIGH Items

{{for each HIGH recommendation not approved in this session:}}
- [ ] [RETRO-{{N}}] {{recommendation_title}} — {{one_line_description}}
```

Emit: `[TODO Written] tasks/todo.md — {{N}} HIGH items added`

This ensures the next retrospective can detect unresolved HIGH items from prior runs via the orphaned-recommendation check in Step 2.

Document all changes applied in the retrospective report.

### Step 7b — Sync changes to installed plugin cache

If any SKILL.md file was modified in Step 7, the installed plugin cache must be updated — otherwise the next run will still execute the old version.

Detect the cache path:

```bash
CACHE=$(ls -d ~/.claude/plugins/cache/*/*/claude-tech-squad/*/skills/ 2>/dev/null | head -1)
echo "${CACHE:-NOT_FOUND}"
```

If cache is found, copy each modified skill to the cache:

```bash
# For each modified skill (e.g. implement, discovery, security-audit):
cp plugins/claude-tech-squad/skills/{{skill}}/SKILL.md "$CACHE/{{skill}}/SKILL.md"
```

If cache is NOT_FOUND, emit a warning:

```
[Warning] Plugin cache not found. Changes applied to source only.
Run: claude plugin install claude-tech-squad@alexfloripavieira-plugins
to reinstall and pick up the updated skill files.
```

Emit: `[Cache Synced] {{N}} skill(s) updated in installed plugin`

### Step 8 — Save report and mark timestamp

Write the full retrospective report to:
```
ai-docs/factory-retrospective-YYYY-MM-DD.md
```

Create the timestamp marker:
```bash
touch ai-docs/.last-retro
```

### Step 8b — Write SEP log

Write to `ai-docs/.squad-log/factory-retrospective-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: factory-retrospective
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [logs-analyzed, patterns-identified, recommendations-approved]
fallbacks_invoked: []
logs_analyzed: N
patterns_identified: N
changes_applied: N
report_artifact: ai-docs/factory-retrospective-YYYY-MM-DD.md
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 9 — Entropy Management (Automated Cleanup)

After writing the SEP log, perform these automated entropy checks:

**9a. Reset retrospective counter:**

The `.retro-counter` file at `ai-docs/.squad-log/.retro-counter` is a small plain-text file containing a single integer — the number of SEP-log-writing skill runs since the last retrospective. It is managed by:

- `/implement`, `/squad`, `/hotfix`, `/bug-fix`, etc. — increment by 1 at end of run
- `runtime-policy.yaml` `entropy_management.factory_retrospective_auto_trigger` — reads the value and prompts `/factory-retrospective` after threshold (default 5)
- This step (9a) — **resets to 0** at the end of every retrospective

```bash
echo "0" > ai-docs/.squad-log/.retro-counter
```

The file is gitignored; only `.gitkeep` is tracked. If the file is missing, treat it as `0` and create it with `0`. If it contains a non-integer, reset to `0` and emit `[Entropy] counter corrupted — reset to 0`.

**9b. Stale artifact detection:**
Scan `ai-docs/` for files older than 30 days that have no corresponding SEP log entry:
```bash
find ai-docs/ -name "*.md" -not -path "ai-docs/.squad-log/*" -mtime +30 2>/dev/null
```
For each stale file, emit: `[Entropy] Stale artifact: {{file}} ({{age}} days old, no matching SEP log)`

**9c. Broken chain cleanup recommendations:**
For each broken chain identified in Step 2 (discovery without implement, hotfix without postmortem):
- Emit: `[Entropy] Broken chain: {{chain_description}}`
- Recommend: close the orphan, trigger the missing downstream skill, or archive

**9d. Token cost trend analysis:**
If SEP logs contain `tokens_input` and `tokens_output` fields, compute:
- Average token cost per skill over the analysis period
- Skill with highest average cost
- Trend: is cost per run increasing, stable, or decreasing?
- Emit: `[Entropy] Token cost trend: {{trend}} — avg {{avg_tokens}} tokens/run, highest: {{skill}} at {{max_tokens}} tokens/run`

**9e. Doom loop frequency report:**
Count `[Doom Loop Detected]` entries across SEP logs and trace files:
- If any: recommend specific agent prompt improvements
- Emit: `[Entropy] Doom loops: {{count}} detected in analysis period — top agent: {{agent_name}} ({{agent_count}} occurrences)`

### Step 10 — Report to user

Tell the user:
- Number of patterns identified
- Changes applied (if any)
- Path to the saved retrospective report
- Entropy management actions taken
- Token cost trends (if data available)
- Suggested cadence for running the next retrospective
