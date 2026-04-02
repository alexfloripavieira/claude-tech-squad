---
name: dependency-check
description: Checks project dependencies for vulnerabilities and outdated packages, categorizes findings by severity, and produces an upgrade plan. Trigger with "checar dependencias", "dependency check", "atualizar pacotes", "vulnerabilidades em deps".
user-invocable: true
---

# /dependency-check — Dependency Vulnerability and Update Check

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources (S3 buckets, databases, clusters, queues) in any environment
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Remove secrets or environment variables from production
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Disable or bypass authentication/authorization as a workaround
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands
- Apply migrations or schema changes to production without first verifying a backup exists
- Auto-upgrade packages to major versions without presenting a breaking-changes summary first

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Detects package managers, runs real vulnerability and outdated-package checks, categorizes findings by severity, and produces a prioritized upgrade plan.

## When to Use

- Periodic dependency maintenance
- Before releases or security reviews
- When evaluating upgrade risk
- When the user says: "checar dependencias", "dependency check", "atualizar pacotes", "vulnerabilidades em deps"

## Execution

Follow these steps exactly:

### Step 1 — Detect package managers

Read the following files to determine which package managers are in use:

- `pyproject.toml` (Poetry or pip with PEP 621)
- `requirements.txt`, `requirements/*.txt` (pip)
- `Pipfile` (pipenv)
- `package.json` (npm)
- `yarn.lock` (yarn)
- `pnpm-lock.yaml` (pnpm)

Record all detected managers and their lock files.

### Step 2 — Run vulnerability checks via Bash

**Python dependency vulnerabilities:**
```bash
pip-audit --format=text 2>/dev/null || safety check 2>/dev/null || echo "TOOL_NOT_AVAILABLE: pip-audit/safety"
```

**Python outdated packages:**
```bash
pip list --outdated --format=columns 2>/dev/null || echo "TOOL_NOT_AVAILABLE: pip list --outdated"
```

**JavaScript vulnerabilities:**
```bash
npm audit 2>/dev/null || echo "TOOL_NOT_AVAILABLE: npm audit"
```

**JavaScript outdated packages:**
```bash
npm outdated 2>/dev/null || echo "TOOL_NOT_AVAILABLE: npm outdated"
```

**Yarn (if detected):**
```bash
yarn audit 2>/dev/null || echo "TOOL_NOT_AVAILABLE: yarn audit"
yarn outdated 2>/dev/null || echo "TOOL_NOT_AVAILABLE: yarn outdated"
```

### Step 2b — Supply chain safety check

For any new or recently added packages (added since the last dependency check or the last git tag), run additional supply chain verification:

```bash
# New packages since last tag (git-based)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  git diff ${LAST_TAG}..HEAD -- requirements*.txt package.json pyproject.toml 2>/dev/null | grep "^+" | grep -v "^+++" | head -30
else
  echo "NO_LAST_TAG"
fi
```

For each newly added package, check:
- **Typosquatting risk**: Is the package name suspiciously similar to a well-known package? (e.g. `requets` vs `requests`, `lodahs` vs `lodash`)
- **Minimal publish history**: Was this package published very recently (< 6 months) with no prior release history?
- **Unusual permissions requested**: Does the package's install scripts request network access, file system writes outside of its directory, or shell execution?

If any supply chain risk is detected, emit a `[Supply Chain Warning]` and include it in the Critical findings category.

### Step 3 — Categorize findings

Organize all findings into four categories:

1. **Supply chain risks (Critical)** — Typosquatting, malicious packages, suspicious new packages
2. **Security vulnerabilities (Critical)** — Known CVEs, exploitable issues
3. **Major version updates (Important)** — Breaking changes possible, review needed
4. **Minor/patch updates (Informative)** — Safe to upgrade, bug fixes and improvements

### Step 4 — Invoke planner agent for risk assessment

Use TeamCreate to create a team named "dependency-check-team". Then spawn the agent using the Agent tool with `team_name="dependency-check-team"` and a descriptive `name`.

Use the Agent tool with `subagent_type: "claude-tech-squad:planner"`, `team_name: "dependency-check-team"`, `name: "planner"`.

Prompt:
```
You are the Planner agent. Assess the risk of upgrading the following dependencies.

Security vulnerabilities found:
{{vulnerabilities}}

Major version updates available:
{{major_updates}}

Minor/patch updates available:
{{minor_updates}}

Project stack and framework versions:
{{stack_info}}

For each security vulnerability and major update, evaluate:
1. Upgrade urgency (immediate / soon / when convenient)
2. Breaking change risk (high / medium / low)
3. Known compatibility issues with the project's framework version
4. Recommended upgrade strategy (direct upgrade / staged / pin version)
5. Testing requirements after upgrade
```

### Step 5 — Produce report

Generate a structured report:

```markdown
# Dependency Check Report — YYYY-MM-DD

## Summary
- Security vulnerabilities: N (Critical: N, High: N, Medium: N, Low: N)
- Major updates available: N packages
- Minor/patch updates available: N packages
- Tools executed: [list]
- Tools not available: [list]

## Security Vulnerabilities

### [CVE-YYYY-NNNNN] package-name
- **Current version:** X.Y.Z
- **Fixed in:** A.B.C
- **Severity:** Critical / High / Medium / Low
- **Description:** ...
- **Upgrade command:** `pip install package==A.B.C` or `npm install package@A.B.C`

## Major Updates (Breaking Changes Possible)

| Package | Current | Latest | Risk | Notes |
|---------|---------|--------|------|-------|

## Minor/Patch Updates (Safe)

| Package | Current | Latest | Type |
|---------|---------|--------|------|

## Recommended Upgrade Plan

### Phase 1: Security fixes (immediate)
```bash
# Commands to run
```

### Phase 2: Major upgrades (planned)
```bash
# Commands to run
```

### Phase 3: Minor/patch updates (maintenance)
```bash
# Commands to run
```

## Testing Checklist
- [ ] Run full test suite after Phase 1
- [ ] ...
```

### Step 5b — Write Remediation Tasks (SEP Contrato 2)

Write a companion remediation tasks file for actionable follow-up.

Write to `ai-docs/dependency-remediation-YYYY-MM-DD.md`:

```markdown
# Dependency Remediation Tasks — YYYY-MM-DD

> Auto-generated by /dependency-check. Check off items as they are resolved.

## Phase 1 — Security fixes (immediate)
- [ ] [CVE-YYYY-NNNNN] {{package}} {{current}} → {{fixed_version}} — `{{upgrade_command}}`

## Phase 2 — Major upgrades (planned)
- [ ] {{package}} {{current}} → {{latest}} — review breaking changes first

## Phase 3 — Minor/patch updates (maintenance)
- [ ] {{package}} {{current}} → {{latest}} — safe to upgrade

## Metadata
- Check date: YYYY-MM-DD
- Full report: ai-docs/dependency-check-YYYY-MM-DD.md
- Status: open
```

Also write the execution log:

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-dependency-check-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: dependency-check
timestamp: {{ISO8601}}
status: completed
vulnerabilities_critical: N
major_updates: N
remediation_artifact: ai-docs/dependency-remediation-YYYY-MM-DD.md
---

## Findings Gerados
{{list_critical_vulnerabilities_one_line_each}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
Emit: `[Remediation Tasks Written] ai-docs/dependency-remediation-YYYY-MM-DD.md`

### Step 6 — Save report

Create the `ai-docs/` directory if it does not exist. Write the report to:
```
ai-docs/dependency-check-YYYY-MM-DD.md
```

### Step 7 — Report to user

Tell the user:
- Total vulnerabilities by severity
- Most urgent upgrades (top 3)
- Which tools ran successfully and which were not available
- Path to the saved report
- Recommended immediate actions
