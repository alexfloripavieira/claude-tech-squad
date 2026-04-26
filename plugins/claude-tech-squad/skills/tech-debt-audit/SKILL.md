---
name: tech-debt-audit
description: This skill should be used when the team needs a deep, multi-lens tech debt audit across code, architecture, data, performance, security, and dependencies, resulting in a prioritized debt register and remediation plan. Trigger with "auditar divida tecnica", "tech debt audit", "deep tech debt analysis", "code health report", "analise de divida tecnica". NOT for fixing debt directly (use /refactor or /implement).
user-invocable: true
---

# /tech-debt-audit — Deep Tech Debt Analysis

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

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

**Additional constraint for tech-debt audit:** This skill is **read-only**. No agent may write code, config, or migrations. The skill produces debt registers and remediation plans only. Operators invoke `/refactor`, `/implement`, or `/squad` separately to act on the findings.

## When to Use

- Quarterly or pre-release codebase health assessment
- Before planning a major refactor or rearchitecture
- After a velocity drop or rising bug rate is observed
- When the user says: "auditar divida tecnica", "tech debt audit", "deep tech debt analysis", "code health report"

## When NOT to Use

- Single-PR review — use `reviewer` or `code-reviewer` agent
- Lint cleanup — use `pre-commit-lint` skill
- Security-only audit — use `/security-audit`
- Dependency-only check — use `/dependency-check`
- Acting on debt — use `/refactor` (for one module) or `/squad` (for cross-cutting work)

## Execution

Follow these steps exactly.

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
- [S] Skip and continue — analyst will note the missing lens in the final report
- [X] Abort the run
```

4. **Parallel batch teammates:** [S] on one specialist does not block the batch. The analyst (final step) MUST flag any missing lens as a confidence reducer in the executive summary.
5. **Do NOT advance to the analyst synthesis step** until every specialist has returned, been explicitly skipped, or the run has been aborted.

## Visual Reporting Contract

- After every teammate returns, pipe its Result Contract `metrics` JSON to `plugins/claude-tech-squad/scripts/render-teammate-card.sh` and print the card inline. Respect `observability.teammate_cards.format` (ascii | compact | silent) from `runtime-policy.yaml`.
- Immediately before writing the SEP log, assemble the pipeline summary JSON (schema identical to `scripts/test-fixtures/pipeline-board-input.json`) and pipe to `plugins/claude-tech-squad/scripts/render-pipeline-board.sh`. Respect `observability.pipeline_board.enabled`.
- Renderer failures are non-fatal: log a WARNING in the SEP log and continue.

### Step 0a — Remediation Triage Checkpoint (blocking)

Before any other work, compute the close-rate across prior `ai-docs/tech-debt-remediation-*.md` files (the trackable backlog with `- [ ]` / `- [x]` checkboxes — the register snapshot at `ai-docs/tech-debt-*.md` is not closeable).

```bash
TOTAL_OPEN=$(grep -h "^- \[ \].*CRITICAL\|^- \[ \].*HIGH" ai-docs/tech-debt-remediation-*.md 2>/dev/null | wc -l)
TOTAL_CLOSED=$(grep -h "^- \[x\].*CRITICAL\|^- \[x\].*HIGH" ai-docs/tech-debt-remediation-*.md 2>/dev/null | wc -l)
TOTAL=$((TOTAL_OPEN + TOTAL_CLOSED))
if [ "$TOTAL" -gt 0 ]; then
  CLOSE_RATE=$((TOTAL_CLOSED * 100 / TOTAL))
else
  CLOSE_RATE=100
fi
echo "close_rate=${CLOSE_RATE}% open=${TOTAL_OPEN} closed=${TOTAL_CLOSED}"
```

**If close-rate < 40%:** the backlog is stagnant. Emit:

```
[Gate] Tech Debt Doom Loop Detected | close_rate={{rate}}% | open_critical_high={{open}}
A new audit would add findings without closing the backlog. This run is BLOCKED until:
- [Q] Invoke /claude-tech-squad:squad on the recurring CRITICAL/HIGH findings (mandatory recommendation)
- [O] Override — provide explicit reason to be recorded in SEP log under `doom_loop_override_reason`
- [X] Abort this audit
```

If [Q]: exit cleanly and instruct the user to run `/claude-tech-squad:squad "Address recurring CRITICAL/HIGH tech-debt findings"`. If [O]: record `doom_loop_override_reason` in the SEP log and continue. If [X]: abort.

If no prior register exists, skip this gate silently and continue.

Emit: `[Remediation Triage] passed | close_rate={{rate}}% | action={{continued|overridden|aborted}}`

### Step 1 — Preflight Gate

Emit `[Preflight Start] tech-debt-audit`

**python3 plugins/claude-tech-squad/bin/squad-cli accelerated preflight** (preferred — saves ~5K tokens):

```bash
python3 plugins/claude-tech-squad/bin/squad-cli preflight --skill tech-debt-audit --policy plugins/claude-tech-squad/runtime-policy.yaml --project-root .
```

If `squad-cli` is not available, fall back to manual preflight: read `runtime-policy.yaml`, detect stack from signal files, check the retro counter.

Emit `[Preflight Passed] tech-debt-audit | execution_mode=teammates | runtime_policy=<version>`

### Step 2 — Recurring/Regressed Detection (read-only)

Before spawning specialists, scan for prior tech-debt artifacts so the analyst can tag NEW vs. RECURRING vs. REGRESSED:

```bash
PRIOR_REGISTERS=$(ls ai-docs/tech-debt-*.md 2>/dev/null | sort -r | head -3)
echo "Prior registers: ${PRIOR_REGISTERS:-NONE}"

# Most-changed files in the last 180 days (drives change_frequency scoring)
git log --since=180.days.ago --name-only --pretty=format: 2>/dev/null | sort | uniq -c | sort -rn | head -50 > /tmp/tech-debt-churn.txt
```

Capture the prior register paths and the churn list — they will be passed to every specialist and to the final analyst.

Emit: `[Preflight Context] prior_registers={{count}} churn_window=180d`

### Step 3 — Create Audit Team

Use TeamCreate to create a team named "tech-debt-audit-team":

```
TeamCreate(name="tech-debt-audit-team", description="Deep tech debt audit run for: {{repo_or_module_target}}")
```

Emit: `[Team Created] tech-debt-audit-team`

### Step 4 — Specialist Lenses (Parallel)

Spawn the 5 specialist lens agents in parallel. Each receives the same shared context (prior registers list, churn list, target scope) plus a lens-specific prompt.

```
Agent(team_name="tech-debt-audit-team", name="code-quality",
      subagent_type="claude-tech-squad:code-quality",
      prompt=<code lens prompt>)

Agent(team_name="tech-debt-audit-team", name="design-principles",
      subagent_type="claude-tech-squad:design-principles-specialist",
      prompt=<architecture lens prompt>)

Agent(team_name="tech-debt-audit-team", name="dba",
      subagent_type="claude-tech-squad:dba",
      prompt=<data lens prompt>)

Agent(team_name="tech-debt-audit-team", name="performance",
      subagent_type="claude-tech-squad:performance-engineer",
      prompt=<performance lens prompt>)

Agent(team_name="tech-debt-audit-team", name="security",
      subagent_type="claude-tech-squad:security-reviewer",
      prompt=<security debt lens prompt>)
```

Each lens prompt must include:
- The audit scope (full repo or specific module)
- The 180-day churn list (`/tmp/tech-debt-churn.txt` contents)
- Prior register paths (if any)
- Explicit instruction: "Return debt items only — do not propose code edits. Use `file:line` references. Tag each item with category (`code|arch|data|perf|sec`) and a draft severity (critical|high|medium|low). The tech-debt-analyst will produce final scoring and the canonical register."

Emit: `[Batch Spawned] tech-debt-lenses | Teammates: code-quality, design-principles, dba, performance, security`

### Step 5 — Lens Result Consolidation Gate

Wait for all 5 specialists to return. Validate every output:
- Has `result_contract` block
- Has at least one debt finding OR explicit "no debt found in scope"
- All findings include `file:line` (or `module` for architectural items)

If a lens returns invalid output, follow the Teammate Failure Protocol above. If a lens is finally [S]kipped, record `<lens>_skipped: true` in the SEP log so the analyst can lower confidence appropriately.

Emit: `[Gate Passed] lens-consolidation | lenses_returned={{N}} | lenses_skipped={{M}}`

### Step 6 — Tech Debt Analyst Synthesis

Spawn the analyst as a single sequential teammate after all lens outputs are collected:

```
Agent(team_name="tech-debt-audit-team", name="tech-debt-analyst",
      subagent_type="claude-tech-squad:tech-debt-analyst",
      prompt=<analyst prompt>)
```

The analyst prompt MUST include:
- Full output from each of the 5 lenses (or "skipped" marker for skipped ones)
- Full content of the most recent prior debt register (if any) for RECURRING/REGRESSED tagging
- The 180-day churn list
- Skipped-lens markers so the analyst can lower confidence accordingly
- Explicit instruction: "Synthesize into one canonical debt register. Score every item by `blast_radius x change_frequency x complexity`. Detect hotspots (≥ 3 categories overlap). Build ROI-ordered remediation plan for CRITICAL and HIGH only. Identify systemic categories (close-rate < 30% over last 3 audits). Do NOT duplicate lens findings — synthesize."

Emit: `[Analyst Spawned] tech-debt-analyst`

### Step 7 — Analyst Output Validation Gate

Validate the analyst output before writing artifacts:
- Executive summary present (severity counts, hotspots, recurring/regressed counts, top 3 risks)
- Debt register has stable IDs (`DEBT-CODE-001`, `DEBT-ARCH-001`, etc.)
- Every CRITICAL/HIGH item has a first-cut remediation and effort size
- Hotspot map present (or explicitly "no hotspots detected")
- ROI-ordered plan covers all CRITICAL and HIGH items
- `result_contract` and `verification_checklist` blocks present and valid

If any validation fails, re-spawn the analyst once with explicit instruction listing the missing fields. If second attempt also fails, surface to the user.

Emit: `[Gate Passed] analyst-output | items={{total}} | critical={{N}} | high={{M}} | hotspots={{H}}`

### Step 8 — Write Debt Register Artifact

Write the canonical debt register:

```bash
mkdir -p ai-docs
```

Write to `ai-docs/tech-debt-YYYY-MM-DD.md`:

```markdown
# Tech Debt Register — YYYY-MM-DD

> Auto-generated by /tech-debt-audit. Read-only output.
> To act on findings, invoke `/refactor <module>` (single hotspot) or `/squad "Address systemic <category> debt"` (cross-cutting).

## Executive Summary
{{counts_by_severity}}
{{hotspot_count}}
{{recurring_regressed_counts}}
{{top_3_risks}}

## Debt Register

| ID | Category | File:Line | Score | Severity | Status | Description | First-Cut | Effort |
|---|---|---|---|---|---|---|---|---|
{{rows}}

## Hotspot Map

{{files_and_modules_with_3_or_more_category_overlap}}

## ROI-Ordered Remediation Plan (CRITICAL + HIGH)

| Rank | Item ID | Risk Reduction | Velocity Unblock | Effort | ROI Score |
|---|---|---|---|---|---|
{{rows}}

## Systemic Findings (close-rate < 30%)

{{categories_recommending_squad_intervention}}

## Frozen Complexity (informational — no action required)

{{high_complexity_unchanged_12mo}}

## Trend

| Category | NEW | RECURRING | REGRESSED | Close-rate (last 3 audits) |
|---|---|---|---|---|
{{rows}}

## Audit Metadata
- Audit date: YYYY-MM-DD
- Lenses returned: {{returned_lenses}}
- Lenses skipped: {{skipped_lenses}}
- Confidence: {{analyst_confidence}}
- Prior registers consulted: {{prior_registers_paths}}
```

Emit: `[Debt Register Written] ai-docs/tech-debt-YYYY-MM-DD.md`

### Step 8b — Write Remediation Tasks (closeable checklist)

Also write a companion remediation checklist file with `- [ ]` / `- [x]` items so the doom-loop gate (Step 0a) can compute close-rate accurately. The register itself is a snapshot; the remediation file is the trackable backlog.

Write to `ai-docs/tech-debt-remediation-YYYY-MM-DD.md`:

```markdown
# Tech Debt Remediation Tasks — YYYY-MM-DD

> Auto-generated by /tech-debt-audit. Check off items as they are resolved.
> Re-run /tech-debt-audit after closing Phase 1 items to refresh the close-rate.

> **Assignee rule (MANDATORY):** every action item MUST carry an `@assignee` tag. Items without an assignee are rejected.

## Phase 1 — Critical (score >= 60)
- [ ] [DEBT-CODE-001] CRITICAL {{finding_title}} — {{file}}:{{line}} @assignee
- [ ] [DEBT-ARCH-001] CRITICAL {{finding_title}} — {{file}}:{{line}} @assignee

## Phase 2 — High (score 30-59)
- [ ] [DEBT-DATA-001] HIGH {{finding_title}} — {{file}}:{{line}} @assignee
- [ ] [DEBT-PERF-001] HIGH {{finding_title}} — {{file}}:{{line}} @assignee

## Phase 3 — Medium / Low (score < 30)
- [ ] [DEBT-CODE-002] MEDIUM {{finding_title}} — {{file}}:{{line}} @assignee

## Audit Metadata
- Audit date: YYYY-MM-DD
- Full register: ai-docs/tech-debt-YYYY-MM-DD.md
- Status: open
```

Emit: `[Remediation Tasks Written] ai-docs/tech-debt-remediation-YYYY-MM-DD.md`

### Step 9a — Team Cleanup (before SEP log)

Clean up the team created at Step 3 before writing the SEP log so cleanup status can be recorded:

```
TeamDelete(name="tech-debt-audit-team")
```

Capture outcome into `{{team_cleanup_status}}` (`success` or `failed: <reason>`). On failure, do not halt — emit a warning and continue:

- On success: emit `[Team Deleted] tech-debt-audit-team | cleanup complete`
- On failure: emit `[Team Cleanup Warning] tech-debt-audit-team | <reason>`

### Step 9b — Temp file cleanup (before SEP log)

Remove the per-run temp file used during the analysis so the SEP log can record the cleanup outcome:

```bash
rm -f /tmp/tech-debt-churn.txt
```

Capture outcome into `{{temp_cleanup_status}}` (`success` or `failed: <reason>`). Cleanup failures are non-fatal — emit a warning and continue.

- On success: emit `[Temp Files Cleaned] tech-debt-audit | 1 file removed`
- On failure: emit `[Temp Cleanup Warning] tech-debt-audit | <reason>`

### Step 9c — Write SEP log

Write the execution log to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-tech-debt-audit-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: tech-debt-audit
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}
status: completed
final_status: completed
execution_mode: teammates
architecture_style: n/a
checkpoints: [preflight-passed, lens-consolidation-passed, analyst-output-passed, register-written]
fallbacks_invoked: []
lenses_returned: {{N}}
lenses_skipped: {{M}}
total_debt_items: {{total}}
items_critical: {{N}}
items_high: {{N}}
items_medium: {{N}}
items_low: {{N}}
hotspots: {{H}}
recurring_count: {{R}}
regressed_count: {{G}}
systemic_categories: {{list}}
analyst_confidence: high | medium | low
register_artifact: ai-docs/tech-debt-YYYY-MM-DD.md
remediation_artifact: ai-docs/tech-debt-remediation-YYYY-MM-DD.md
developer_feedback: {{one_line_text_or_null}}   # captured at end-of-run from operator if provided
tokens_input: {{actual_or_null}}
tokens_output: {{actual_or_null}}
estimated_cost_usd: {{usd}}
total_duration_ms: {{ms}}
team_cleanup_status: {{team_cleanup_status}}
temp_cleanup_status: {{temp_cleanup_status}}
---

## Top Findings
{{top_5_critical_or_high_items_one_line_each}}
```

When writing manually, substitute every `{{...}}` placeholder with the captured value — including `{{team_cleanup_status}}` from Step 9a (use `success` or `failed: <reason>`; never leave the literal placeholder).

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 10 — Report to User

Tell the user:
- Total debt items by severity
- Top 3 hotspots (file:line) with their overlapping categories
- Recurring and regressed counts
- Systemic categories recommending `/squad` intervention
- Path to the saved debt register
- Suggested next action: `/refactor <hotspot_module>` for the highest-ROI hotspot, or `/squad "Address systemic <category> debt"` for systemic patterns

Do NOT propose code edits. The skill ends after the report — operators decide which remediation skill to invoke next.
