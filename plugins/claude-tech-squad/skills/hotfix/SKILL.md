---
name: hotfix
description: Streamlined emergency fix workflow for production issues. Skips discovery overhead — goes straight to root cause, minimal patch, tests, hotfix branch, PR, and deploy checklist. Trigger with "hotfix", "fix urgente", "producao quebrada", "patch emergencial", "emergency fix".
user-invocable: true
---

# /hotfix — Emergency Production Fix

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Deploy to production before the fix has been deployed and verified in staging (even in emergencies — staging takes minutes, a bad production deploy takes hours to recover)
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in production
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as an emergency workaround
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations to production without confirming a recent backup exists

**PII Safety:** Stack traces and logs may contain emails, user IDs, tokens, or credentials. Before passing any log content to agents: mask tokens (replace with `[REDACTED]`), mask email addresses, never pass raw database credentials or API keys. Agents must not store PII in their responses or in SEP logs.

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Lightweight emergency fix workflow. Faster than `/bug-fix` for known production breaks — skips root cause investigation overhead and goes straight to minimal patch → tests → branch → deploy.

**Use when:** production or staging is broken, you know approximately where, and speed matters.

**Escalate to `/squad` if:** the fix requires architectural changes, touches more than 5 files, or reveals a design flaw that needs proper scoping.

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

### Step 1 — Hotfix Intake Gate

Ask the user for (if not already provided):
1. **Symptom**: What is broken? (error, stack trace, user impact)
2. **Scope**: Which service, endpoint, or component?
3. **Deploy target**: Which environment needs the fix? (staging / production)
4. **Branch strategy**: What is the base branch for the hotfix? (default: `main` or `master`)

Do NOT proceed until scope and deploy target are confirmed. This is a blocking gate.

### Step 2 — Stack Command Detection (SEP Stack-Agnostic)

Read project files to detect test and build commands before spawning any agent:

| Signal file | test command | build command |
|---|---|---|
| `Makefile` with `test:` | `make test` | `make build` |
| `package.json` scripts | `npm test` | `npm run build` |
| `pyproject.toml` | `pytest` | n/a |
| `pom.xml` | `mvn test` | `mvn package` |
| `build.gradle` | `./gradlew test` | `./gradlew build` |

Store as `{{test_command}}` and `{{build_command}}`. CLAUDE.md overrides take priority.

### Step 3 — Create hotfix branch

```bash
git fetch origin
git checkout -b hotfix/{{slug}} origin/{{base_branch}}
```

Where `{{slug}}` is a short descriptor (e.g. `hotfix/null-pointer-checkout`).

Emit: `[Hotfix Branch] hotfix/{{slug}} created from {{base_branch}}`

### Step 4 — Spawn TechLead in root-cause mode

```
Agent(
  subagent_type = "claude-tech-squad:techlead",
  prompt = """
## Emergency Fix Investigation

### Symptom
{{symptom}}

### Scope
{{scope}}

### Stack trace / error (if available)
{{error}}

---
You are acting in rapid root-cause mode. Identify the root cause and the minimal change required to fix it.
Produce:
1. Root cause (1-3 sentences)
2. Minimal patch — exact files and lines to change
3. Risk: what could this change break?
4. Verification: how to confirm the fix works
Do NOT implement the fix. Return analysis only.
"""
)
```

Present root cause analysis to user before proceeding.

### Step 5 — Root cause confirmation gate

Present the diagnosis:

```
Root cause: {{root_cause}}
Proposed patch: {{patch_description}}
Risk: {{risk}}

Proceed with this fix? [Y/N/modify]
```

**This is a blocking gate.** Do NOT implement until user confirms.

### Step 6 — Spawn backend-dev or frontend-dev for minimal patch

Based on scope, spawn the appropriate implementation agent:

```
Agent(
  subagent_type = "claude-tech-squad:backend-dev",  # or frontend-dev, mobile-dev
  prompt = """
## Hotfix Implementation

### Root cause
{{root_cause}}

### Proposed patch
{{patch_description}}

### Constraints
- Minimal change only — do not refactor, do not clean up unrelated code
- Do not add new dependencies
- Do not change APIs or contracts unless the bug is in the contract itself

### Safety constraints (non-negotiable)
- Never force-push (`git push --force`) to any branch
- Never skip pre-commit hooks (`git commit --no-verify`)
- Never drop tables, databases, or truncate data without explicit user confirmation
- Never disable authentication or authorization as an emergency fix
- If the fix requires any of the above, STOP and report to the user before proceeding

### Test command
{{test_command}}

---
Implement the minimal fix. Write or update the test that proves the bug is fixed.
Run {{test_command}} and confirm PASS.

Run lint check: `{{lint_command}}` on changed files. If lint violations are found, fix before proceeding. If `{{lint_command}}` was not detected, skip and log.

Return:
## Completion Block
- Files changed: [list]
- Tests added/modified: [list]
- Test result: {{test_command}} → PASS/FAIL
- Test count: N passed, M failed
"""
)
```

Emit: `[Teammate Spawned] hotfix-impl | pane: hotfix-impl`

### Step 7 — Reviewer gate

Spawn reviewer for a lightweight review of the patch only:

```
Agent(
  subagent_type = "claude-tech-squad:reviewer",
  prompt = """
## Hotfix Review

### Root cause
{{root_cause}}

### Patch
{{implementation_output}}

---
This is an emergency fix. Review for:
1. Does the patch actually fix the root cause?
2. Does it introduce new bugs or regressions?
3. Is there a simpler, safer approach?

Return: APPROVED or CHANGES REQUESTED (with specific issues).
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] reviewer | pane: reviewer`

If CHANGES REQUESTED: spawn implementation agent again with feedback. Repeat until APPROVED.

### Step 8 — Security spot-check

If the bug involves auth, input handling, data access, or secret exposure, spawn security-reviewer:

```
Agent(
  subagent_type = "claude-tech-squad:security-reviewer",
  prompt = """
## Security Spot-Check — Hotfix

### Patch
{{approved_patch}}

---
Quick security check on this emergency fix.
Flag any: auth bypass, input injection, data exposure, or secret leakage.
Return: CLEAR or RISK with specific issue.
Do NOT chain.
"""
)
```

Skip this step if the bug is unrelated to security surface (UI layout, config typo, etc.).

If security-reviewer returns RISK:
- Emit: `[Gate] Security Risk Found | Issue: <summary>`
- Spawn the implementation agent again with the specific security issue as a fix mandate — do NOT advance until resolved
- Re-run security-reviewer after fix to confirm CLEAR
- If RISK persists after fix attempt: surface to user `[A]ccept risk (document) / [X]Abort`

### Step 9 — Commit and push

```bash
git add {{changed_files}}
git commit -m "hotfix: {{short_description}}"
git push origin hotfix/{{slug}}
```

### Step 10 — Open PR

```bash
gh pr create \
  --base {{base_branch}} \
  --head hotfix/{{slug}} \
  --title "hotfix: {{short_description}}" \
  --body "$(cat <<'EOF'
## Hotfix

### Root cause
{{root_cause}}

### Patch
{{patch_description}}

### Tests
- {{test_command}} → PASS (N passed)

### Deploy checklist
- [ ] Merge PR after approval
- [ ] Deploy to staging and verify
- [ ] Deploy to production
- [ ] Monitor for 15 minutes post-deploy
- [ ] Close incident if open
EOF
)"
```

Emit the PR URL to the user.

### Step 11 — Deploy checklist gate

Present the deploy checklist and ask:

```
Hotfix PR opened: {{pr_url}}

Deploy checklist:
- [ ] PR approved by at least one reviewer
- [ ] Hotfix deployed to STAGING — verify fix works in staging before production
- [ ] Staging verification confirmed (symptom no longer occurs, no new errors)
- [ ] Production deploy executed
- [ ] Post-deploy monitoring (15 min minimum — watch error rates, latency, logs)
- [ ] Incident resolved / on-call cleared

Ready to proceed? [Y] when each step is done.
```

**Mandatory staging gate:** Production deploy must NOT occur until staging deploy is confirmed working. Even in emergencies, a staging verification catches broken deploys before they compound the incident. Skipping staging requires the user to explicitly type "SKIP STAGING" with a reason — log this in the SEP log.

This is informational — the actual deploy is always a manual step. Do NOT attempt to deploy automatically.

### Step 12 — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-hotfix-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
parent_run_id: null
skill: hotfix
timestamp: {{ISO8601}}
status: completed
branch: hotfix/{{slug}}
pr_url: {{pr_url}}
base_branch: {{base_branch}}
root_cause_confirmed: true
reviewer_result: APPROVED
security_checked: true | skipped
postmortem_recommended: true
uat_result: N/A
---

## Root Cause
{{root_cause}}

## Patch Summary
{{patch_description}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 12b — Post-mortem prompt (proactive)

After the deploy checklist gate, always prompt for a post-mortem. Do NOT skip.

```
Hotfix concluído. Todo incidente de produção merece um post-mortem.

Quer iniciar agora?
- [S] Iniciar /incident-postmortem com contexto deste hotfix
- [N] Lembrar depois (registrado como pendente no SEP log)
```

If [S]: pass `parent_run_id: {{run_id}}` to the incident-postmortem run and invoke `/incident-postmortem` with the hotfix context pre-filled (symptom, root cause, patch, timeline).

If [N]: record `postmortem_recommended: true` in the SEP log so `/factory-retrospective` can detect hotfixes without associated post-mortems.

Emit: `[Gate] postmortem-prompt | Waiting for user input`

### Step 13 — Report to user

Tell the user:
- Root cause confirmed
- Files changed
- Tests: PASS (N passed)
- PR URL
- Deploy checklist status
- Any security findings (if security check ran)
