---
name: release
description: Standalone release preparation workflow. Builds change inventory from git, validates CI/CD and deploy assumptions, defines rollback steps, generates release notes, creates the version tag, and identifies required communication. Trigger with "preparar release", "gerar release", "release notes", "criar tag", "cortar release", "cut release".
user-invocable: true
---

# /release — Release Preparation

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Create a version tag or cut a release when CI is FAILING — CI must be GREEN before any tag is created
- Deploy to production before staging has been successfully deployed and verified
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in production
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a workaround
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations to production without confirming a recent backup exists

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Standalone release workflow. Use when implementation is complete and you need: change inventory, CI/CD validation, rollback plan, release notes, and version tag — without running the full `/squad`.

## When to Use

- Implementation is done and you want to cut a release
- You need release notes from a set of commits or PRs
- You want CI/CD validation and rollback documentation before deploying
- When the user says: "preparar release", "gerar release", "release notes", "criar tag", "cortar release", "cut release"

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

4. **Sequential teammates** (output feeds the next agent): [S] degrades ALL downstream teammates — warn the user explicitly before accepting skip.
5. **Do NOT advance to the next step** until every teammate has returned valid output, been explicitly skipped, or the run has been aborted.

## Execution

### Step 1 — Release Intake Gate

Ask the user (if not already provided):
1. **Version**: What is the version number? (e.g. `v1.4.0`, `2026.03`)
2. **Base**: What branch or tag is this release cut from? (default: current branch)
3. **Target**: What is the deploy target? (staging / production / both)
4. **Scope**: Is there a specific PR range or commit range? (optional — defaults to all commits since last tag)

### Step 2 — Build change inventory

```bash
# Find last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Commits since last tag
if [ -n "$LAST_TAG" ]; then
  git log ${LAST_TAG}..HEAD --oneline 2>/dev/null
else
  git log --oneline | head -50
fi
```

Categorize commits by conventional commit prefix:
- `feat:` → New features
- `fix:` → Bug fixes
- `hotfix:` → Emergency fixes
- `refactor:` → Refactors
- `perf:` → Performance improvements
- `security:` → Security fixes
- `deps:` / `chore(deps):` → Dependency updates
- `docs:` → Documentation
- `test:` → Test changes
- `chore:` → Maintenance

Also check for merged PRs if GitHub CLI is available:
```bash
gh pr list --state merged --base {{base_branch}} --limit 50 --json number,title,mergedAt,labels 2>/dev/null || echo "GH_NOT_AVAILABLE"
```

### Step 3 — Validate CI/CD

```bash
# Check if CI is passing on current branch
gh run list --branch $(git branch --show-current) --limit 5 --json status,conclusion,workflowName 2>/dev/null || echo "CI_STATUS_NOT_AVAILABLE"
```

Check for:
- Any failing CI runs on the release branch
- Pending migrations that haven't been applied
- Environment variables or secrets that need updating

```bash
# Check for pending migrations (if applicable)
git diff ${LAST_TAG}..HEAD --name-only 2>/dev/null | grep -E "migration|migrate|schema" || echo "NO_MIGRATION_FILES"
```

**CI Gate (hard block):** If CI status is `failure` or `cancelled` on the release branch, emit:

```
[BLOCKED] CI is FAILING on this branch. Release is blocked until CI passes.

Failing workflow(s): {{workflow_names}}

Do NOT proceed with tagging or release. Fix CI first, then re-run /release.
```

Do NOT continue to Step 4 if CI is failing. This is a non-negotiable safety gate — a failed CI means untested code, and deploying untested code violates the contract above.

**Exception:** If CI status is unavailable (`CI_STATUS_NOT_AVAILABLE`), emit a warning and allow the user to confirm at the gate in Step 7 that they accept the risk of unknown CI status.

Emit notices for:
- Migration files present (may need manual apply step)
- New environment variables introduced since last tag

### Step 4 — Spawn release agent for rollback plan

Use TeamCreate to create a team named "release-team". Then spawn each agent using the Agent tool with `team_name="release-team"` and a descriptive `name` for each agent.

```
Agent(
  subagent_type = "claude-tech-squad:release",
  team_name = "release-team",
  name = "release-agent",
  prompt = """
## Release Preparation

### Version
{{version}}

### Change Inventory
{{categorized_commits}}

### CI/CD Status
{{ci_status}}

### Pending Migrations
{{migration_files}}

### Deploy Target
{{target}}

---
You are the Release agent. Produce:
1. Rollback plan — specific steps to revert this release if needed
2. Deploy checklist — ordered steps to deploy safely (staging first, then production)
3. Required communications — who needs to know before/after deploy
4. Monitoring checklist — what to watch for 30 minutes post-deploy
5. GO / NO-GO assessment — is this release safe to deploy?

Safety constraints (non-negotiable):
- Return NO-GO if CI was FAILING on the release branch
- Deploy checklist must include staging verification before production
- Never recommend force-pushing or skipping hooks
- Never recommend disabling monitoring to proceed faster

Return structured output. Do NOT chain to other agents.
"""
)
```

If release agent returns NO-GO: present blockers to user and halt. Do NOT proceed to tagging.

### Step 5 — Spawn SRE for blast radius assessment

```
Agent(
  subagent_type = "claude-tech-squad:sre",
  team_name = "release-team",
  name = "sre",
  prompt = """
## SRE Release Review

### Change Inventory
{{categorized_commits}}

### Files Changed
{{changed_files_list}}

### Deploy Target
{{target}}

---
You are the SRE. Assess:
1. Blast radius — what breaks if this deploy goes wrong?
2. Rollback feasibility — can we revert cleanly within 5 minutes?
3. Canary recommendation — should this be a phased rollout?
4. SLO risk — does any change threaten existing SLOs?

Return: GO or NO-GO with specific risks. Do NOT chain.
"""
)
```

If SRE returns NO-GO: present to user and halt.

### Step 5b — Cost analysis (proactive)

Automatically spawn cost-optimizer to assess whether this release introduces new costs. Do NOT skip — run for every release.

```
Agent(
  subagent_type = "claude-tech-squad:cost-optimizer",
  team_name = "release-team",
  name = "cost-optimizer",
  prompt = """
## Pre-Release Cost Analysis

### Changes in this release
{{categorized_commits}}

### Files changed
{{changed_files_list}}

---
You are the Cost Optimizer. Analyze this release for cost impact:
1. New or modified DB queries — potential N+1, missing indexes, full table scans
2. New external API calls — pricing model, rate limits, per-call cost
3. New async jobs or workers — compute cost, memory footprint
4. New storage operations — S3/GCS writes, log volume, data retention
5. New infrastructure resources — lambdas, containers, queues

For each risk: estimate impact (negligible / low / medium / high) and mitigation.
Return: CLEAR (no significant cost risk) or RISK with specific items.
Do NOT chain.
"""
)
```

If cost-optimizer returns RISK: add cost findings to the release notes and flag for the release confirmation gate.
If CLEAR: emit `[Cost Analysis] No significant cost risk detected` and proceed.

### Step 5c — Feature flag audit (proactive)

Check if any feature flags from the blueprint are pending state changes for this release:

```bash
# Search for feature flag references in changed files
git diff ${LAST_TAG}..HEAD -- . | grep -iE "feature_flag|featureFlag|ff_|FLAG_|unleash|launchdarkly|flipper" | head -20 || echo "NO_FLAGS_FOUND"
```

If flags are found:
- List each flag, its current state, and whether it should be enabled/disabled/removed in this release
- Add a **Feature Flags** section to the deploy checklist:
  ```
  - [ ] Enable flag: {{flag_name}} in {{environment}}
  - [ ] Remove flag: {{flag_name}} — full rollout confirmed
  ```

If no flags found: proceed silently.

### Step 6 — Generate release notes

Produce release notes in two formats:

**Technical (internal):**

```markdown
# Release {{version}} — {{date}}

## What's in this release
### New Features
{{feat_commits}}

### Bug Fixes
{{fix_commits}}

### Security
{{security_commits}}

### Dependencies
{{deps_commits}}

### Other Changes
{{remaining_commits}}

## Deploy Notes
{{rollback_plan}}

## Monitoring
{{monitoring_checklist}}
```

**User-facing (changelog entry):**

```markdown
## {{version}} — {{date}}

### Added
- {{user_facing_features}}

### Fixed
- {{user_facing_fixes}}

### Security
- {{security_fixes}}
```

### Step 7 — Release confirmation gate

Present to user:

```
Release {{version}} summary:
- {{N}} features, {{N}} fixes, {{N}} security fixes
- CI/CD: {{PASSING/FAILING/UNKNOWN}}
- Release agent: {{GO/NO-GO}}
- SRE: {{GO/NO-GO}}
- Cost analysis: {{CLEAR/RISK}}
- Pending migrations: {{yes/no}}
- Feature flags to toggle: {{N}}

Deploy sequence after tagging:
1. Deploy to STAGING → verify → confirm
2. Deploy to PRODUCTION (only after staging verified)

Proceed to tag and publish release notes? [Y/N]
```

**This is a blocking gate.** Do NOT create tag until user confirms.

If CI/CD is UNKNOWN and user confirms: record `ci_unknown_override: true` in the SEP log.

### Step 8 — Create tag and release

If user confirms:

```bash
git tag -a {{version}} -m "Release {{version}}"
git push origin {{version}}
```

If GitHub CLI available, create GitHub release:

```bash
gh release create {{version}} \
  --title "{{version}}" \
  --notes "{{user_facing_release_notes}}"
```

### Step 9 — Write SEP log (SEP Contrato 1)

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-release-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: release
timestamp: {{ISO8601}}
status: completed
version: {{version}}
release_agent_result: GO | NO-GO
sre_result: GO | NO-GO
tag_created: true | false
features: N
fixes: N
security_fixes: N
---

## Change Summary
{{one_paragraph}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 10 — Report to user

Tell the user:
- Version tagged: `{{version}}`
- GitHub release URL (if created)
- Deploy checklist location
- Monitoring checklist
- Any NO-GO blockers that were overridden (if user proceeded anyway)
