# Changelog

## [3.0.0] - 2026-03-24

### Changed (agent delegation model -- explicit invocations)
- `incident-manager`: all specialist agent invocations now use explicit `Agent tool with subagent_type:` pattern. Agents are invoked in parallel with structured prompts for each specialist.
- `cost-optimizer`: DBA invocation now uses explicit `Agent tool with subagent_type: "claude-tech-squad:dba"` with cost-focused prompt.
- `devops`, `sre`, `observability-engineer`, `analytics-engineer`, `platform-dev`: out-of-scope delegation now uses explicit user-facing language ("tell the user: this requires agent X") instead of ambiguous "call X" text.

### Design principle enforced
Each agent either (a) invokes another agent explicitly via Agent tool when it is an orchestrator, or (b) tells the user explicitly which agent to invoke when the request is outside its scope. No agent silently absorbs work that belongs to another.

## [2.9.0] - 2026-03-24

### Changed (scope deduplication — each agent owns exactly one specialty)
- `platform-dev`: narrowed to background workers, job queues, developer tooling, integration glue, and observability hooks in code. CI/CD and infra config explicitly delegated to `ci-cd` and `devops`.
- `devops`: removed "blast radius" ownership — now explicitly delegated to `sre`. Devops owns infrastructure design and config; SRE owns runtime reliability assessment.
- `sre`: clarified boundaries — owns blast radius, SLO, rollback readiness, and canary strategy. Infrastructure config delegated to `devops`. Incident coordination delegated to `incident-manager`.
- `qa`: removed Lint Gate and TDD Compliance Gate (belong to `reviewer`). QA now owns exclusively behavioral validation: test execution, AC verification, regression detection.
- `observability-engineer`: scoped to ops/infrastructure observability only (logs, system metrics, traces, on-call alerts, Grafana/Prometheus dashboards). Product/business metrics explicitly delegated to `analytics-engineer`.
- `analytics-engineer`: scoped to product analytics only (user behavior events, funnels, A/B tests, product dashboards). Infrastructure metrics explicitly delegated to `observability-engineer`.
- `cost-optimizer`: removed DB query performance analysis. Now calls `dba` for query-level cost concerns, focusing exclusively on cloud spend, API costs, storage lifecycle, and infrastructure rightsizing.

## [2.8.0] - 2026-03-24

### Added
- Agent `incident-manager`: orchestrates production incident response — triage, severity classification, specialist coordination, stakeholder communication, mitigation-first strategy, and post-mortem generation.
- Agent `cost-optimizer`: cloud and application cost specialist — infrastructure rightsizing, API cost reduction, DB query cost analysis, storage lifecycle, and cost attribution.

### Changed
- Agent `devops`: upgraded from shallow consultant (4 responsibilities) to full specialist. Now covers: container strategy (Docker/Compose/K8s), IaC, secrets management, scaling and capacity planning, disaster recovery, and rollback planning. Added Bash/Read/Glob/Grep tools for real config inspection.

## [2.7.0] - 2026-03-24

### Added
- Skill `bug-fix`: focused defect resolution workflow (root cause → failing test → fix → real test execution → review). Escalates to `/squad` if architectural issues detected.
- Agent `code-quality`: strategic code quality specialist owning lint configuration, coding standards, tech debt analysis, and quality metrics. Complements `reviewer` (tactical) with strategic quality ownership.

### Changed
- Agent `qa` and `reviewer` now execute real lint/test tools via Bash (backpressure real) — introduced in v2.6.0 and now complemented by dedicated quality ownership in `code-quality`

## 2.6.0 (2026-03-24)

- Added: Skill `security-audit` — auditoria atomica com execucao real de bandit/pip-audit/npm audit
- Added: Skill `migration-plan` — planejamento de migrations com data-architect + dba
- Added: Skill `cloud-debug` — debug de producao com observability-engineer + sre + techlead
- Added: Skill `dependency-check` — verificacao real de dependencias desatualizadas/vulneraveis
- Added: Skill `factory-retrospective` — auto-melhoria da factory via analise de execution logs
- Changed: QA agente agora executa ferramentas reais (pytest, ruff, mypy) antes da revisao textual
- Changed: Security Reviewer agora executa bandit, pip-audit, safety antes da analise de ameacas
- Changed: Jira/Confluence Specialist agora cria issues e paginas reais via API Atlassian MCP
- Fixed: marketplace.json e CHANGELOG sincronizados com plugin.json (versao 2.5.0 estava nao documentada)

## 2.5.0 (2026-03-XX)

- Added: Hexagonal Architecture como padrao em todos os agentes de arquitetura e implementacao
- Added: Skill `pre-commit-lint` para auto-fix de lint antes de commits (ruff, black, isort, eslint, prettier)
- Added: Lint Compliance Gate no QA (falha rapida se lint nao passa) e no Reviewer (lint + TDD compliance)
- Added: TDD Compliance Gate no Reviewer (verifica testes para cada nova funcao/classe)
- Changed: TDD-first e agora mandatorio em todos os agentes (nao apenas no /squad)
- Changed: PO agora tem Post-Implementation Audit obrigatorio antes do sign-off
- Changed: PM agora tem UAT obrigatorio mapeando cada AC a evidencia concreta
- Changed: Backend-dev ganhou tabela de imports permitidos/proibidos por camada Hexagonal

## 2.4.0

- made `/claude-tech-squad:squad` TDD-first by default for code changes
- required the Test Plan and TDD Delivery Plan to be ready before build starts in squad flows
- made TDD exceptions explicit in squad and implementation reporting
- updated docs to explain the new default behavior

## 2.3.0

- added `tdd-specialist` to drive development from failing tests and red-green-refactor cycles
- added `design-principles-specialist` for SOLID, Clean Architecture, Ports and Adapters, Hexagonal-style boundaries, and testability guardrails
- updated discovery, implement, and squad workflows to include structural guardrails and TDD delivery planning before implementation
- updated public documentation and playbooks to explain the new testing and design-role split

## 2.2.0

- added visible orchestration lines for phase changes, agent handoffs, retries, and parallel batches
- added mandatory `Agent Execution Log` output to discovery, implement, and squad workflows
- documented how visible agent execution appears in Claude output

## 2.1.0

- clarified product positioning versus `claude-config`
- added validation workflow and release documentation
- added license and public-distribution structure

## 2.0.0

- expanded the plugin into a full specialist technology squad
