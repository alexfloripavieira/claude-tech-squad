---
name: migration-plan
description: Plans database migrations by analyzing current migration state, detecting pending model changes, and producing a structured migration strategy with rollback plans. Trigger with "planejar migration", "migration plan", "mudanca de schema", "alterar modelo Django".
user-invocable: true
---

# /migration-plan — Database Migration Planning

Analyzes the current migration state, detects pending model changes, coordinates with data architecture and DBA specialists, and produces a safe migration plan with rollback strategy.

## When to Use

- Before any change to Django models.py
- When planning schema changes
- Before deploying migrations to staging/production
- When the user says: "planejar migration", "migration plan", "mudanca de schema", "alterar modelo Django"

## Execution

Follow these steps exactly:

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

Use the Agent tool with `subagent_type: "claude-tech-squad:data-architect"`.

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

Use the Agent tool with `subagent_type: "claude-tech-squad:dba"`.

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

### Step 7 — Save plan

Create the `ai-docs/` directory if it does not exist. Write the plan to:
```
ai-docs/migration-plan-YYYY-MM-DD.md
```

### Step 8 — Report to user

Tell the user:
- Number of migrations needed and affected apps
- Overall risk level
- Any high-risk operations that require special attention
- Path to the saved plan
- Recommended next steps
