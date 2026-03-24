# Claude Tech Squad — Manual Técnico

**Versão:** 5.2.0
**Plugin:** `claude-tech-squad`

---

## Índice

1. [O que é o plugin](#1-o-que-é-o-plugin)
2. [Instalação e ativação](#2-instalação-e-ativação)
3. [Teammate Mode — panes tmux por agente](#3-teammate-mode--panes-tmux-por-agente)
4. [Skills disponíveis e quando usar cada uma](#4-skills-disponíveis-e-quando-usar-cada-uma)
5. [Fluxo completo de cada skill](#5-fluxo-completo-de-cada-skill)
6. [Os 55 agentes — papéis e especialidades](#6-os-55-agentes--papéis-e-especialidades)
7. [Arquitetura da esteira](#7-arquitetura-da-esteira)
8. [Gates de usuário](#8-gates-de-usuário)
9. [Visibilidade de execução](#9-visibilidade-de-execução)
10. [Regras de uso](#10-regras-de-uso)
11. [Referência rápida](#11-referência-rápida)

---

## 1. O que é o plugin

O `claude-tech-squad` é uma equipe de software completa rodando dentro do Claude Code. Cada skill inicia uma esteira onde agentes especializados trabalham em sequência ou em paralelo — cada um com escopo exato, sem sobreposição.

**Princípios fundamentais:**

- Cada agente tem exatamente uma especialidade.
- A esteira pode rodar em dois modos: inline (subagente) ou teammate (pane tmux por agente).
- TDD é o padrão para qualquer mudança de código.
- Gates de usuário existem apenas nos pontos onde a decisão humana é insubstituível.
- Toda execução emite linhas de visibilidade no terminal.

---

## 2. Instalação e ativação

### Via marketplace (recomendado)

```bash
# Adicionar o marketplace uma vez por máquina
claude plugin marketplace add alexfloripavieira/claude-tech-squad

# Instalar globalmente (qualquer repositório)
claude plugin install -s user claude-tech-squad@alexfloripavieira-plugins

# Ou só para o projeto atual
claude plugin install -s project claude-tech-squad@alexfloripavieira-plugins
```

### Auto-update

Para receber atualizações automaticamente, adicione em `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "alexfloripavieira-plugins": {
      "source": { "source": "github", "repo": "alexfloripavieira/claude-tech-squad" },
      "autoUpdate": true
    }
  }
}
```

---

## 3. Teammate Mode — panes tmux por agente

Por padrão, os agentes rodam como subagentes inline na mesma sessão Claude. Com o teammate mode ativo, cada especialista abre em seu próprio pane tmux — uma instância Claude Code independente por agente.

### Configuração

Adicione em `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "CLAUDE_CODE_TEAMMATE_MODE": "tmux"
  }
}
```

### Como iniciar

```bash
# Criar sessão tmux
tmux new-session -s squad

# Iniciar Claude Code dentro da sessão
claude
```

### O que acontece

Com teammate mode ativo, cada `/discovery`, `/implement` e `/squad`:

1. Cria um time via `TeamCreate`
2. Spawna cada especialista com `Agent(team_name=..., name=..., subagent_type=...)`
3. Cada especialista abre em pane próprio
4. O orchestrador coordena e apresenta os gates

Sem tmux mode, os mesmos workflows funcionam corretamente como subagentes inline — mesmos outputs, mesmos gates, sem panes visuais.

---

## 4. Skills disponíveis e quando usar cada uma

| Skill | Quando usar |
|---|---|
| `/squad` | Feature completa do zero ao deploy. Inclui discovery + build + release. |
| `/discovery` | Planejar antes de implementar. Produz blueprint completo sem escrever código. |
| `/implement` | Implementar a partir de um blueprint existente (saída do `/discovery`). |
| `/bug-fix` | Corrigir um bug específico com stack trace ou repro steps. 1–5 arquivos. |
| `/security-audit` | Auditoria de segurança periódica ou pré-release. Roda bandit, pip-audit, npm audit. |
| `/migration-plan` | Planejar mudança de schema de banco antes de alterar models. |
| `/cloud-debug` | Investigar problema em ambiente de cloud/produção com logs e infra. |
| `/dependency-check` | Verificar dependências desatualizadas, vulnerabilidades, licenças. |
| `/factory-retrospective` | Analisar execuções recentes e melhorar o processo da equipe. |
| `/pre-commit-lint` | Configurar hook de lint automático nos commits. |

**Regra de escalada:**

```
bug 1–5 arquivos     → /bug-fix
feature nova         → /squad
planejar primeiro    → /discovery → /implement
schema vai mudar     → /migration-plan (antes do /squad ou /implement)
auditoria periódica  → /security-audit
```

---

## 5. Fluxo completo de cada skill

### /discovery

**Objetivo:** Produzir um Discovery & Blueprint Document completo sem escrever código.

**Input:** Descrição da feature ou problema.

**Fluxo (com teammate mode: cada nó = pane tmux separado):**

```
/discovery "feature X"
    │
    ├─ Recon do repositório (README, CLAUDE.md, package.json, pyproject.toml)
    ├─ TeamCreate → time "discovery"
    │
    └─ pm
         └─ ba
              └─ po ────────────────────────── [GATE 1: validação de escopo]
                   └─ planner
                        └─ [GATE 2: tradeoffs técnicos aprovados]
                             └─ architect
                                  └─ techlead ─────────────── [GATE 3: direção arquitetural]
                                       └─ PARALLEL BENCH (specialist notes)
                                            ├─ backend-architect
                                            ├─ frontend-architect
                                            ├─ api-designer
                                            ├─ data-architect
                                            ├─ ux-designer
                                            ├─ ai-engineer / agent-architect / rag-engineer (se LLM)
                                            ├─ prompt-engineer (se LLM)
                                            └─ outros por contexto
                                       └─ PARALLEL QUALITY BASELINE
                                            ├─ security-reviewer
                                            ├─ privacy-reviewer
                                            ├─ performance-engineer
                                            └─ outros por contexto
                                       └─ design-principles-specialist
                                            └─ test-planner
                                                 └─ tdd-specialist ── [GATE 4: blueprint final]
```

**Saída:** Discovery & Blueprint Document com 13 seções.

**Gates de usuário:** 4

---

### /implement

**Objetivo:** Implementar a partir de um blueprint existente.

**Input obrigatório:** Discovery & Blueprint Document.

**Fluxo:**

```
/implement
    │
    ├─ Validação: blueprint existe na conversa?
    │   Não → pede ao usuário para rodar /discovery primeiro
    │
    ├─ TeamCreate → time "implement"
    │
    └─ tdd-specialist (failing tests first)
         └─ PARALLEL IMPLEMENTATION
              ├─ backend-dev
              ├─ frontend-dev
              ├─ mobile-dev (se mobile)
              └─ data-engineer (se pipeline)
         └─ reviewer ◄──────────────────────── loop ──┐
              APPROVED → qa                            │
              CHANGES  → impl agent ──────────────────┘
         └─ qa (execução real de testes)
              PASS → quality bench
              FAIL → impl agent
         └─ PARALLEL QUALITY BENCH
              ├─ security-reviewer / security-engineer
              ├─ privacy-reviewer
              ├─ performance-engineer
              ├─ accessibility-reviewer
              ├─ chaos-engineer (se sistema distribuído / LLM)
              └─ integration-qa
         └─ docs-writer
              └─ tech-writer (se docs externas)
                   └─ jira-confluence-specialist
                        └─ pm ─────────────── [GATE 5: UAT]
```

**Gates de usuário:** 1 (UAT final)

---

### /squad

**Objetivo:** Entrega end-to-end completa: discovery + build + release.

**Fluxo:** `/discovery` completo + `/implement` completo + release chain com time persistente:

```
TeamCreate → time "squad" (persiste por todas as fases)

[Discovery Chain — Gates 1-4]
    └─ [Build Chain — Gate 5: UAT]
         └─ release
              └─ sre ──[GO / NO-GO]
```

**Gates de usuário:** 5

---

### /bug-fix

```
/bug-fix
    ├─ [GATE: symptom + expected + repro + context]
    └─ techlead (root cause)
         └─ tdd-specialist (failing test que prova o bug)
              └─ backend-dev ou frontend-dev (fix mínimo)
                   └─ reviewer
                        └─ qa (confirma fix + sem regressão)
```

**Escalada para /squad se:** root cause revela problema arquitetural ou > 5 arquivos.

---

### /security-audit, /migration-plan, /cloud-debug, /dependency-check, /factory-retrospective, /pre-commit-lint

Veja [OPERATIONAL-PLAYBOOK.md](OPERATIONAL-PLAYBOOK.md) para exemplos de uso de cada uma.

---

## 6. Os 59 agentes — papéis e especialidades

### Discovery & Planning

| Agente | Especialidade |
|---|---|
| `pm` | Problem statement, user stories, ACs |
| `business-analyst` | Domain rules, workflows, edge cases |
| `po` | Priorização, scope cuts, release increments |
| `planner` | Stack validation, technical feasibility, tradeoffs |
| `architect` | Design da solução, workstreams, sequenciamento |
| `techlead` | Orquestrador: execution strategy, sequencing, ownership |

### Especialistas de Arquitetura

| Agente | Especialidade |
|---|---|
| `backend-architect` | APIs, services, domain layer, auth, storage |
| `frontend-architect` | UI structure, routing, state, client error handling |
| `api-designer` | REST/GraphQL/RPC contracts, versioning, error models |
| `data-architect` | Schema evolution, migrations, event flows, data contracts |
| `ux-designer` | User flows, interaction states, microcopy, friction |
| `ai-engineer` | Model integrations, prompt contracts, tool use, evals, latency |
| `agent-architect` | Multi-agent orchestration, MCP, tool use design, agent loops |
| `integration-engineer` | Third-party contracts, retries, idempotency, failure handling |
| `devops` | Containers, IaC, secrets, scaling, DR |
| `ci-cd` | Pipelines, quality gates, artifact flow, deploy stages |
| `dba` | Migration safety, locking, indexes, rollback feasibility |
| `platform-dev` | Background workers, job queues, developer tooling |
| `cloud-architect` | VPC topology, IAM strategy, multi-region HA, DR, Well-Architected |

### LLM / AI Specialists

| Agente | Especialidade |
|---|---|
| `prompt-engineer` | Prompt design, chain-of-thought, token optimization, caching, versionamento |
| `rag-engineer` | Chunking, embedding, vector stores, hybrid search, reranking, HyDE, RAPTOR |
| `llm-eval-specialist` | RAGAS, DeepEval, hallucination detection, regression suites, LLM-as-judge |
| `conversational-designer` | Dialog flows, intent mapping, personas, fallback, escalation |
| `ml-engineer` | Fine-tuning (LoRA/QLoRA), training pipelines, MLOps, drift monitoring |

### Implementação

| Agente | Especialidade |
|---|---|
| `backend-dev` | APIs, services, auth, persistence, queues |
| `frontend-dev` | UI, routing, state, accessibility, frontend tests |
| `mobile-dev` | React Native, Flutter, iOS (SwiftUI), Android (Compose) |
| `data-engineer` | ETL/ELT, Kafka, Spark, dbt, Airflow, data quality, CDC |
| `tdd-specialist` | Red-green-refactor cycles, failing test blueprints |

### Search

| Agente | Especialidade |
|---|---|
| `search-engineer` | Elasticsearch/OpenSearch, full-text, faceted, relevance tuning, hybrid |

### Qualidade & Revisão

| Agente | Especialidade |
|---|---|
| `reviewer` | Code review: bugs, correctness, TDD compliance, complexity |
| `qa` | Test execution real, AC validation, regression check |
| `test-planner` | Test matrix: unit/integration/e2e/regression |
| `test-automation-engineer` | Test suites, fixtures, harnesses, quality gates |
| `integration-qa` | Contract validation, cross-service flows, external deps |

### Revisores Especializados

| Agente | Especialidade |
|---|---|
| `security-reviewer` | Auth, authz, injection, secrets, OWASP — revisão de código |
| `security-engineer` | Implementa OAuth2/OIDC/MFA, WAF, SAST/DAST, threat modeling |
| `privacy-reviewer` | PII exposure, data minimization, consent, masking |
| `compliance-reviewer` | Audit trail, LGPD/GDPR/PCI, regulated data |
| `accessibility-reviewer` | WCAG, keyboard nav, ARIA, contrast, focus |
| `performance-engineer` | Latência, throughput, queries, caching, load |
| `chaos-engineer` | Fault injection, circuit breaker validation, resilience de LLM agents |
| `design-principles-specialist` | SOLID, DRY, Clean Arch, coupling/cohesion, testability |
| `code-quality` | Lint config, tech debt, coding standards, SonarQube |

### Observabilidade & Monitoramento

| Agente | Especialidade |
|---|---|
| `observability-engineer` | Logs estruturados, métricas, traces, alerting rules |
| `monitoring-specialist` | Dashboards Grafana/New Relic/Datadog, APM, SLO tracking, LLM cost dashboards |
| `analytics-engineer` | Product events, funnels, A/B tests, product dashboards |

### Design

| Agente | Especialidade |
|---|---|
| `design-system-engineer` | Component libraries, design tokens, Storybook, Figma → código |

### Documentação & Developer Experience

| Agente | Especialidade |
|---|---|
| `docs-writer` | Docs técnicos internos, migration notes, operator guidance |
| `tech-writer` | User guides, API references públicas, tutorials, changelogs para clientes |
| `devex-engineer` | Setup local, CLI tooling, scaffolding, contribuição, onboarding |
| `jira-confluence-specialist` | Jira issues, epics, stories, Confluence pages (via MCP Atlassian) |
| `developer-relations` | Comunidade dev externa, SDKs, tutoriais, conteúdo técnico, feedback de devs |

### Business & Growth

| Agente | Especialidade |
|---|---|
| `solutions-architect` | Integrações enterprise, pré-venda técnica, RFPs, PoCs para clientes |
| `growth-engineer` | A/B testing, feature flags, funnels, growth loops, experimentação |

### Operações & Release

| Agente | Especialidade |
|---|---|
| `release` | Release plan, change inventory, rollback, comunicação |
| `sre` | SLOs, blast radius, rollback readiness, canary strategy |
| `cost-optimizer` | Cloud spend, API costs, query costs, rightsizing |
| `incident-manager` | Coordenação de incidentes de produção |

---

## 7. Arquitetura da esteira

### Diagrama completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DISCOVERY CHAIN                                                         │
│                                                                         │
│  skill → pm → ba → po ──[GATE 1]── planner ──[GATE 2]── architect      │
│                                                              │           │
│                              ┌───────────────────────────────┘           │
│                              ▼                                           │
│                          techlead ──[GATE 3]                             │
│                              │                                           │
│          ┌───────────────────┼──────────────────────┐                   │
│          ▼                   ▼                       ▼                   │
│   backend-arch         frontend-arch            api-designer             │
│   data-arch → dba      ux-designer              integ-engineer           │
│   ai-engineer          agent-architect           rag-engineer            │
│   prompt-engineer      search-engineer           cloud-architect         │
│          └───────────────────┼──────────────────────┘                   │
│                              ▼                                           │
│                    QUALITY BASELINE BENCH                                │
│                    security-rev, privacy-rev, performance, observ        │
│                              ▼                                           │
│              design-principles → test-planner → tdd-specialist          │
│                                                        │                 │
│                                               [GATE 4: blueprint]       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  BUILD CHAIN                                                             │
│                                                                         │
│  tdd-specialist (failing tests)                                         │
│          │                                                              │
│          ├─── backend-dev                                               │
│          ├─── frontend-dev       (paralelo)                             │
│          ├─── mobile-dev                                                │
│          └─── data-engineer                                             │
│                    │                                                    │
│                 reviewer ◄──────────────────────── loop ───┐           │
│              APPROVED │    CHANGES REQUESTED               │           │
│                    ▼                                        │           │
│                   qa ──── FAIL ────────────────────────────┘           │
│                 PASS │                                                  │
│                    ▼                                                    │
│              QUALITY BENCH (paralelo)                                   │
│              security-rev, security-eng, privacy-rev                    │
│              perf-eng, access-rev, chaos-eng, integ-qa                  │
│                    │                                                    │
│              docs-writer → tech-writer → jira-confluence                │
│                    │                                                    │
│                   pm ─────────────────────────── [GATE 5: UAT]         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  RELEASE CHAIN (apenas /squad)                                           │
│                                                                         │
│  release → sre ──[GO]── fim                                             │
│                └─[NO-GO]── resolve blockers                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Gates de usuário

| Gate | Quem apresenta | O que decidir |
|---|---|---|
| **Gate 1** — Scope Validation | `po` | O escopo definido está correto? Cortes necessários? |
| **Gate 2** — Technical Tradeoffs | `planner` | Qual abordagem técnica seguir? |
| **Gate 3** — Architecture Direction | `techlead` | A arquitetura proposta faz sentido? |
| **Gate 4** — Blueprint Confirmation | `tdd-specialist` | O blueprint está aprovado para implementação? |
| **Gate 5** — UAT | `pm` | A feature entregue atende aos critérios de aceitação? |

Nenhum gate pode ser pulado. Responder ao gate é o que move a esteira para a próxima fase.

---

## 9. Visibilidade de execução

### Modo inline (padrão)

```
[Phase Start] discovery
[Agent Start] PM | claude-tech-squad:pm | Problem framing and user stories
[Agent Done] PM | Status: completed | Output: 3 user stories, 8 ACs defined
[Agent Blocked] PO | Waiting on: user scope validation (Gate 1)
[Agent Batch Start] specialist-bench | Agents: backend-architect, frontend-architect, rag-engineer
[Agent Done] Backend Architect | Status: completed | Output: hexagonal layers defined
[Agent Batch Done] specialist-bench | Outcome: specialist notes ready
```

### Modo teammate (tmux)

```
[Team Created] discovery
[Teammate Spawned] pm | pane: pm
[Teammate Spawned] ba | pane: ba
[Gate] Scope Validation | Waiting for user input
[Batch Spawned] specialist-bench | Teammates: backend-arch, frontend-arch, rag-engineer, prompt-engineer
[Teammate Done] reviewer | Status: APPROVED
[Teammate Done] qa | Status: PASS
```

---

## 10. Regras de uso

### Qual skill usar

```
Tenho um bug com stack trace           → /bug-fix
Quero planejar antes de implementar    → /discovery
Tenho um blueprint, quero implementar  → /implement
Quero tudo de uma vez                  → /squad
Vou mudar models do banco              → /migration-plan ANTES do /squad ou /implement
Preciso de auditoria de segurança      → /security-audit
Problema em produção                   → /cloud-debug
Deps desatualizadas                    → /dependency-check
Melhorar o processo da squad           → /factory-retrospective
```

### TDD

- `/squad` e `/implement`: TDD obrigatório por padrão
- `/bug-fix`: TDD obrigatório (failing test antes do fix)
- Exceção declarada explicitamente quando o repositório não tem stack de testes viável

### Autonomia

Os agentes trabalham autonomamente entre os gates. Não é necessário interagir entre um gate e outro — a esteira se move sozinha.

---

## 11. Referência rápida

### Skills por contexto

```bash
# Feature nova completa
/claude-tech-squad:squad "implementar autenticação com OAuth Google"

# Produto LLM: agente de viagens com RAG
/claude-tech-squad:squad "construir chatbot de viagens com RAG, busca vetorial e tool use"

# Só planejar, implementar depois
/claude-tech-squad:discovery "refatorar sistema de pagamentos para suportar PIX"

# Implementar com blueprint pronto
/claude-tech-squad:implement

# Bug específico
/claude-tech-squad:bug-fix

# Antes de qualquer mudança de modelo
/claude-tech-squad:migration-plan

# Auditoria de segurança
/claude-tech-squad:security-audit

# Problema em produção
/claude-tech-squad:cloud-debug

# Checar dependências
/claude-tech-squad:dependency-check

# Retrospectiva do processo
/claude-tech-squad:factory-retrospective
```

### Fluxos alternativos por contexto

```
AI feature:        backend-architect → ai-engineer → agent-architect → techlead
RAG feature:       rag-engineer → llm-eval-specialist → prompt-engineer → techlead
Chatbot:           conversational-designer → prompt-engineer → rag-engineer → techlead
Schema change:     data-architect → dba → techlead
External APIs:     api-designer → integration-engineer → techlead
UI feature:        frontend-architect → ux-designer → design-system-engineer → techlead
Search feature:    search-engineer → rag-engineer (se híbrido) → techlead
Mobile feature:    frontend-architect → mobile-dev → techlead
Cloud infra:       cloud-architect → devops → sre → techlead
Tech debt:         reviewer → code-quality → reviewer
Incidente:         incident-manager → {sre + devops + observability-engineer}
Enterprise client: solutions-architect → integration-engineer → techlead
Growth / A/B:      growth-engineer → analytics-engineer → techlead
Dev community:     developer-relations → tech-writer → techlead
```
