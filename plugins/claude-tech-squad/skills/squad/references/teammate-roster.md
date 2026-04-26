# Teammate Roster — Full subagent_type Mappings

All spawns use: `Agent(team_name=<squad-team>, name=<role>, subagent_type="claude-tech-squad:<subagent>", prompt=...)`.

## Phase 1 — Discovery

Core discovery chain (stack-aware — use routing variables from Step 1):

| name | subagent_type |
|---|---|
| `pm` | `{{pm_agent}}` (e.g. `django-pm` for Django, `pm` otherwise) |
| `business-analyst` | `business-analyst` |
| `po` | `po` |
| `planner` | `planner` |
| `architect` | `architect` |
| `techlead` | `{{techlead_agent}}` (e.g. `django-tech-lead` for Django, `techlead` otherwise) |
| `design-principles` | `design-principles-specialist` |
| `test-planner` | `test-planner` |
| `tdd-specialist` | `tdd-specialist` |
| `llm-eval-specialist` | `llm-eval-specialist` |
| `llm-safety-reviewer` | `llm-safety-reviewer` |
| `llm-cost-analyst` | `llm-cost-analyst` |

Specialist batch (spawned based on TechLead requirements, any subset):

| name | subagent_type |
|---|---|
| `backend-arch` | `backend-architect` |
| `hexagonal-arch` | `hexagonal-architect` |
| `frontend-arch` | `frontend-architect` |
| `api-designer` | `api-designer` |
| `data-arch` | `data-architect` |
| `ux-designer` | `ux-designer` |
| `devops` | `devops` |
| `ci-cd` | `ci-cd` |
| `dba` | `dba` |
| `ai-engineer` | `ai-engineer` |
| `rag-engineer` | `rag-engineer` |
| `integration-engineer` | `integration-engineer` |
| `ml-engineer` | `ml-engineer` |
| `search-engineer` | `search-engineer` |
| `prompt-engineer` | `prompt-engineer` |
| `cloud-arch` | `cloud-architect` |
| `mobile-dev` | `mobile-dev` |

Quality baseline batch (always runs in parallel with specialist batch):

| name | subagent_type |
|---|---|
| `security-baseline` | `security-reviewer` |
| `privacy-baseline` | `privacy-reviewer` |
| `compliance-baseline` | `compliance-reviewer` |
| `perf-baseline` | `performance-engineer` |
| `observability-baseline` | `observability-engineer` |

All agents receive the full accumulated context from prior teammates. All architecture-sensitive agents also receive `{{architecture_style}}`. All review-sensitive agents also receive `{{lint_profile}}`. All agents end with: "Do NOT chain to other agents — the orchestrator handles sequencing."

## Phase 2 — Implementation

Stack-aware (use routing variables from Step 1):

| name | subagent_type |
|---|---|
| `tdd-impl` | `tdd-specialist` |
| `backend-dev` | `{{backend_agent}}` (e.g. `django-backend`, `python-developer`, or `backend-dev`) |
| `frontend-dev` | `{{frontend_agent}}` (e.g. `django-frontend`, `react-developer`, `vue-developer`, or `frontend-dev`) |
| `platform-dev` | `platform-dev` |
| `reviewer` | `{{reviewer_agent}}` (e.g. `code-reviewer` for Django, `reviewer` otherwise) |
| `qa` | `{{qa_agent}}` (e.g. `qa-tester` for web stacks, `qa` otherwise) |
| `techlead-audit` | `{{techlead_agent}}` |
| `security-rev` | `security-reviewer` |
| `privacy-rev` | `privacy-reviewer` |
| `perf-eng` | `performance-engineer` |
| `access-rev` | `accessibility-reviewer` |
| `integ-qa` | `integration-qa` |
| `code-quality` | `code-quality` |
| `docs-writer` | `docs-writer` |
| `jira-confluence` | `jira-confluence-specialist` |
| `pm-uat` | `{{pm_agent}}` |
