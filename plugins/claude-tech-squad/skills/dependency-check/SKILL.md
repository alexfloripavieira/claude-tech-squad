---
name: dependency-check
description: Checks project dependencies for vulnerabilities and outdated packages, categorizes findings by severity, and produces an upgrade plan. Trigger with "checar dependencias", "dependency check", "atualizar pacotes", "vulnerabilidades em deps".
user-invocable: true
---

# /dependency-check — Dependency Vulnerability and Update Check

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

### Step 3 — Categorize findings

Organize all findings into three categories:

1. **Security vulnerabilities (Critical)** — Known CVEs, exploitable issues
2. **Major version updates (Important)** — Breaking changes possible, review needed
3. **Minor/patch updates (Informative)** — Safe to upgrade, bug fixes and improvements

### Step 4 — Invoke planner agent for risk assessment

Use the Agent tool with `subagent_type: "claude-tech-squad:planner"`.

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
