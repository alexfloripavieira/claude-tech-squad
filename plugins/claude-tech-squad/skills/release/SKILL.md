---
name: release
description: Standalone release preparation workflow. Builds change inventory from git, validates CI/CD and deploy assumptions, defines rollback steps, generates release notes, creates the version tag, and identifies required communication. Trigger with "preparar release", "gerar release", "release notes", "criar tag", "cortar release", "cut release".
user-invocable: true
---

# /release — Release Preparation

Standalone release workflow. Use when implementation is complete and you need: change inventory, CI/CD validation, rollback plan, release notes, and version tag — without running the full `/squad`.

## When to Use

- Implementation is done and you want to cut a release
- You need release notes from a set of commits or PRs
- You want CI/CD validation and rollback documentation before deploying
- When the user says: "preparar release", "gerar release", "release notes", "criar tag", "cortar release", "cut release"

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

Emit warnings for:
- CI failures on the branch
- Migration files present (may need manual apply step)
- New environment variables introduced since last tag

### Step 4 — Spawn release agent for rollback plan

```
Agent(
  subagent_type = "claude-tech-squad:release",
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
2. Deploy checklist — ordered steps to deploy safely
3. Required communications — who needs to know before/after deploy
4. Monitoring checklist — what to watch for 30 minutes post-deploy
5. GO / NO-GO assessment — is this release safe to deploy?

Return structured output. Do NOT chain to other agents.
"""
)
```

If release agent returns NO-GO: present blockers to user and halt. Do NOT proceed to tagging.

### Step 5 — Spawn SRE for blast radius assessment

```
Agent(
  subagent_type = "claude-tech-squad:sre",
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
- Pending migrations: {{yes/no}}

Proceed to tag and publish release notes? [Y/N]
```

**This is a blocking gate.** Do NOT create tag until user confirms.

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
