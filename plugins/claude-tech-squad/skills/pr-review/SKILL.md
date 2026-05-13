---
name: pr-review
description: This skill should be used when a pull request needs a structured multi-lens review across correctness, security, privacy, performance, and accessibility, with review threads opened on GitHub. Trigger with "revisar pr", "pr review", "code review da pr", "abrir threads de review", "review pull request". NOT for implementing fixes directly before review.
user-invocable: true
---

# /pr-review — Pull Request Review with Specialist Bench

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Auto-approve or auto-merge a pull request — review findings are presented to the user, who decides
- Post review comments containing raw secrets, tokens, passwords, or credentials found in the diff (mask them as `[REDACTED]` before posting)
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Fetches the PR diff, runs the full reviewer bench in parallel, produces structured inline comments, and opens review threads on GitHub via the API.

## When to Use

- Before merging any non-trivial pull request
- When you want specialist coverage (security, privacy, performance, accessibility) beyond a basic code review
- When the user says: "revisar pr", "pr review", "code review da pr", "abrir threads de review", "review pull request"

## Operator Visibility Contract

Emit these trace lines so the operator can follow the review bench and the SEP log can capture state transitions:

- `[Preflight Start] pr-review`
- `[PR Intake] <repo> #<number> | files=<count> | additions=<N> | deletions=<N>`
- `[Stack Detected] <stack> | reviewer=<agent>`
- `[Team Created] pr-review-team`
- `[Batch Spawned] reviewer-bench | Teammates: reviewer, security-reviewer, privacy-reviewer, performance-engineer, accessibility-reviewer`
- `[Teammate Done] <role> | findings=<count>`
- `[Teammate Retry] <role> | Reason: <failure>`
- `[Gate] Teammate Failure | <name> failed twice` (when applicable)
- `[Consolidation Complete] BLOCKING=<N> | MAJOR=<N> | MINOR=<N>`
- `[Comments Posted] <count> threads on PR <url>`
- `[Team Deleted] pr-review-team | cleanup complete` (or `[Team Cleanup Warning]` on failure)
- `[SEP Log Written] ai-docs/.squad-log/<filename>`

## Inter-Teammate Cross-Talk Protocol

Teammates MUST exchange `SendMessage` with each other — not only with the lead — before reporting their `result_contract`. Lead does NOT relay. Required by `runtime-policy.yaml::agent_teams.cross_talk_protocol`. Enforcement is **mode-aware**: `teammate` mode opens a blocking gate on missing pairs; `inline` mode (tmux unavailable) downgrades to warning-only and the pipeline continues. Mode is resolved at preflight by `${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh`.

**Required pairs (pr-review) — adversarial_review / advogado do diabo:**
- `code-reviewer` ↔ `security-reviewer` (logic vs security challenge)
- `code-reviewer` ↔ `performance-engineer` (correctness vs perf trade-off)
- `security-reviewer` ↔ `privacy-reviewer` (overlap detection: do not report same finding twice)

**Advogado do diabo:** these pairs MUST challenge assumptions, risks, alternatives, missing evidence, and trade-offs directly in pt-BR before synthesis. Record any objection that changes severity, scope, or recommendation in the SEP log with mitigation and final decision.

**Spawn-prompt rule:** every spawn prompt MUST include a `peers:` block.

**Audit:** lead dumps mailbox to `sep_log.mailbox[]`. Zero outbound `SendMessage` to a required peer triggers the Teammate Failure Protocol with `reason: cross-talk-missing` and opens `[Gate] Cross-Talk Missing | pair: <a>↔<b> | [R]espawn / [A]ccept / [X]Abort`.

## Orchestration Contract — Mandatory Phases (CTS hard requirement)

The lead orchestrator MUST execute the four phases below in order on every
run of this skill. Skipping any phase is a contract violation. The SEP log
MUST record `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`,
`language_policy_applied: pt-BR`, and `timeouts_observed: [...]`. `scripts/validate.sh`
greps each dev-flow SKILL.md for the phase tags `CTS-PHASE: skill-init`,
`CTS-PHASE: agent-spawn`, `CTS-PHASE: agent-monitor`, `CTS-PHASE: agent-cleanup`,
and `CTS-PHASE: skill-finalize` to enforce wiring.

### Phase A — Skill Branch Init (CTS-PHASE: skill-init)

Run BEFORE any `Agent(...)` call:

```bash
INIT_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/init-skill-branch.sh pr-review)
# parse: skill_branch=<...> base_branch=<...> base_commit=<...> watchdog_pid=<...>
```

- Exit 3 → tree dirty → emit `[Preflight Failed] main worktree dirty` and STOP.
- On success emit `[Skill Branch Created] skill_branch=<...> base_branch=<...> base_commit=<...>`.
- A background watchdog daemon is launched and its pid recorded. The watchdog
  enforces the per-agent and per-skill runtime caps as a last-resort safety
  net. THE WATCHDOG DOES NOT REPLACE THE LEAD'S MONITORING DUTY — see Phase B.1.
- Persist `skill_branch` value for Phases B and D.

### Phase B — Per-Agent Spawn Wrap (CTS-PHASE: agent-spawn)

For EVERY `Agent(...)` invocation in this skill (teammate or inline mode):

```bash
SPAWN_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/spawn-agent-worktree.sh pr-review <agent_name> <agent_id>)
# parse: path=<...> branch=<...> base=<...> spawned_at=<epoch>
```

The Agent spawn `prompt` MUST begin with, in this exact order:

1. `language_policy.spawn_prompt_preamble` — literal text from `runtime-policy.yaml::language_policy.spawn_prompt_preamble` (pt-BR mandate).
2. The five worktree fields from `runtime-policy.yaml::agent_worktrees.spawn_prompt_inject.fields_appended_to_every_prompt`:
   - `skill_branch: <...>`
   - `worktree_path: <path>`
   - `branch: <branch>`
   - `base_commit: <base>`
   - `instruction: cd into worktree_path before any Read/Edit/Write/Bash. ...`
3. The role-specific spawn prompt body that this SKILL.md defines below.

Emit `[Worktree Spawned] agent=<...> | path=<...> | branch=<...> | spawned_at=<epoch>`.
Record `spawned_at` per agent — Phase B.1 needs it.

### Phase B.1 — Active Monitoring (CTS-PHASE: agent-monitor) — LEAD'S FIRST-LINE DUTY

This is what the orchestrator exists for. The watchdog is the OS-level
backstop; the lead is the first responder.

For every spawned agent the lead MUST:

1. **Track wall-clock since `spawned_at`.** Cap per agent is
   `runtime-policy.yaml::failure_handling.agent_max_runtime_seconds`
   (default 900s = 15 minutes). Skill-level cap is `skill_max_runtime_seconds`
   (default 7200s = 2 hours).

2. **Never block-wait indefinitely on a single agent.** Between status
   checks, do other work (other teammates' messages, gate handling) or
   sleep in short increments — never sit in an unbounded wait. If your
   runtime offers a polling primitive, use it; otherwise emit a status
   probe every ~120s.

3. **Detect stalls.** A teammate is considered stalled if EITHER:
   - wall-clock since `spawned_at` exceeds the per-agent cap, OR
   - no progress signal (SendMessage, tool call, partial output) for >
     `failure_handling.idle_seconds` (default 300s).

4. **On stall:**
   - Emit `[Teammate Timeout] agent=<...> | reason=<runtime_cap|idle> | age_seconds=<n>`.
   - Send `pkill -f -- "--agent-id <agent>@<skill>"` (or equivalent) to
     terminate the agent process.
   - Run `bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <path>`
     to remove the worktree (merge of partial work optional; merge failure
     non-fatal here).
   - Decrement retry budget. If budget remains and the failure mode is
     recoverable, respawn (Phase B again, fresh `spawned_at`). Otherwise
     open `[Gate] Teammate Failure | agent=<...> | reason=timeout |
     [R]espawn / [S]kip / [X]Abort`.
   - Append `{agent, reason, age_seconds, action}` to the SEP log's
     `timeouts_observed[]`.

5. **Never wait for human input from a subagent.** If a subagent emits a
   recovery prompt ("What should Claude do instead?"), the lead treats it
   as `reason=idle` and triggers the stall handler. Subagents MUST NOT
   block the skill on interactive prompts.

The watchdog daemon spawned in Phase A enforces the same caps independently;
if the lead misses a stall (e.g. it crashed or is itself stuck), the
watchdog kills the agent and writes a `.killed` marker. The lead MUST
inspect `ai-docs/.squad-log/.agents/*.killed` on its next tick and reflect
the kill in the SEP log.

### Phase C — Per-Agent Cleanup (CTS-PHASE: agent-cleanup)

Immediately after the Agent returns its `result_contract` (or after Phase
B.1 stall handling, or on skill abort):

```bash
CLEANUP_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <worktree_path>)
```

- Exit 0 → emit `[Worktree Cleanup] agent=<...> | merged=<true|false> | commits_ahead=<n> | branch_deleted=<branch>`.
- Exit 4 → merge conflict → emit `[Worktree Cleanup Conflict]` and open `[Gate] Worktree Merge Conflict | [R]esolve / [A]bort`. Worktree and branch are preserved until the user resolves.

This phase runs ONCE PER AGENT SPAWN (including timed-out spawns) and is non-skippable.

### Phase C.5 — SEP Log Commit (CTS-PHASE: sep-commit)

After the SEP log file is written under `ai-docs/.squad-log/<skill>-<timestamp>.md`
and BEFORE Phase D finalize, the lead MUST commit it on the skill branch.
Without this commit, finalize-skill.sh will see a dirty main worktree and
abort. The skill-active-guard hook is wired to allow these specific git
operations when scoped to `ai-docs/.squad-log/`.

```bash
CTS_LEAD_OK=1 git -C "$REPO_TOPLEVEL" add ai-docs/.squad-log/
CTS_LEAD_OK=1 git -C "$REPO_TOPLEVEL" commit -m "chore(squad-log): pr-review SEP log"
```

The lead MUST NOT delegate this step to the user — that defeats the
orchestration contract. If the commit fails, surface a `[Gate] SEP Log
Commit Failed` instead of asking the user to run the commands manually.

### Phase D — Skill Finalize (CTS-PHASE: skill-finalize)

After the last agent finishes, after the SEP log is written and committed,
and before returning control to the user:

```bash
FINAL_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/finalize-skill.sh "$skill_branch")
```

- Exit 0 → emit `[Skill Finalized] skill_branch=<...> | orphan_worktrees=0 | orphan_branches=0`. Sentinel is removed; watchdog exits on its next tick.
- Non-zero → STOP and surface the failing invariant to the user. Do NOT mark the skill complete.

`finalize-skill.sh` does NOT push, merge to base, or delete the skill
branch — that is the user's call.

### Cross-Talk & Language Audit (mandatory checks before SEP write)

- Inspect mailbox: every Required Pair declared in this skill's
  `## Inter-Teammate Cross-Talk Protocol` must have at least one outbound
  `SendMessage`. Empty pair → Teammate Failure with `reason: cross-talk-missing`.
- The lead's user-facing output (gate prompts, narrative reports) MUST
  follow `runtime-policy.yaml::language_policy.lead_to_user_preamble` (pt-BR).
- SEP log MUST contain:
  - `language_policy_applied: pt-BR`
  - `cts_phases_completed: [skill-init, agent-spawn, agent-monitor, agent-cleanup, skill-finalize]`
  - `worktrees: [...]` (one entry per agent spawn with `path`, `branch`, `commits_ahead`, `merged`, `final_status`)
  - `timeouts_observed: [...]` (empty list if none — explicit field required)
  - `bypasses_observed: [...]` (one entry per silenced/skipped teammate: `{agent, reason, user_decision: A|R|X, gate_emitted: true}`). EMPTY LIST IF NONE — explicit field required. Marking any agent as "BYPASSED" without a `[Gate] Reviewer Bypass Requested` and explicit user choice is a contract violation. **`user_decision` MUST come from a fresh per-gate chat reply.** Session-level preferences (e.g. "no clarifying questions" directive, autonomous-run mode, prior similar bypass) DO NOT pre-authorize the gate. See `runtime-policy.yaml::failure_handling.bypass_policy.session_preferences_do_not_authorize` and `forbidden_auto_resolutions`.



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

### Step 1 — PR Intake Gate

Ask the user (if not already provided):
1. **PR URL or number**: GitHub PR to review
2. **Review focus** (optional): Any specific concerns (security, performance, breaking changes)
3. **Open threads**: Should findings be posted as GitHub review threads? [Y/N]

### Step 2 — Fetch PR metadata

```bash
# Extract owner/repo/number from URL or ask user
gh pr view {{pr_number}} --repo {{owner/repo}} --json title,body,baseRefName,headRefName,additions,deletions,changedFiles 2>/dev/null
```

Fetch the diff:

```bash
gh pr diff {{pr_number}} --repo {{owner/repo}} 2>/dev/null
```

List changed files:

```bash
gh pr view {{pr_number}} --repo {{owner/repo}} --json files --jq '.files[].path' 2>/dev/null
```

Record: PR title, base branch, head branch, files changed, additions, deletions.

### Step 2b — Stack Specialist Routing

Detect repository stack from the changed files and repo root:

| Signal | Detected stack |
|---|---|
| `manage.py` + `django` in requirements | `django` |
| `package.json` with `"react"` | `react` |
| `package.json` with `"vue"` | `vue` |
| `tsconfig.json` or `typescript` in devDeps | `typescript` |
| `package.json` (no react/vue/ts) | `javascript` |
| `pyproject.toml`/`requirements.txt` without `manage.py` | `python` |
| None | `generic` |

Resolve: `{{reviewer_agent}}` — `code-reviewer` if `django`, otherwise `reviewer`.

Emit: `[Stack Detected] {{detected_stack}} | reviewer={{reviewer_agent}}`

### Step 3 — Detect review scope

From the changed files, determine which specialist reviewers are relevant:

| Files changed | Reviewers to spawn |
|---|---|
| Any source files | reviewer (always) |
| Auth, permissions, input handling, secrets | security-reviewer |
| User data, PII, external data flows | privacy-reviewer |
| DB queries, N+1, loops, rendering | performance-engineer |
| UI components, HTML, ARIA | accessibility-reviewer |
| API contracts, versioning, payloads | api-designer |
| Migrations, schema changes | dba |

### Step 4 — Spawn reviewer bench (parallel)

Use TeamCreate to create a team named "pr-review-team". Then spawn each reviewer using the Agent tool with `team_name="pr-review-team"` and a descriptive `name` for each agent.

Spawn all relevant reviewers in parallel. Each receives the full diff and file list.

```
Agent(
  subagent_type = "claude-tech-squad:reviewer",
  team_name = "pr-review-team",
  name = "reviewer",
  prompt = """
## Pull Request Review

### PR: {{title}}
### Base: {{base}} ← {{head}}
### Files: {{changed_files}}

### Diff:
{{full_diff}}

---
You are the Reviewer. Review for correctness, logic errors, missing tests, unnecessary complexity,
and documentation compliance.

For each finding, provide:
- file: path/to/file.ext
- line: N (must be a line present in the diff)
- severity: critical | high | medium | low | nit
- comment: specific, actionable feedback

Return findings as a structured list. Do NOT chain to other agents.
"""
)
```

Spawn security-reviewer (`name: "security-rev"`), privacy-reviewer (`name: "privacy-rev"`), performance-engineer (`name: "perf-eng"`), accessibility-reviewer (`name: "access-rev"`), api-designer (`name: "api-designer"`), dba (`name: "dba"`) with equivalent prompts adapted to their specialist lens. All use `team_name="pr-review-team"`.

Emit: `[Batch Spawned] review-bench | Teammates: reviewer, security-rev, privacy-rev, ...`

### Step 5 — Consolidate findings

Collect all outputs. Deduplicate findings that point to the same file:line. Resolve conflicts (if reviewer says "low" but security says "critical" for same finding, use the higher severity).

Build a consolidated findings list:

```
findings = [
  { file, line, severity, reviewer, comment },
  ...
]
```

Filter out findings where `line` is not in the diff (cannot be posted as inline comment).

### Step 6 — Present summary to user

```markdown
## PR Review Summary — {{title}}

### Findings by severity
- Critical: N
- High: N
- Medium: N
- Low/Nit: N

### Top issues
1. [CRITICAL] {{file}}:{{line}} — {{comment}}
2. [HIGH] {{file}}:{{line}} — {{comment}}
3. ...

### Reviewers that ran
- reviewer, security-reviewer, privacy-reviewer, ...
```

Ask the user if not already confirmed:
```
Open {{N}} findings as GitHub review threads? [Y/N]
```

**This is a blocking gate.** Do NOT post to GitHub until user confirms.

### Step 7 — Post review to GitHub

If user confirmed [Y]:

Build the review payload. All inline comments must reference lines present in the diff.

```bash
# Write payload to temp file to avoid shell escaping issues
cat > /tmp/pr_review_payload.json << 'PAYLOAD'
{
  "body": "Automated review by specialist bench. See inline comments for details.",
  "event": "COMMENT",
  "comments": [
    {
      "path": "{{file}}",
      "line": {{line}},
      "side": "RIGHT",
      "body": "[{{SEVERITY}}] {{comment}}"
    }
  ]
}
PAYLOAD

gh api repos/{{owner}}/{{repo}}/pulls/{{pr_number}}/reviews \
  --method POST \
  --input /tmp/pr_review_payload.json
```

**Important:** Use `--input` with a JSON file, never `--field` for array parameters — GitHub API returns HTTP 422 when comments array is not properly serialized.

If any comment fails due to line resolution error, skip that comment and emit a warning listing skipped findings.

Emit: `[Review Posted] {{N}} threads opened on PR #{{pr_number}}`

### Step 8 — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-pr-review-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: pr-review
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [preflight-passed, review-complete, verdict-issued]
fallbacks_invoked: []
pr_number: {{pr_number}}
findings_critical: N
findings_high: N
findings_medium: N
findings_low: N
threads_posted: N
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Findings Summary
{{one_line_per_critical_and_high_finding}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 9 — Report to user

Tell the user:
- Total findings by severity
- Number of threads opened on GitHub (or skipped)
- Any findings that could not be posted (out of diff range) — list them inline
- Path to the SEP log
