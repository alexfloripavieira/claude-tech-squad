# Claude Tech Squad — Manual Técnico

**Versão:** 4.1.0
**Plugin:** `claude-tech-squad`

---

## Índice

1. [O que é o plugin](#1-o-que-é-o-plugin)
2. [Instalação e ativação](#2-instalação-e-ativação)
3. [Skills disponíveis e quando usar cada uma](#3-skills-disponíveis-e-quando-usar-cada-uma)
4. [Fluxo completo de cada skill](#4-fluxo-completo-de-cada-skill)
   - [/discovery](#discovery)
   - [/implement](#implement)
   - [/squad](#squad)
   - [/bug-fix](#bug-fix)
   - [/security-audit](#security-audit)
   - [/migration-plan](#migration-plan)
   - [/cloud-debug](#cloud-debug)
   - [/dependency-check](#dependency-check)
   - [/factory-retrospective](#factory-retrospective)
   - [/pre-commit-lint](#pre-commit-lint)
5. [Os 40 agentes — papéis e especialidades](#5-os-40-agentes--papéis-e-especialidades)
6. [Arquitetura da esteira](#6-arquitetura-da-esteira)
7. [Gates de usuário](#7-gates-de-usuário)
8. [Visibilidade de execução](#8-visibilidade-de-execução)
9. [Regras de uso](#9-regras-de-uso)
10. [Referência rápida](#10-referência-rápida)

---

## 1. O que é o plugin

O `claude-tech-squad` é uma equipe de software completa rodando dentro do Claude Code. Cada skill inicia uma esteira onde agentes especializados se chamam em cadeia — nenhum agente é um ponto cego, todos sabem a quem passar o resultado.

**Princípios fundamentais:**

- Cada agente tem exatamente uma especialidade. Sem sobreposição de escopo.
- Cada agente tem um Handoff Protocol: ao terminar, chama o próximo agente via `Agent tool`.
- Skills são iniciadores de cadeia, não gerenciadores de passo a passo.
- TDD é o padrão para qualquer mudança de código.
- Gates de usuário existem apenas nos pontos onde a decisão humana é irreplaceable.
- Toda execução emite linhas de visibilidade no terminal.

---

## 2. Instalação e ativação

```bash
# Clonar o repositório
git clone https://github.com/alexfloripavieira/claude-tech-squad.git ~/claude-tech-squad

# O plugin é ativado automaticamente pelo Claude Code via plugin.json
# Verificar se está ativo:
# No Claude Code: /list-plugins
```

O plugin registra automaticamente todas as skills e agentes. Nenhuma configuração adicional necessária.

---

## 3. Skills disponíveis e quando usar cada uma

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

## 4. Fluxo completo de cada skill

### /discovery

**Objetivo:** Produzir um Discovery & Blueprint Document completo sem escrever código.

**Input:** Descrição da feature ou problema.

**Fluxo:**

```
/discovery "feature X"
    │
    ├─ Recon do repositório (README, CLAUDE.md, package.json, pyproject.toml)
    │
    └─ PM (problem statement + user stories + ACs)
         └─ Business Analyst (domain rules + workflows + edge cases)
              └─ PO ─────────────────────────── [GATE 1: validação de escopo]
                   └─ Planner (technical tradeoffs + stack validation)
                        └─ [GATE 2: tradeoffs técnicos aprovados]
                             └─ Architect (hexagonal design + file plan)
                                  └─ TechLead ────────────────── [GATE 3: direção arquitetural]
                                       └─ PARALLEL BENCH (specialist notes)
                                            ├─ Backend Architect → (AI Engineer | Data Architect → DBA)
                                            ├─ Frontend Architect → UX Designer
                                            ├─ API Designer → Integration Engineer
                                            └─ outros por contexto
                                       └─ Design Principles Specialist (SOLID, Clean Arch guardrails)
                                            └─ Test Planner (test matrix: unit/integration/e2e)
                                                 └─ TDD Specialist ────── [GATE 4: blueprint final]
```

**Saída:** `Discovery & Blueprint Document` com 13 seções: product definition, business analysis, prioritization, tech requirements, architecture, tech lead plan, specialist notes, design guardrails, quality baselines, test plan, TDD delivery plan, stack conventions, workstreams.

**Gates de usuário:** 4 (escopo, tradeoffs, arquitetura, blueprint final)

**Duração típica:** Sem código escrito. Apenas análise e planejamento.

---

### /implement

**Objetivo:** Implementar a partir de um blueprint existente.

**Input obrigatório:** Discovery & Blueprint Document (saída do `/discovery` ou fornecido manualmente).

**Fluxo:**

```
/implement
    │
    ├─ Validação: blueprint existe na conversa?
    │   Não → pede ao usuário para rodar /discovery primeiro
    │
    └─ TechLead (BUILD mode)
         └─ TDD Specialist (failing tests first)
              └─ Test Automation Engineer (harness + fixtures)
                   └─ PARALLEL IMPLEMENTATION
                        ├─ Backend Dev
                        │   └─ (AI Engineer | DBA | Integration Engineer — por contexto)
                        └─ Frontend Dev
                   └─ Reviewer ────── loop backpressure ──────┐
                        │  APPROVED → QA                       │
                        │  CHANGES  → Backend Dev / Frontend Dev ─┘
                        └─ QA (pytest real execution)
                             │  PASS → TechLead (QUALITY-COMPLETE mode)
                             │  FAIL → Backend Dev / Frontend Dev
                             └─ PARALLEL QUALITY BENCH
                                  ├─ Security Reviewer
                                  ├─ Privacy Reviewer
                                  ├─ Compliance Reviewer
                                  ├─ Accessibility Reviewer
                                  ├─ Performance Engineer
                                  ├─ Observability Engineer
                                  ├─ Analytics Engineer
                                  └─ Integration QA
                             └─ Docs Writer
                                  └─ Jira/Confluence Specialist
                                       └─ PM ─────────────── [GATE 5: UAT]
```

**Gates de usuário:** 1 (UAT final)

**TDD obrigatório:** Sim. Exceção apenas se o repositório não tem stack de testes viável.

---

### /squad

**Objetivo:** Entrega end-to-end completa: discovery + build + release.

**Input:** Descrição da feature.

**Fluxo:** `/discovery` completo + `/implement` completo + release chain:

```
[Discovery Chain — Gates 1-4]
    └─ [Build Chain — Gate 5: UAT]
         └─ Platform Dev → DevOps → CI/CD → SRE → Release → TechLead
                                                      │
                                              [GO]    └─ Docs Writer → Jira/Confluence → PM
                                              [NO-GO] └─ TechLead (resolve blockers)
```

**Gates de usuário:** 5 (escopo, tradeoffs, arquitetura, blueprint, UAT)

**Quando usar vs /discovery + /implement separados:**

| Critério | /squad | /discovery → /implement |
|---|---|---|
| Escopo claro desde o início | Sim | Tanto faz |
| Quer revisar o blueprint antes de implementar | Não | Sim |
| Feature simples, confiança no processo | Sim | Não |
| Feature complexa com múltiplos times | Sim | Sim |

---

### /bug-fix

**Objetivo:** Corrigir um bug específico com root cause analysis, test-first e validação real.

**Input:** Symptom + expected behavior + reproduction steps.

**Fluxo:**

```
/bug-fix
    │
    ├─ [GATE: coleta symptom + expected + repro + context]
    │
    └─ TechLead (root cause analysis)
         │  ESCALATE → para se > 5 arquivos ou problema arquitetural
         └─ TDD Specialist (failing test que prova o bug)
              └─ Backend Dev ou Frontend Dev (fix mínimo)
                   └─ Reviewer (code quality check)
                        └─ QA (pytest real — confirma fix + sem regressão)
                             └─ Relatório final ao usuário
```

**Gates de usuário:** 1 (intake inicial — symptom + repro)

**Escalada para /squad se:** root cause revela problema arquitetural ou > 5 arquivos.

---

### /security-audit

**Objetivo:** Auditoria de segurança com ferramentas reais.

**Fluxo:**

```
/security-audit
    │
    ├─ Detecta stack (Python / JS / ambos)
    │
    ├─ Python: bandit + pip-audit + safety
    ├─ JS: npm audit ou yarn audit
    ├─ Grep por secrets hardcoded (API_KEY, SECRET, PASSWORD, TOKEN)
    │
    └─ Security Reviewer (análise dos resultados)
         └─ Relatório estruturado salvo em ai-docs/security-audit-YYYY-MM-DD.md
```

**Saída:** Relatório com findings por severidade (critical / major / minor / info), required fixes, e recomendações.

---

### /migration-plan

**Objetivo:** Planejar mudança de schema antes de alterar models.

**Fluxo:**

```
/migration-plan
    │
    ├─ Mapeia migrations existentes (Glob */migrations/0*.py)
    ├─ Lê models.py atuais
    ├─ Identifica mudanças pendentes
    │
    └─ Data Architect (estratégia de migração)
         └─ DBA (segurança: locking, rollback, índices)
              └─ Plano salvo em ai-docs/migration-plan-YYYY-MM-DD.md
```

**Saída:** Migration strategy com: schema delta, ordem de execução, backfill plan, rollback steps, risco de locking.

---

### /cloud-debug

**Objetivo:** Investigar problema em ambiente cloud/produção.

**Fluxo:**

```
/cloud-debug
    │
    ├─ Detecta provedores cloud (AWS, GCP, Azure, Docker, K8s)
    ├─ Coleta: logs recentes, status de containers/pods, env vars, conectividade
    │
    └─ SRE (análise de blast radius e estabilidade)
         └─ Observability Engineer (logs + métricas + traces)
              └─ DevOps (infra e containers)
                   └─ Diagnóstico salvo em ai-docs/cloud-debug-YYYY-MM-DD.md
```

---

### /dependency-check

**Objetivo:** Verificar saúde das dependências do projeto.

**Fluxo:**

```
/dependency-check
    │
    ├─ Python: pip list --outdated + pip-audit
    ├─ JS: npm outdated + npm audit
    ├─ Licenças: pip-licenses ou license-checker
    │
    └─ Relatório com: outdated (critical/major/minor), vulnerabilidades, licenças problemáticas
         └─ Salvo em ai-docs/dependency-check-YYYY-MM-DD.md
```

---

### /factory-retrospective

**Objetivo:** Analisar execuções recentes e melhorar o processo.

**Fluxo:**

```
/factory-retrospective
    │
    ├─ Lê logs em ai-docs/ (últimas execuções)
    ├─ Identifica: retry loops, gates rejeitados, agentes com alta taxa de erro
    ├─ Analisa padrões: qual tipo de erro mais comum?
    │
    └─ Recomendações:
         ├─ Melhorias de prompt para agentes específicos
         ├─ Ajustes de workflow
         └─ Salvo em ai-docs/retrospective-YYYY-MM-DD.md
```

---

### /pre-commit-lint

**Objetivo:** Configurar hook de lint automático antes de cada commit.

**Fluxo:**

```
/pre-commit-lint
    │
    ├─ Detecta stack e ferramentas disponíveis
    │   Python: ruff, black, isort
    │   JS/TS: eslint, prettier
    │
    └─ Configura PreToolUse hook no settings.json para rodar lint em arquivos staged
```

---

## 5. Os 40 agentes — papéis e especialidades

### Cadeia de Discovery (PM → TDD Specialist)

| Agente | Especialidade | Chama em seguida |
|---|---|---|
| `pm` | Problem statement, user stories, ACs | `business-analyst` |
| `business-analyst` | Domain rules, workflows, edge cases | `po` |
| `po` | Priorização, scope cuts, release increments | `planner` [após gate] |
| `planner` | Stack validation, technical feasibility, tradeoffs | `architect` [após gate] |
| `architect` | Hexagonal design, file plan, sequencing | `techlead` |
| `techlead` | Orquestrador das 3 fases: DISCOVERY / BUILD / QUALITY-COMPLETE | Veja seção 6 |
| `design-principles-specialist` | SOLID, DRY, Clean Arch, coupling/cohesion | `test-planner` |
| `test-planner` | Test matrix: unit/integration/e2e, test cases | `tdd-specialist` |
| `tdd-specialist` | Red-green-refactor cycles, failing test blueprints | Gate (DISCOVERY) / `reviewer` (BUILD) |

### Cadeia de Build (TechLead → PM)

| Agente | Especialidade | Chama em seguida |
|---|---|---|
| `backend-dev` | APIs, services, auth, persistence, queues | `reviewer` |
| `frontend-dev` | UI, routing, state, accessibility, frontend tests | `reviewer` |
| `reviewer` | Code review: bugs, security, quality, TDD gate, lint | `qa` (approved) / impl (changes) |
| `qa` | Test execution real (pytest), AC validation, regressions | `techlead` (pass) / impl (fail) |
| `docs-writer` | Technical docs, migration notes, changelog | `jira-confluence-specialist` |
| `jira-confluence-specialist` | Jira issues, epics, stories, Confluence pages (via MCP Atlassian) | `pm` (UAT) |

### Cadeia de Infraestrutura

| Agente | Especialidade | Chama em seguida |
|---|---|---|
| `platform-dev` | Background workers, job queues, developer tooling, integration glue | `devops` |
| `devops` | Containers, IaC, secrets, scaling, DR | `ci-cd` |
| `ci-cd` | Pipelines, quality gates, artifact flow, deploy stages | `sre` |
| `sre` | Blast radius, SLOs, rollback readiness, canary strategy | `release` (GO) / `techlead` (NO-GO) |
| `release` | Release checklist, change inventory, pre-deploy checklist | `techlead` |

### Especialistas de Arquitetura (bench paralelo — DISCOVERY)

| Agente | Especialidade | Chama em seguida |
|---|---|---|
| `backend-architect` | APIs, services, domain layer, TDD order | `ai-engineer` (se AI) / `data-architect` (se schema) |
| `frontend-architect` | UI structure, routing, state, client error handling | `ux-designer` |
| `data-architect` | Schema evolution, migrations, event flows | `dba` |
| `api-designer` | REST/GraphQL contracts, versioning, error models | `integration-engineer` (se APIs externas) |
| `ux-designer` | User flows, interaction states, microcopy, accessibility | `techlead` (retorna) |
| `dba` | Migration safety, locking, indexes, rollback | `techlead` (retorna) |
| `ai-engineer` | Prompt contracts, tool use, RAG, evals, latency | `techlead` (retorna) |
| `integration-engineer` | Third-party contracts, retries, idempotency, failure handling | `techlead` (retorna) |

### Bench de Qualidade (paralelo — QUALITY-COMPLETE)

| Agente | Especialidade | Chama em seguida |
|---|---|---|
| `security-reviewer` | Auth, authz, injection, secrets, OWASP — roda bandit/pip-audit | `techlead` (retorna) |
| `privacy-reviewer` | PII exposure, data minimization, consent, masking | `techlead` (retorna) |
| `compliance-reviewer` | Audit trail, GDPR/LGPD/PCI, regulated data, traceability | `techlead` (retorna) |
| `accessibility-reviewer` | WCAG, keyboard nav, ARIA, contrast, focus | `techlead` (retorna) |
| `performance-engineer` | Latency, throughput, query cost, caching, load | `techlead` (retorna) |
| `observability-engineer` | Logs, system metrics, traces, alerts, Grafana/Prometheus | `techlead` (retorna) |
| `analytics-engineer` | Product events, funnels, A/B tests, product dashboards | `techlead` (retorna) |
| `integration-qa` | Contract validation, cross-service flows, external dependencies | `techlead` (retorna) |

### Especialistas On-demand

| Agente | Quando é chamado | Chama em seguida |
|---|---|---|
| `test-automation-engineer` | TDD Specialist ou QA precisam de harness/fixtures | Caller (retorna) |
| `code-quality` | Reviewer detecta tech debt sistemático | `reviewer` (retorna) |
| `cost-optimizer` | SRE ou DevOps precisam de análise de custos | `dba` (se query cost) / caller |
| `incident-manager` | Usuário ou SRE declaram incidente | Paralelo: `sre` + `devops` + `observability-engineer` |

---

## 6. Arquitetura da esteira

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
│                    ┌─────────┼─────────┐                                │
│                    ▼         ▼         ▼                                │
│             backend-arch  frontend-arch  api-designer                   │
│                    │         │              │                            │
│                    ▼         ▼              ▼                            │
│            data-arch→dba  ux-designer  integ-engineer                   │
│                    │                                                     │
│                    ▼                                                     │
│              design-principles → test-planner → tdd-specialist          │
│                                                        │                 │
│                                               [GATE 4: blueprint]       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  BUILD CHAIN                                                             │
│                                                                         │
│  techlead (BUILD) → tdd-specialist → test-automation-engineer           │
│                          │                                              │
│               ┌──────────┴──────────┐                                   │
│               ▼                     ▼                                   │
│          backend-dev           frontend-dev                             │
│          (+ ai-eng | dba)            │                                  │
│               └──────────┬──────────┘                                   │
│                          ▼                                              │
│                       reviewer ◄─────────────────────┐                 │
│                    APPROVED │    CHANGES REQUESTED    │                 │
│                          ▼                            │                 │
│                         qa ──── FAIL ─────────────────┘                │
│                       PASS │                                            │
│                          ▼                                              │
│                    techlead (QUALITY)                                   │
│                          │                                              │
│        ┌─────────────────┼─────────────────┐                           │
│        ▼                 ▼                 ▼                            │
│   security-rev     privacy-rev     compliance-rev                       │
│   accessibility    performance     observability                        │
│   analytics        integration-qa                                       │
│        └─────────────────┼─────────────────┘                           │
│                          ▼                                              │
│                     docs-writer → jira-confluence → pm ──[GATE 5: UAT] │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  OPS CHAIN (apenas /squad)                                               │
│                                                                         │
│  platform-dev → devops → ci-cd → sre ──[GO]── release → techlead       │
│                                    └─[NO-GO]── techlead (fix blockers) │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  BUG-FIX CHAIN                                                           │
│                                                                         │
│  skill ──[GATE: intake]── techlead → tdd-specialist                     │
│                                           → backend/frontend-dev        │
│                                                → reviewer → qa          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  INCIDENT CHAIN                                                          │
│                                                                         │
│  incident-manager ──┬── sre                                             │
│                     ├── devops            (paralelo)                    │
│                     └── observability-engineer                          │
│                          │                                              │
│                     [resolução]                                         │
│                          ▼                                              │
│                     techlead (BUILD) — se código precisar mudar         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Gates de usuário

Os gates são os únicos momentos onde a esteira para e espera input humano.

| Gate | Quem apresenta | O que decidir |
|---|---|---|
| **Gate 1** — Scope Validation | `po` | O escopo definido está correto? Cortes necessários? |
| **Gate 2** — Technical Tradeoffs | `planner` | Qual abordagem técnica seguir? (stack, lib, pattern) |
| **Gate 3** — Architecture Direction | `techlead` | A arquitetura hexagonal proposta faz sentido? |
| **Gate 4** — Blueprint Confirmation | `tdd-specialist` | O blueprint de testes e implementação está aprovado? |
| **Gate 5** — UAT | `pm` | A feature entregue atende aos critérios de aceitação? |

**Regra:** Nenhum gate pode ser pulado. Responder ao gate é o que move a esteira para a próxima fase.

---

## 8. Visibilidade de execução

Toda skill emite linhas de progresso no terminal:

```
[Phase Start] discovery
[Agent Start] PM | claude-tech-squad:pm | Problem framing and user stories
[Agent Done] PM | Status: completed | Output: 3 user stories, 8 ACs defined
[Agent Start] Business Analyst | claude-tech-squad:business-analyst | Domain rules
[Agent Done] Business Analyst | Status: completed | Output: 5 domain rules, 2 edge cases
[Agent Blocked] PO | Waiting on: user scope validation (Gate 1)

[Agent Batch Start] specialist-bench | Agents: backend-architect, frontend-architect, api-designer
[Agent Start] Backend Architect | claude-tech-squad:backend-architect | API and service design
[Agent Start] Frontend Architect | claude-tech-squad:frontend-architect | Component structure
[Agent Start] API Designer | claude-tech-squad:api-designer | Contract definition
[Agent Done] Backend Architect | Status: completed | Output: 3 endpoints, hexagonal layers defined
[Agent Done] Frontend Architect | Status: completed | Output: 4 components, routing plan
[Agent Done] API Designer | Status: completed | Output: REST contract v1, error model defined
[Agent Batch Done] specialist-bench | Outcome: 3 specialist notes ready

[Agent Retry] Reviewer | Reason: backend-dev returned critical security issue
```

O log completo de execução é incluído na saída final de cada skill.

---

## 9. Regras de uso

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

### Regras de escalada

- `/bug-fix` → `/squad`: quando root cause revela problema arquitetural ou > 5 arquivos
- `/discovery` sozinho: quando não há certeza se vai implementar agora
- `/implement` requer blueprint: sem Discovery & Blueprint Document, a skill pede para rodar `/discovery` primeiro

### TDD

- `/squad` e `/implement`: TDD obrigatório por padrão
- `/bug-fix`: TDD obrigatório (failing test antes do fix)
- Exceção declarada explicitamente quando o repositório não tem stack de testes viável

### Autonomia

Os agentes trabalham de forma autônoma entre os gates. Não é necessário (e nem recomendado) interagir com o terminal entre um gate e outro. A esteira vai se mover sozinha.

---

## 10. Referência rápida

### Skills por contexto

```bash
# Feature nova completa
/claude-tech-squad:squad "implementar autenticação com OAuth Google"

# Só planejar agora, implementar depois
/claude-tech-squad:discovery "refatorar sistema de pagamentos para suportar PIX"

# Implementar com blueprint pronto na conversa
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

### Quem chama quem (resumo)

```
pm → ba → po → planner → architect → techlead
techlead → [bench paralelo] → design-principles → test-planner → tdd-specialist
tdd-specialist → [impl paralelo] → reviewer → qa → techlead (quality)
techlead → [quality bench paralelo] → docs-writer → jira-confluence → pm
platform-dev → devops → ci-cd → sre → release → techlead
```

### Fluxos alternativos por contexto

```
AI feature:        backend-architect → ai-engineer → techlead
Schema change:     data-architect → dba → techlead
External APIs:     api-designer → integration-engineer → techlead
UI feature:        frontend-architect → ux-designer → techlead
Tech debt:         reviewer → code-quality → reviewer
Query cost:        cost-optimizer → dba → sre
Incidente:         incident-manager → {sre + devops + observability} → techlead
```
