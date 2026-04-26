# Gate Catalog — `/discovery`

| Step | Gate                          | Consumes                              | Emits                  | Auto-advance? |
|------|-------------------------------|---------------------------------------|------------------------|---------------|
| 0    | Preflight Gate                | runtime-policy.yaml                   | preflight_pass         | No            |
| 1    | Problem Intake                | user prompt                           | problem_brief          | No            |
| 2    | PRD Author                    | problem_brief                         | prd_artifact           | Conditional   |
| 3    | Business Analyst              | prd_artifact                          | business_rules         | Conditional   |
| 4    | TechSpec / Inception Author   | prd_artifact + business_rules         | techspec_artifact      | No            |
| 5    | Architect Lens                | techspec_artifact                     | architecture_decisions | No            |
| 6    | Specialist Slice (parallel)   | architecture_decisions                | slice_designs          | Conditional   |
| 7    | Test Planner                  | techspec + slices                     | test_plan              | No            |
| 8    | TDD Specialist (delivery plan)| test_plan                             | tdd_delivery_plan      | No            |
| 9    | Tasks Planner                 | full chain                            | tasks_artifact         | No            |
| 10   | Operator Sign-off             | full chain                            | discovery_ack          | Operator only |
| 11   | SEP Log Write                 | full run trace                        | sep_log_path           | Always        |

Auto-advance is governed by `runtime-policy.yaml.auto_advance.eligible_gates` and the standard rule: all consumed ARCs `high` confidence + zero BLOCKING findings.

## Gate 0 — Scope Confirmation (Step 2b)

Triggered before spawning PM if any of: ticket title contains both "v1" and "v2" (or multiple version refs); user request mentions "and also" / "plus" / lists 3+ distinct features; ticket has subtasks spanning different modules or APIs.

When triggered, present:

```
[Gate] Scope Confirmation

The task appears to involve multiple scopes:
- {{scope_a}}
- {{scope_b}}

Which scope should this discovery cover?
[1] {{scope_a}} only
[2] {{scope_b}} only
[A] Both (larger discovery)
```

Store the decision as `{{confirmed_scope}}` and pass to PM. If no ambiguity is detected, skip silently — do not ask unnecessary questions.

## Gate 1 — Product Definition (PM, Step 3)

- ≥3 measurable acceptance criteria defined
- Scope is bounded (no open-ended "and anything else needed")
- Success metrics are observable (testable behavior, not feelings)

If user is unsatisfied: ask what is missing, re-spawn PM with that gap as context.

## Gate 2 — Scope Validation (PO, Step 5)

- Scope cut is explicit — what is OUT is listed
- Must-have vs nice-to-have distinction is clear
- Release slice fits a single deployment

## Gate 3 — Technical Tradeoffs (Planner, Step 6)

- ≥2 technical options were presented
- Selected option has rationale (not just "best practice")
- Breaking changes / migration risks identified

## Gate 4 — Architecture Direction (TechLead, Step 8)

- Workstream ownership assigned (who builds what)
- Sequencing explicit (what blocks what)
- Architecture-layer violations flagged or cleared

## Auth-Sensitive HARD Gate (Step 10)

If feature touches authentication, magic-link/OTP, OAuth/SSO, password reset, account recovery, impersonation, or session token storage/refresh/revocation, `security-reviewer` is a HARD gate — CANNOT be skipped-with-risk and CANNOT be auto-advanced. Run waits for `security-reviewer` output with status APPROVED or BLOCKED. Record `auth_touching_feature: true` and `security_reviewer_gate: hard` in SEP frontmatter.

## Final Gate — Blueprint Confirmation (TDD Specialist, Step 13)

User confirms the TDD Delivery Plan to mark discovery complete.

## Discovery → Implement Bridge Gate (Step 15)

Always presented immediately after the SEP log is written:

```
Blueprint salvo em ai-docs/{{feature_slug}}/blueprint.md

Próximo passo: /implement ai-docs/{{feature_slug}}/blueprint.md

Quer iniciar a implementação agora? [S/N]
```

- **S**: set `implement_triggered: true` in the SEP log via Edit tool, then invoke `/implement` with the blueprint path.
- **N**: leave `implement_triggered: false` and populate `implement_deferred_reason` (mandatory — empty/missing means orphaned discovery in factory-retrospective). Write `tasks/pending-implement-{{feature_slug}}.md` so the blueprint is not lost.

Emit `[Gate] implement-bridge | Waiting for user input`.
