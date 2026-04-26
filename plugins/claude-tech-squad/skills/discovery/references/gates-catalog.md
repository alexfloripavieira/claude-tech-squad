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
