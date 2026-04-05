---
name: pr-review
description: Reviews a pull request with the full specialist bench (reviewer, security, privacy, performance, accessibility), produces structured inline comments, and opens threads on GitHub via the API. Trigger with "revisar pr", "pr review", "code review da pr", "abrir threads de review", "review pull request".
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
