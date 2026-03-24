# Changelog

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
