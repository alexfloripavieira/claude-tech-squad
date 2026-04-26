# Teammate Roster — `/implement`

Full roster of teammates spawned by `/implement`, organized by phase. The SKILL.md keeps a short summary; this file holds the per-teammate prompt scaffolding and Progressive Disclosure rules.

## Phase 0 — Delivery docs

| Teammate | subagent_type | Receives | Returns |
|---|---|---|---|
| tasks-planner | claude-tech-squad:tasks-planner | PRD path, TechSpec path, slug | tasks.md |
| work-item-mapper | claude-tech-squad:work-item-mapper | tasks digest, taxonomy from runtime-policy | work-items.md |

## Phase 1 — TDD

| Teammate | subagent_type | Receives | Returns |
|---|---|---|---|
| tdd-specialist | claude-tech-squad:tdd-specialist | full TDD plan, full test plan, architecture digest | failing tests + run cmd |

Progressive Disclosure: full TDD/test plan, digest of architecture (max 500 tokens).

## Phase 2 — Implementation batch (parallel)

| Teammate | subagent_type | Receives | Returns |
|---|---|---|---|
| backend-dev | claude-tech-squad:{{backend_agent}} | full failing tests + workstream + commands | code + completion block |
| frontend-dev | claude-tech-squad:{{frontend_agent}} | same | same |
| platform-dev | claude-tech-squad:platform-dev | same (only if queues/workers in scope) | same |

Progressive Disclosure: full TDD failing tests + own workstream, digest of broader blueprint (max 500 tokens).

Each impl agent must return a `## Completion Block` with: task, status, files changed, test command + result, test counts (SEP Contrato 4).

## Phase 3 — Reviewer

| Teammate | subagent_type | Receives | Returns |
|---|---|---|---|
| reviewer | claude-tech-squad:{{reviewer_agent}} | full diff + arch digest + test plan digest | findings + verdict |

Output contract — must produce ALL:
1. `## Findings` (in-scope issues, empty if none)
2. `## Pre-existing Findings` (Major | Minor classification)
3. Final verdict: `APPROVED` or `CHANGES REQUESTED: <items>`
4. `result_contract` + `verification_checklist`

## Phase 4 — QA

| Teammate | subagent_type | Receives | Returns |
|---|---|---|---|
| qa | claude-tech-squad:{{qa_agent}} | full AC + full test plan + impl digest + test command | PASS/FAIL diagnosis |

QA runs commands, does not review code.

## Phase 5 — TechLead Conformance Audit (mandatory, never skippable)

| Teammate | subagent_type | Receives | Returns |
|---|---|---|---|
| techlead-audit | claude-tech-squad:techlead | full execution plan + arch + AC + impl + QA | CONFORMANT/NON-CONFORMANT verdict |

Output format must include: Verdict, Workstream Coverage, Architecture Violations, TDD Compliance, Requirements Traceability, Gaps (if NON-CONFORMANT).

## Phase 6 — Quality bench (parallel, mandatory)

| Teammate | subagent_type | Receives | Conditional? |
|---|---|---|---|
| security-rev | claude-tech-squad:security-reviewer | full diff + arch digest | always |
| privacy-rev | claude-tech-squad:privacy-reviewer | same | always |
| perf-eng | claude-tech-squad:performance-engineer | same | always |
| access-rev | claude-tech-squad:accessibility-reviewer | same | always |
| integ-qa | claude-tech-squad:integration-qa | same | always |
| code-quality | claude-tech-squad:code-quality | same + `{{lint_command}}` | always |
| load-test | claude-tech-squad:performance-engineer | endpoints + SLOs | only if HTTP/queues/jobs touched |

Each returns a structured checklist. Findings classified as BLOCKING / WARNING / INFO.

## Phase 7 — CodeRabbit Final Review Gate

Shell-based, not an agent: `bash plugins/claude-tech-squad/bin/coderabbit_gate.sh`.

| Exit code | Action |
|---|---|
| 0 | clean → advance |
| 2 | findings → re-spawn `reviewer-coderabbit` with findings, max 2 cycles |
| 1 | error → operator gate `[R/S/X]` |

## Phase 8 — Docs + Delivery

| Teammate | subagent_type | Receives |
|---|---|---|
| docs-writer | claude-tech-squad:docs-writer | full impl + full AC + digests of arch/QA/conformance/quality bench/test plan |
| jira-confluence | claude-tech-squad:jira-confluence-specialist | impl summary + docs delta |

## Phase 9 — PM UAT (operator gate)

| Teammate | subagent_type | Receives | Returns |
|---|---|---|---|
| pm-uat | claude-tech-squad:pm | full AC + digests of QA/conformance/quality bench | APPROVED / REJECTED + gaps |

Validates evidence per acceptance criterion, not code.

## Routing variables

The following are resolved by the Preflight Gate via `squad-cli preflight` and substituted into prompts:

- `{{backend_agent}}`, `{{frontend_agent}}`, `{{reviewer_agent}}`, `{{qa_agent}}`
- `{{test_command}}`, `{{build_command}}`, `{{lint_command}}`
- `{{lint_profile}}`, `{{architecture_style}}`, `{{feature_slug}}`
