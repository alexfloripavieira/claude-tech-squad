# Changelog

## [5.4.0] - 2026-03-24 — Squad Execution Protocol (SEP): Observability, Continuity, and Remediation Contracts

### Added

**Squad Execution Protocol (SEP)** — four stack-agnostic contracts that close the observability and continuity gaps identified in the factory retrospective. All changes are additive new steps in existing skills; no existing behavior removed.

**Contrato 1 — Execution Log** (`discovery`, `implement`, `security-audit`, `dependency-check`):
Every skill now writes a structured YAML-frontmatter log entry to `ai-docs/.squad-log/` on completion. Logs include: `skill`, `timestamp`, `status`, `retry_count`, `gates_blocked`, `uat_result`, `implement_triggered`, `output_artifact`. The `factory-retrospective` reads these logs as its primary data source instead of inferring patterns from git history.

**Contrato 2 — Remediation Tasks** (`security-audit`, `dependency-check`):
Both audit skills now generate a companion `ai-docs/security-remediation-YYYY-MM-DD.md` and `ai-docs/dependency-remediation-YYYY-MM-DD.md` file with checkbox task lists organized by severity. The `factory-retrospective` counts `- [ ]` vs `- [x]` items across runs to compute remediation closure rate.

**Contrato 3 — Discovery → Implement Bridge Gate** (`discovery`):
After the blueprint confirmation gate, `/discovery` now presents an explicit "Quer iniciar a implementação agora? [S/N]" prompt. If yes, `/implement` is invoked immediately with the blueprint path. If no, the execution log records `implement_triggered: false`, which the `factory-retrospective` surfaces as an orphaned discovery.

**Contrato 4 — Task Status Protocol** (`implement`):
Each implementation agent now returns a mandatory `Completion Block` (task name, status, files changed, test command result) before the orchestrator advances to the Reviewer phase. Blocks are aggregated in the execution log.

**Stack Command Detection** (`implement` — Step 0):
Before any teammate is spawned, `/implement` detects the project's real commands from `Makefile`, `package.json`, `pyproject.toml`, `pom.xml`, or `build.gradle`. Detected commands — or overrides from `CLAUDE.md` — are injected into every implementation agent prompt. Agents never infer test/migrate/lint commands; they receive them explicitly.

**`factory-retrospective` SEP-aware Step 1**:
Step 1 now reads `ai-docs/.squad-log/` as the primary source. Computes: average `retry_count` per skill, orphaned discovery rate, open remediation items, `uat_result: REJECTED` rate. Falls back to git/markdown inference when no SEP logs exist (backward compatible with pre-5.4.0 runs).

### Fixed

- `factory-retrospective`: was blind to teammate-mode runs (no persistent artifacts). Now reads `.squad-log/` which is written by all skills regardless of teammate vs inline mode.

## [5.3.0] - 2026-03-24 — Sequencing Model Consistency: 40 Agent Handoff Protocol Rewrites

### Changed

**Handoff Protocol rewrite across 40 of 59 agents.** Every agent that previously used `Agent tool` in its Handoff Protocol to chain directly to the next agent (Model B) has been rewritten to return structured output to the orchestrator (Model A). This eliminates double-execution risk, context loss, and safety contract bypass paths.

**Subtypes fixed:**
- **B1 — Forward-chain agents (26):** Handoff Protocol invoked `Agent tool` with `subagent_type` to spawn the next agent directly. Rewritten to return output to the orchestrator.
- **B2 — Return-via-Agent-tool agents (12):** Used `Agent tool` in the Handoff Protocol to return results. Rewritten to plain structured output.
- **B3 — Implicit chain agents (2):** `mobile-dev` and `data-engineer` had implicit chaining patterns. Rewritten to return to orchestrator.
- **techlead:** Full strip of orchestration logic — now a pure specialist. No longer spawns or sequences other agents.

**Exemptions:**
- `incident-manager`: Retains `Agent tool` usage — legitimate fan-out pattern for coordinating multiple specialists during active incidents.

**Additional fixes:**
- `cost-optimizer`: Mid-body DBA delegation via `Agent tool` converted to recommendation text. Cost-optimizer now recommends DBA involvement instead of spawning it.
- `scripts/validate.sh`: New self-chaining detection rule — fails if any agent file (except `incident-manager`) contains `subagent_type:` references.

### Fixed

- `docs/GETTING-STARTED.md`: Agent count corrected from 55 to 59. Roster table updated with 3 missing agents: `solutions-architect`, `growth-engineer` (Business & Growth), and `developer-relations` (Docs / DX).
- `CHANGELOG.md`: v5.2.0 entry arithmetic corrected from "58 required agents" to "59 required agents".

## [5.2.2] - 2026-03-24 — Safety Guardrails: Absolute Prohibitions — second pass (7 more agents)

### Changed

**Absolute Prohibitions blocks** added to 7 more agents after a full audit of every agent in the roster:

- `chaos-engineer`: NEVER run experiments in production without confirmed maintenance window, on-call present, and documented abort procedure. NEVER inject faults that cause data loss. Staging is the default — production requires explicit confirmation per experiment.
- `security-engineer`: NEVER revoke production tokens without replacement ready. NEVER disable auth or CORS protections. NEVER add WAF rules to production without staging validation. NEVER log or hardcode secrets.
- `cost-optimizer`: NEVER delete storage buckets, cloud databases, or production instances. NEVER disable monitoring to save cost. All deletions require DevOps/SRE verification before execution.
- `ml-engineer`: NEVER promote models to production without rollback procedure. NEVER delete model versions serving production traffic. NEVER overwrite training datasets without a versioned backup. Model deployment follows the same standards as a code release.
- `mobile-dev`: NEVER submit directly to App Store or Play Store production track. NEVER roll out to 100% of users without staged rollout. NEVER hardcode secrets. NEVER disable certificate pinning as a workaround. App store submissions are irreversible for users.
- `frontend-dev`: NEVER commit to main/develop directly. NEVER merge without approved review. NEVER hardcode credentials. NEVER disable CSP or XSS protections as a workaround.
- `techlead`: As execution authority, NEVER authorize any specialist to take a prohibited action without explicit written user confirmation. Surfaces all such decisions to the user with a clear risk summary before proceeding.

**Full audit verdict:** 13 agents now have Absolute Prohibitions (dba, devops, ci-cd, release, incident-manager, data-engineer, backend-dev, platform-dev, sre, chaos-engineer, security-engineer, cost-optimizer, ml-engineer, mobile-dev, frontend-dev, techlead = 16 total). The 3 skill orchestrators (discovery, implement, squad) carry the Global Safety Contract. All remaining agents are pure review/design/analysis with no execution authority.

## [5.2.1] - 2026-03-24 — Safety Guardrails: Absolute Prohibitions across all dangerous agents

### Added

**Absolute Prohibitions blocks** added to every agent and orchestrator that can take destructive actions. Each block explicitly lists forbidden operations and requires written user confirmation before proceeding — regardless of incident urgency or business pressure.

**Agents hardened:**
- `dba`: DROP DATABASE, DROP TABLE, TRUNCATE, backup deletion, destructive migrations without rollback
- `devops`: tsuru app-remove, cloud resource deletion (EC2, RDS, S3, clusters), rm -rf, terraform destroy, stopping prod services
- `ci-cd`: merge without approved PR, force push to protected branches, disable quality gates, skip hooks with --no-verify
- `release`: deploy without tested rollback plan, skip staging validation, merge without PR approval
- `incident-manager`: all of the above, plus queue deletion and token revocation — explicitly states that incident urgency does not override these rules
- `data-engineer`: DROP TABLE/DATABASE, S3/GCS bucket deletion, Kafka/Kinesis topic deletion, dbt --full-refresh on prod, disabling CDC streams
- `backend-dev`: destructive migrations without rollback script, committing directly to main/develop, removing auth as a workaround, hardcoding secrets
- `platform-dev`: purging message queues with unprocessed messages, terminating workers with active tasks, removing feature flags, deleting cron schedules
- `sre`: approving deployment without rollback plan, disabling SLO alerting, approving unsafe migrations, silencing monitoring — explicitly states business pressure does not override these rules

**Global Safety Contract** added to the 3 main skill orchestrators:
- `skills/discovery/SKILL.md`
- `skills/implement/SKILL.md`
- `skills/squad/SKILL.md`

The contract propagates to every teammate spawned by these workflows. It covers the same forbidden operations plus an explicit note: **no deadline, incident, or business pressure overrides this contract.**

## [5.2.0] - 2026-03-24 — 3 Business Agents + Hardened Validation (59 total)

### Added
- `solutions-architect`: Customer-facing technical architect for enterprise integrations, pre-sales, RFPs, and PoCs. Distinct from internal architect.
- `growth-engineer`: Experimentation infrastructure, A/B testing, feature flags, funnel instrumentation, and growth loop implementation. Distinct from analytics-engineer.
- `developer-relations`: External developer community, SDK publishing, tutorials, technical content, and developer feedback loops. Distinct from tech-writer and devex-engineer.

### Changed
- `scripts/validate.sh`: Hardened from 6 checks to full validation — now validates version consistency between `marketplace.json` and `plugin.json`, all 10 required skills, all 59 required agents (by name), frontmatter (`name:` + `description:`) on every agent and skill file, and required documentation files. Outputs agent count on success.

## [5.1.2] - 2026-03-24 — Documentation complete for v5.1

### Changed
- `docs/MANUAL.md`: updated from v4.1.0 to v5.1.1 — 55 agents, teammate mode setup, updated architecture diagrams, LLM/AI alternative flows in quick reference
- `docs/EXECUTION-TRACE.md`: added teammate mode trace examples with `[Team Created]`, `[Teammate Spawned]`, `[Gate]`, `[Batch Spawned]`, `[Teammate Done]` terminology; added tmux troubleshooting section
- `docs/OPERATIONAL-PLAYBOOK.md`: expanded from 7 to 15 scenarios — added RAG chatbot, multi-agent MCP, monitoring/observability dashboards, hybrid search, and mobile feature scenarios

## [5.1.1] - 2026-03-24 — Auto-update distribution pipeline

### Fixed
- `marketplace.json` estava travado em `4.2.0` desde a release inicial, tornando todas as versões subsequentes (`4.2.1`, `5.0.0`, `5.1.0`) invisíveis para usuários com `autoUpdate: true`. Corrigido para `5.1.0`.

### Added
- `.github/workflows/release.yml`: workflow do GitHub Actions disparado em tags `v*.*.*`. Valida o plugin, verifica consistência de versões entre `marketplace.json`, `plugin.json` e a tag, e cria um GitHub Release com as notas extraídas do `CHANGELOG.md`.
- `scripts/release.sh`: script de release em um comando. Faz bump de `marketplace.json` e `plugin.json`, valida, checa entrada no `CHANGELOG.md`, commita, cria a tag e faz push. Uso: `./scripts/release.sh 5.2.0`.
- `docs/RELEASING.md`: atualizado com o processo automatizado completo e explicação de como o `autoUpdate` funciona para os usuários.

## [5.1.0] - 2026-03-24 — 16 New Specialist Agents (55 total)

Expanded the squad from 39 to 55 agents covering LLM/AI stacks, monitoring, cloud, security, mobile, data, search, and developer experience.

### Added

**LLM / AI Specialists**
- `prompt-engineer`: Prompt design, chain-of-thought, token optimization, prompt caching, versioning, regression testing
- `rag-engineer`: Full RAG stack — chunking, embedding, vector stores, hybrid search, reranking, HyDE, RAPTOR, agentic RAG
- `agent-architect`: Multi-agent orchestration, MCP (Model Context Protocol), tool use contracts, ReAct/Plan-Execute/MRKL loops, Claude Agent SDK, LangChain/LlamaIndex/AutoGen/CrewAI
- `llm-eval-specialist`: RAGAS, DeepEval, TruLens, hallucination detection, regression suites, LLM-as-judge, production quality monitoring
- `conversational-designer`: Dialog flows, intent architecture, persona, fallback strategies, conversation memory, escalation paths
- `ml-engineer`: Fine-tuning (LoRA/QLoRA), training pipelines, MLOps, model registry, serving, drift monitoring

**Infrastructure & Operations**
- `monitoring-specialist`: Grafana, New Relic, Datadog dashboards; APM; SLO/error budget tracking; alert tuning; LLM cost and quality dashboards
- `cloud-architect`: VPC/networking topology, IAM strategy, multi-region HA, DR planning, Well-Architected review across AWS/GCP/Azure
- `security-engineer`: Implements OAuth2/OIDC/MFA, WAF rules, SAST/DAST pipeline integration, threat modeling, secrets management
- `chaos-engineer`: Fault injection, circuit breaker validation, degraded-mode testing, LLM dependency resilience, game days

**Mobile & Data**
- `mobile-dev`: React Native, Flutter, iOS (SwiftUI), Android (Compose) — offline, push, deep links, app store deployment
- `data-engineer`: ETL/ELT pipelines, Kafka, Spark, dbt, Airflow, data quality (Great Expectations), CDC, lakehouse

**Search**
- `search-engineer`: Elasticsearch/OpenSearch full-text, faceted search, relevance tuning, autocomplete, hybrid keyword+vector

**Documentation & Developer Experience**
- `tech-writer`: User guides, public API references, tutorials, customer changelogs, onboarding docs (distinct from docs-writer)
- `devex-engineer`: Local dev setup, CLI tooling, scaffolding, Makefile targets, contribution workflows, onboarding experience
- `design-system-engineer`: Component libraries, design tokens, Storybook, theming, Figma/Pencil → code contract, accessibility at component layer

## [5.0.0] - 2026-03-24 — BREAKING: TeamCreate-Based Teammate Architecture

Skills `discovery`, `implement`, and `squad` now spawn each specialist as a real Claude Code teammate via `TeamCreate` + `Agent(team_name=...)`, giving every specialist its own tmux pane. This replaces the previous inline `Agent` tool chain where all agents ran in the same process without visual separation.

### Changed
- `skills/discovery/SKILL.md`: rewritten to use `TeamCreate` + teammate spawning. Each specialist (PM, BA, PO, Planner, Architect, TechLead, specialist batch, quality batch, Design Principles, Test Planner, TDD Specialist) gets its own tmux pane. Gates remain at PO, Planner, TechLead, and TDD Specialist.
- `skills/implement/SKILL.md`: rewritten to use `TeamCreate` + teammate spawning. TDD Specialist, implementation batch, Reviewer, QA, quality bench, Docs Writer, Jira/Confluence, and PM UAT each run in their own pane. Retry loops preserved.
- `skills/squad/SKILL.md`: rewritten as the full end-to-end pipeline using a single persistent team across Discovery, Implementation, and Release phases. All 20+ specialists spawn in individual panes.

### Migration
- Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in env
- Requires `CLAUDE_CODE_TEAMMATE_MODE=tmux` in `~/.claude/settings.json` for pane visibility
- Without these env vars, teammates fall back to in-process execution

## [4.2.1] - 2026-03-24

### Fixed
- `plugin.json`: removed `skills` and `agents` arrays that caused manifest validation error ("Invalid input") in Claude Code. Skills and agents are now auto-discovered from directory structure, matching the format used in prior versions.

## [4.2.0] - 2026-03-24

### Added
- `docs/MANUAL.md`: complete technical manual covering all 10 skills, all 40 agents, full pipeline diagrams, user gates reference, and quick-reference guide

## [4.1.0] - 2026-03-24

### Added
- Handoff Protocol to all 25 remaining specialist agents — no agent is a dead end
- Architecture sub-chains: backend-architect → ai-engineer or data-architect → dba; frontend-architect → ux-designer; api-designer → integration-engineer
- Ops chain: platform-dev → devops → ci-cd → sre → release → techlead
- Quality bench reporters (all report to techlead): security-reviewer, privacy-reviewer, compliance-reviewer, accessibility-reviewer, performance-engineer, observability-engineer, analytics-engineer, integration-qa
- incident-manager orchestrates parallel sre + devops + observability-engineer; calls techlead for post-incident code fixes
- cost-optimizer calls dba for query costs; reports to sre or techlead
- code-quality reports back to reviewer
- test-automation-engineer reports to tdd-specialist or qa depending on caller

## [4.0.0] - 2026-03-24 — BREAKING: Chain-Driven Team Architecture

The squad now operates as an autonomous agent chain. Skills are entry points; agents call each other forward using the Agent tool.

Discovery chain: pm → business-analyst → po [gate] → planner [gate] → architect → techlead [gate] → specialist bench → design-principles-specialist → test-planner → tdd-specialist [gate]

Build chain: techlead → tdd-specialist → impl batch → reviewer → qa → techlead (quality) → quality bench → docs-writer → jira-confluence-specialist → pm [UAT gate]

Release chain (/squad only): release → sre

### Changed
- All key agents have Handoff Protocol sections
- Skills simplified to chain starters only
- techlead is the technical orchestrator for both blueprint and build phases
- impl agents call reviewer when done; reviewer calls qa or back to impl; qa calls techlead or back to impl

## [3.0.0] - 2026-03-24

### Changed
- All orchestrator agents use explicit Agent tool invocations
- Agents outside their scope use user-facing language to redirect, not silent absorption

## [2.9.0] - 2026-03-24

### Changed (scope deduplication)
- platform-dev: narrowed to workers, queues, tooling, integration glue
- devops: blast radius removed (→ sre); owns infrastructure config
- sre: owns blast radius, SLO, rollback, canary; delegates infra to devops, incidents to incident-manager
- qa: lint and TDD gates removed (→ reviewer); owns behavioral validation only
- observability-engineer: ops observability only; product metrics → analytics-engineer
- analytics-engineer: product analytics only; infra metrics → observability-engineer
- cost-optimizer: DB query analysis removed (→ dba); owns cloud/API/storage costs

## [2.8.0] - 2026-03-24

### Added
- Agent incident-manager: production incident orchestration — triage, severity, coordination, mitigation, post-mortem
- Agent cost-optimizer: cloud and application cost specialist

### Changed
- devops upgraded to full specialist with real tool access

## [2.7.0] - 2026-03-24

### Added
- Skill bug-fix: root cause → failing test → fix → real validation → review
- Agent code-quality: strategic quality ownership — lint config, tech debt, standards, metrics

## [2.6.0] - 2026-03-24

### Added
- Skill security-audit: real bandit / pip-audit / npm audit execution
- Skill migration-plan: data-architect + dba coordination
- Skill cloud-debug: observability-engineer + sre + techlead
- Skill dependency-check: real outdated/vulnerable dependency scanning
- Skill factory-retrospective: self-improvement via execution log analysis
- jira-confluence-specialist: real Atlassian API calls via MCP (17 tools)

### Changed
- qa and security-reviewer now execute real tools for backpressure

## [2.5.0] - 2026-03-24

### Added
- Hexagonal Architecture as default in all architecture and implementation agents
- Skill pre-commit-lint: auto-fix lint before commits
- Lint Compliance Gate in qa and reviewer
- TDD Compliance Gate in reviewer

### Changed
- TDD-first mandatory in all agents
- po: Post-Implementation Audit required before sign-off
- pm: UAT maps each AC to concrete evidence

## [2.4.0]

- /squad TDD-first by default for code changes
- Test Plan and TDD Delivery Plan required before build starts

## [2.3.0]

- Added tdd-specialist: drives development from failing tests
- Added design-principles-specialist: SOLID, Clean Architecture, Hexagonal guardrails

## [2.2.0]

- Added visible orchestration lines (phase changes, handoffs, retries, parallel batches)
- Mandatory Agent Execution Log in all workflow outputs

## [2.1.0]

- Clarified product positioning vs claude-config
- Added validation workflow, release documentation, license

## [2.0.0]

- Expanded plugin into a full specialist technology squad
