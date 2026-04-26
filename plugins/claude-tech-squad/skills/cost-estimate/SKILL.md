---
name: cost-estimate
description: Analyze a task description and recommend the most cost-effective skill. Classifies complexity, estimates token cost, and prevents using /squad for a 5-line fix. Zero agents spawned — instant response. Trigger with "cost estimate", "which skill", "quanto custa", "qual skill usar", "estimate cost".
user-invocable: true
---

# /cost-estimate — Task Complexity Analysis & Skill Recommendation

## Global Safety Contract

**This contract applies to this workflow. Violating it requires explicit written user confirmation.**

No operation may, under any circumstances:
- Delete or overwrite SEP log files — logs are audit trails, treat them as read-only
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute dynamic shell injection or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Analyzes the user's task description, classifies complexity, and recommends the cheapest adequate skill. This is a **zero-agent, read-only** skill — no teammates spawned, no code written, no side effects beyond a SEP log.

## When to Use

- Before starting any work — "which skill should I use for this?"
- When unsure if a task needs `/squad` or just `/bug-fix`
- To estimate cost before committing tokens
- When the user says: "cost estimate", "which skill", "quanto custa", "qual skill usar"

**This skill should be the cheapest operation in the plugin.** If it costs more than the skill it recommends, it has failed its purpose.

## Execution

This skill reads conversation context only. No Agent tool calls. No TeamCreate. The orchestrator executes all steps directly.

### Step 1 — Read task description

Extract the user's task from the conversation. If the user hasn't described a task, ask:

```
What is the task to build, fix, review, or audit?
Describe in one sentence — the skill recommends the right command and estimates the cost.
```

**Deduplication guard:** Before proceeding, compute a `task_hash` by normalizing the task description (lowercase, strip punctuation, collapse whitespace) and comparing it against the `task_summary` field of the last 10 SEP logs in `ai-docs/.squad-log/` that have `skill: cost-estimate`. If a matching hash is found in a log written within the last 10 minutes, emit:

```
[Duplicate Detected] cost-estimate already ran for this task {{N}} minute(s) ago.
Cached result: {{recommended_skill}} — {{complexity_tier}} — {{estimated_cost}}
Run again? [Y/N]
```

If [N], return the cached recommendation without writing a new SEP log.
If [Y] or no match found, continue to Step 2.

### Step 2 — Classify complexity

Analyze the task description against these signal patterns:

| Signal in task | Complexity tier | Rationale |
|---|---|---|
| "typo", "rename", "one file", "small change", "comment" | **trivial** | No plugin needed |
| "bug", "fix", "broken", "error", "failing test", 1-3 files mentioned | **small** | Focused fix |
| "production down", "outage", "emergency", "hotfix", "urgent" | **small-urgent** | Fast fix path |
| "PR", "review", "pull request", "code review" | **small-review** | Analysis only |
| "feature", "implement", "build", "add", "create", 4+ files or components | **medium** | Feature work |
| "refactor", "clean up", "tech debt", "decouple" | **medium-refactor** | Guarded refactor |
| "security", "audit", "CVE", "vulnerability" | **medium-audit** | Analysis |
| "end-to-end", "full pipeline", "from scratch", "new project", multi-component | **large** | Full delivery |
| "multiple services", "cross-repo", "distributed" | **large-distributed** | Multi-service |

If multiple signals are present, use the **highest** tier detected.

### Step 3 — Map to skill recommendation

| Complexity tier | Recommended skill | Alternatives | Estimated agents | Estimated tokens | Estimated cost (Opus) |
|---|---|---|---|---|---|
| **trivial** | No plugin — ask Claude directly | — | 0 | ~5K | ~$0.01 |
| **small** | `/bug-fix` | `/hotfix` (if urgent) | 3-5 | 200K-400K | $1-3 |
| **small-urgent** | `/hotfix` | `/cloud-debug` (if need investigation) | 4-6 | 300K-500K | $2-4 |
| **small-review** | `/pr-review` | `/security-audit` (if security focus) | 6-8 | 300K-600K | $2-5 |
| **medium** | `/discovery` then `/implement` | `/squad` (if want one command) | 10-15 | 800K-1.5M + 1.5M-3M | $6-12 + $10-20 |
| **medium-refactor** | `/refactor` | `/implement` (if architecture change) | 4-6 | 400K-800K | $3-6 |
| **medium-audit** | `/security-audit` | `/dependency-check` (if deps only) | 2-4 | 200K-400K | $1-3 |
| **large** | `/squad` | `/discovery` + `/implement` (separate) | 20-30 | 3M-5M | $15-30 |
| **large-distributed** | `/multi-service` | `/squad` per service | 15-25 | 2M-4M | $12-25 |

### Step 4 — Present recommendation

```markdown
## Cost Estimate

**Task:** {{one_line_summary}}
**Complexity:** {{tier}} ({{rationale}})

### Recommended
**{{skill_name}}** — {{estimated_cost}} ({{estimated_agents}} agents, {{estimated_tokens}} tokens)

### Alternatives
{{alternative_1}} — {{cost}} ({{when_to_use}})
{{alternative_2}} — {{cost}} ({{when_to_use}})

### Savings vs /squad
Running /squad instead would cost: ~$15-30 (3M-5M tokens)
Recommended path saves: ~${{savings}}

### Next step
Run: `/claude-tech-squad:{{recommended_skill}}`
```

### Step 5 — Write SEP log

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-cost-estimate-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: cost-estimate
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [task-analyzed, recommendation-produced]
fallbacks_invoked: []
task_summary: {{one_line}}
task_hash: {{normalized_hash}}
complexity_tier: {{tier}}
recommended_skill: {{skill}}
estimated_cost_usd: {{range}}
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Recommendation
{{skill}} for {{task}} — {{tier}} complexity, {{cost}} estimated
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
