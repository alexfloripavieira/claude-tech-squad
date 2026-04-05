---
name: migration-plan
description: Plans database migrations by analyzing current migration state, detecting pending model changes, and producing a structured migration strategy with rollback plans. Trigger with "planejar migration", "migration plan", "mudanca de schema", "alterar modelo Django".
user-invocable: true
---

# /migration-plan — Database Migration Planning

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Apply migrations to production without confirming a recent backup exists and is restorable
- Run `migrate` (not `--dry-run`) against production or staging without explicit user authorization
- Delete cloud resources (S3 buckets, databases, clusters, queues) in any environment
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Destroy infrastructure via `terraform destroy` or equivalent IaC commands
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands

**Migration-specific rules:**
- Irreversible migrations (removing columns, changing types with data loss) MUST include a rollback script before the plan is marked complete
- Column removal must follow the add-first / dual-read / remove pattern across separate deploys
- Any migration touching more than 10 million rows must include a zero-downtime strategy

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Analyzes the current migration state, detects pending model changes, coordinates with data architecture and DBA specialists, and produces a safe migration plan with rollback strategy.

## When to Use

- Before any change to Django models.py
- When planning schema changes
- Before deploying migrations to staging/production
- When the user says: "planejar migration", "migration plan", "mudanca de schema", "alterar modelo Django"

## Execution

Follow these steps exactly:

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

### Step 1 — Map current migration state

Use Glob to list all migration files:
```
*/migrations/0*.py
**/migrations/0*.py
```

For each app with migrations, read the latest migration file to understand the current schema state.

### Step 2 — Analyze models for pending changes

Read `models.py` for each Django app that has migrations. Compare the model definitions against the latest migration to identify:
- New models
- New fields on existing models
- Changed field types or constraints
- Removed fields or models
- New indexes or constraints
- Changes to Meta options

### Step 3 — Check migration status via Django

Run via Bash:
```bash
python manage.py showmigrations --plan 2>/dev/null || docker compose exec django python manage.py showmigrations --plan 2>/dev/null || echo "showmigrations not available"
```

Also run:
```bash
python manage.py makemigrations --dry-run --check 2>/dev/null || docker compose exec django python manage.py makemigrations --dry-run --check 2>/dev/null || echo "makemigrations dry-run not available"
```

### Step 4 — Invoke data architect agent

Use TeamCreate to create a team named "migration-plan-team". Then spawn each agent using the Agent tool with `team_name="migration-plan-team"` and a descriptive `name` for each agent.

Use the Agent tool with `subagent_type: "claude-tech-squad:data-architect"`, `team_name: "migration-plan-team"`, `name: "data-architect"`.

Prompt:
```
You are the Data Architect agent. Design the migration strategy for the following changes.

Current migration state:
{{migration_files_summary}}

Pending model changes detected:
{{model_changes}}

Django showmigrations output:
{{showmigrations_output}}

Multi-database setup (if applicable):
{{db_setup_notes}}

Produce:
1. List of migrations needed, in dependency order
2. Whether each migration is safe for zero-downtime deployment
3. Data migration needs (if structural changes affect existing data)
4. Dependency graph between migrations
```

### Step 5 — Invoke DBA agent for safety review

Use the Agent tool with `subagent_type: "claude-tech-squad:dba"`, `team_name: "migration-plan-team"`, `name: "dba"`.

Prompt:
```
You are the DBA agent. Review the proposed migration plan for safety.

Proposed migrations:
{{data_architect_output}}

Evaluate:
1. Table locking risks (ALTER TABLE on large tables)
2. Rollback feasibility for each migration
3. Impact on existing data (NULL defaults, type conversions)
4. Index creation strategy (CONCURRENTLY when possible)
5. Estimated downtime or performance impact
6. Safe deployment sequence
```

### Step 5b — Backup verification gate (mandatory for staging/production)

Before producing the final plan, ask the user:

```
This migration plan will be applied to a real database. Before proceeding:

1. Is there a recent backup of the target database?
   - What is the backup date/time?
   - Where is it stored and has it been verified (restore-tested)?

2. What environment will this migration run in first? (local / staging / production)

Provide backup confirmation before the plan is finalized. This is a blocking gate.
```

For local-only development migrations, the user may skip this gate by responding "local dev only".

For any migration rated **High risk** (irreversible column removal, type change with data loss, table with >1M rows), also require:
- Written rollback script path (`ai-docs/rollback-{{migration}}.sql`)
- Confirmation that the rollback was tested on a copy of production data

### Step 6 — Produce migration plan

Generate a structured plan:

```markdown
# Migration Plan — YYYY-MM-DD

## Summary
- Apps affected: [list]
- Migrations needed: N
- Risk level: Low / Medium / High
- Estimated downtime: None / Brief / Significant

## Migrations

### Migration 1: app_name/NNNN_description.py
- **Type:** Schema / Data / Mixed
- **Changes:** ...
- **Locking risk:** None / Low / High (table size: ~N rows)
- **Rollback:** Safe / Requires data migration / Irreversible
- **Dependencies:** [list]

### Migration 2: ...

## Execution Plan

### Pre-deployment
1. Backup database: `pg_dump ...`
2. ...

### Deployment sequence
1. `python manage.py migrate app_name NNNN`
2. ...

### Rollback procedure
1. `python manage.py migrate app_name NNNN_previous`
2. ...

## Risks and Mitigations
| Risk | Severity | Mitigation |
|------|----------|------------|

## Commands Reference
```

### Step 6b — Reviewer Gate

Before saving, spawn reviewer to validate the migration plan:

```
Agent(
  subagent_type = "claude-tech-squad:reviewer",
  team_name = "migration-plan-team",
  name = "reviewer",
  prompt = """
## Migration Plan Review

### Migration Plan
{{migration_plan}}

### Data Architect Analysis
{{data_architect_output}}

### DBA Safety Review
{{dba_output}}

---
Review this migration plan for:
1. Rollback scripts — are they syntactically correct and will they work under load?
2. Migration ordering — is the sequence safe? Any dependency issues?
3. Data validation steps — are they present for data migrations?
4. Locking risks — are table locks properly addressed for large tables?
5. Irreversible operations — are they clearly flagged with tested rollback alternatives?

Return: APPROVED or CHANGES REQUESTED with specific issues.
Do NOT chain.
"""
)
```

If CHANGES REQUESTED: address the specific issues in the migration plan and re-run reviewer. Max 2 review cycles.

Emit: `[Gate] Migration Plan Reviewer APPROVED | Advancing to save`

### Step 7 — Save plan

Create the `ai-docs/` directory if it does not exist. Write the plan to:
```
ai-docs/migration-plan-YYYY-MM-DD.md
```

### Step 7b — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-migration-plan-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: migration-plan
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [preflight-passed, plan-drafted, risks-reviewed]
fallbacks_invoked: []
migrations_planned: N
risk_level: Low | Medium | High
reviewer_result: APPROVED
dba_result: APPROVED
backup_verified: true | skipped (local dev)
plan_path: ai-docs/migration-plan-YYYY-MM-DD.md
---

## Migration Summary
{{one_paragraph_summary}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 8 — Report to user

Tell the user:
- Number of migrations needed and affected apps
- Overall risk level
- Any high-risk operations that require special attention
- Path to the saved plan
- Recommended next steps
