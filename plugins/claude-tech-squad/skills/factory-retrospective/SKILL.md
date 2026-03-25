---
name: factory-retrospective
description: Runs a retrospective on recent agent executions by analyzing execution logs, identifying retry patterns and common failures, and producing improvement recommendations for prompts, rules, and workflow. Trigger with "retrospectiva da factory", "factory retrospective", "melhorar a squad", "revisar processo", "lessons learned".
user-invocable: true
---

# /factory-retrospective — Agent Factory Self-Improvement Retrospective

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

**Orphaned discovery detection:**
From SEP logs with `skill: discovery`, collect all where `implement_triggered: false`. These are discoveries that were never implemented.

**Remediation gap detection:**
Find remediation files and check for unchecked items:
```bash
grep -l "^- \[ \]" ai-docs/security-remediation-*.md ai-docs/dependency-remediation-*.md 2>/dev/null
```
Count `- [ ]` vs `- [x]` lines per file to compute remediation completion rate.

**Fallback source — inferred artifacts (when no SEP logs exist):**

```bash
find ai-docs/ -name "*.md" -newer ai-docs/.last-retro 2>/dev/null | head -20 || find ai-docs/ -name "*.md" -type f 2>/dev/null | sort -t/ -k3 | tail -10 || echo "NO_LOGS_FOUND"
```

Also search for: `tasks/todo.md`, `tasks/lessons.md`

Use Glob: `ai-docs/*.md`, `tasks/*.md`

### Step 2 — Analyze execution patterns

**If SEP logs exist**, compute these metrics directly from frontmatter:
- Average `retry_count` per skill
- Skills with `gates_blocked` most often
- `uat_result: REJECTED` rate
- Orphaned discoveries: SEP logs with `implement_triggered: false`
- Hotfixes without post-mortem: `skill: hotfix` logs with `postmortem_recommended: true` that have no matching `skill: incident-postmortem` log with `parent_run_id` pointing to that hotfix `run_id`
- Open remediation items: `- [ ]` count across all remediation files
- Finding resolution rate: `- [x]` / (`- [x]` + `- [ ]`) per audit
- Run chains: group logs by `parent_run_id` to reconstruct discovery → implement → hotfix → postmortem chains
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

Use the Agent tool with `subagent_type: "claude-tech-squad:techlead"`.

Prompt:
```
You are the Tech Lead agent running a factory retrospective. Synthesize the following execution data into improvement recommendations.

Execution logs analyzed: {{log_count}} files
Date range: {{date_range}}

Retry patterns found:
{{retry_patterns}}

Frequently blocked gates:
{{blocked_gates}}

Rejected agent outputs:
{{rejected_outputs}}

Common errors:
{{common_errors}}

CLAUDE.md rules that caused conflicts:
{{rule_conflicts}}

Produce:
1. Top 5 patterns identified (with evidence from logs)
2. Recommendations for agent prompt improvements (specific changes)
3. Recommendations for CLAUDE.md rule changes (additions, removals, clarifications)
4. Workflow structure improvements (phase order, parallel vs sequential, new gates)
5. Priority ranking by estimated impact (high / medium / low)
```

### Step 5 — Present findings and recommendations

Present to the user:

```markdown
# Factory Retrospective — YYYY-MM-DD

## Execution Summary
- Logs analyzed: N files
- Period: [date range]
- Total retry cycles detected: N
- Most problematic phase: [phase name]

## Patterns Identified

### Pattern 1: [title]
- **Evidence:** [log excerpts]
- **Impact:** [high/medium/low]
- **Root cause:** ...

### Pattern 2: ...

## Recommendations

### Agent Prompt Improvements
| Agent | Change | Expected Impact |
|-------|--------|----------------|

### CLAUDE.md Rule Changes
| Rule | Action (add/remove/clarify) | Rationale |
|------|----------------------------|-----------|

### Workflow Improvements
| Change | Impact | Effort |
|--------|--------|--------|
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

### Step 9 — Report to user

Tell the user:
- Number of patterns identified
- Changes applied (if any)
- Path to the saved retrospective report
- Suggested cadence for running the next retrospective
