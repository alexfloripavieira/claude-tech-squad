# Claude Tech Squad — Manual Técnico

**Versão:** 5.4.0
**Plugin:** `claude-tech-squad`

---

## Índice

1. [O que é o plugin](#1-o-que-é-o-plugin)
2. [Instalação e ativação](#2-instalação-e-ativação)
3. [Teammate Mode — panes tmux por agente](#3-teammate-mode--panes-tmux-por-agente)
4. [Skills disponíveis e quando usar cada uma](#4-skills-disponíveis-e-quando-usar-cada-uma)
5. [Fluxo completo de cada skill](#5-fluxo-completo-de-cada-skill)
6. [Os 59 agentes — papéis e especialidades](#6-os-59-agentes--papéis-e-especialidades)
7. [Arquitetura da esteira](#7-arquitetura-da-esteira)
8. [Gates de usuário](#8-gates-de-usuário)
9. [Visibilidade de execução](#9-visibilidade-de-execução)
10. [Regras de uso](#10-regras-de-uso)
11. [Referência rápida](#11-referência-rápida)
12. [Absolute Prohibitions — guardrails de segurança](#12-absolute-prohibitions--guardrails-de-segurança)
13. [Squad Execution Protocol (SEP) — artefatos e rastreabilidade](#13-squad-execution-protocol-sep--artefatos-e-rastreabilidade)

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

**Saída:** Discovery & Blueprint Document com 13 seções + artefatos SEP:
- `ai-docs/{feature}/blueprint.md`
- `ai-docs/.squad-log/{timestamp}-discovery-{run_id}.md`

**Gates de usuário:** 4 + 1 bridge gate (Contrato 3)

O último gate após o blueprint apresenta:
```
Quer iniciar a implementação agora? [S/N]
```
Se S: invoca `/implement` imediatamente com o blueprint.
Se N: registra `implement_triggered: false` no log — detectável pelo `/factory-retrospective` como orphaned discovery.

---

### /implement

**Objetivo:** Implementar a partir de um blueprint existente.

**Input obrigatório:** Discovery & Blueprint Document.

**Fluxo:**

```
/implement
    │
    ├─ Step 0: Stack Command Detection (SEP)
    │   Lê Makefile / package.json / pyproject.toml / pom.xml
    │   → detecta test_command, migrate_command, lint_command
    │   → override por CLAUDE.md se existir
    │   Injeta {{project_commands}} em todos os agentes
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

**Saída SEP:** `ai-docs/.squad-log/{timestamp}-implement-{run_id}.md` com Completion Blocks de cada agente implementador e resultado do UAT.

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

### /security-audit

Além do relatório principal (`ai-docs/security-audit-YYYY-MM-DD.md`), gera automaticamente:
- `ai-docs/security-remediation-YYYY-MM-DD.md` — checkboxes por severidade para rastreamento de correções (Contrato 2)
- `ai-docs/.squad-log/{timestamp}-security-audit-{run_id}.md` — log SEP com contagem de findings

### /dependency-check

Além do relatório principal (`ai-docs/dependency-check-YYYY-MM-DD.md`), gera automaticamente:
- `ai-docs/dependency-remediation-YYYY-MM-DD.md` — checkboxes por CVE e major updates
- `ai-docs/.squad-log/{timestamp}-dependency-check-{run_id}.md` — log SEP

### /factory-retrospective

Lê `ai-docs/.squad-log/` como fonte primária (SEP-aware desde v5.4.0). Detecta:
- **Orphaned discoveries**: logs com `implement_triggered: false`
- **Taxa de remediação**: razão `- [x]` / `- [ ]` nos arquivos de remediation
- **Retry rate**: média de `retry_count` por skill
- **UAT rejection rate**: logs com `uat_result: REJECTED`

Fallback para inferência por git log e markdown quando não há logs SEP.

### /migration-plan, /cloud-debug, /pre-commit-lint

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
| **Gate Bridge** — Implement Now? | orchestrador | Iniciar `/implement` imediatamente? (SEP Contrato 3) |
| **Gate 5** — UAT | `pm` | A feature entregue atende aos critérios de aceitação? |

Nenhum gate pode ser pulado. Responder ao gate é o que move a esteira para a próxima fase.

O **Gate Bridge** é o único gate que não bloqueia a esteira — responder N registra `implement_triggered: false` no log e encerra o `/discovery` normalmente.

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
[SEP Log Written] ai-docs/.squad-log/2026-03-24T21-00-00-implement-abc123.md
```

### Linhas SEP (v5.4.0+)

```
[SEP Log Written] ai-docs/.squad-log/{filename}
[Remediation Tasks Written] ai-docs/security-remediation-YYYY-MM-DD.md
[Gate] implement-bridge | Waiting for user input
```

Essas linhas aparecem ao final de cada skill que implementa o Squad Execution Protocol. O `[Gate] implement-bridge` aparece apenas no `/discovery` após o blueprint ser confirmado.

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

---

## 12. Absolute Prohibitions — guardrails de segurança

Todos os agentes com autoridade de execução carregam um bloco de **Absolute Prohibitions** no pre-prompt. Essas restrições não podem ser sobrescritas por urgência de incidente, pressão de prazo ou pedido verbal.

### Operações globalmente bloqueadas (todos os agentes)

Exigem **confirmação escrita explícita do usuário** antes de qualquer execução:

| Operação | Contexto |
|---|---|
| `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` | qualquer ambiente |
| `tsuru app-remove`, equivalentes PaaS/cloud | produção |
| Deletar recursos cloud com dados (buckets S3/GCS, RDS, clusters) | produção |
| Merge para `main`/`master`/`develop` sem PR aprovado | sempre |
| `git push --force` em branch protegido | sempre |
| Remover secrets ou env vars de produção | produção |
| Deploy sem plano de rollback documentado e testado | produção |
| Desabilitar autenticação/autorização como workaround | sempre |
| Destruir infraestrutura (`terraform destroy`) | sempre |

### Restrições por agente

| Agente | Restrição crítica específica |
|---|---|
| `chaos-engineer` | Experimentos em produção exigem janela de manutenção + on-call + abort procedure. Staging é o padrão. |
| `security-engineer` | Nunca revogar tokens sem substituto pronto. Nunca desabilitar auth ou CORS. WAF testado em staging antes. |
| `cost-optimizer` | Nunca deletar buckets, databases ou instâncias para "economizar". Validar com DevOps/SRE antes. |
| `ml-engineer` | Nunca promover modelo sem rollback. Nunca deletar versão servindo tráfego. Mesmo padrão de um deploy. |
| `mobile-dev` | Nunca submeter direto para produção na App Store/Play Store. Staged rollout obrigatório. |
| `sre` | GO sem rollback documentado é proibido. Pressão de negócio não sobrescreve o NO-GO. |
| `incident-manager` | Urgência do incidente não sobrescreve nenhuma restrição. Propor mitigação menos destrutiva primeiro. |
| `techlead` | Como autoridade de execução, intercepta e bloqueia qualquer especialista que solicite operação proibida. |

### Global Safety Contract

Os três orchestradores principais (`/discovery`, `/implement`, `/squad`) carregam um **Global Safety Contract** que propaga automaticamente todas essas restrições para cada teammate que spawnam.

O contrato é lido por todos os agentes independentemente de operarem como inline subagent ou como teammate em pane tmux separado.

---

## 13. Squad Execution Protocol (SEP) — artefatos e rastreabilidade

O SEP é um conjunto de quatro contratos stack-agnósticos que cobrem observabilidade, continuidade e remediação em todos os workflows da squad. Funciona tanto quando Claude opera como **inline subagent** quanto como **teammate em painel tmux separado** — o log persiste no disco independentemente do modo de execução.

### Contratos

| Contrato | Nome | Skills que implementam |
|---|---|---|
| C1 | Execution Log | `/discovery`, `/implement`, `/security-audit`, `/dependency-check` |
| C2 | Remediation Tasks | `/security-audit`, `/dependency-check` |
| C3 | Discovery → Implement Bridge Gate | `/discovery` |
| C4 | Task Completion Block | `/implement` (por agente de implementação) |

---

### C1 — Execution Log

Cada skill escreve um log estruturado em `ai-docs/.squad-log/` ao finalizar:

```
ai-docs/.squad-log/YYYY-MM-DDTHH-MM-SS-{skill}-{run_id}.md
```

**Formato (YAML frontmatter):**

```yaml
---
run_id: abc123
skill: discovery | implement | security-audit | dependency-check
timestamp: 2026-03-24T14:30:00Z
status: completed | failed | partial
retry_count: 0
gates_blocked: []
implement_triggered: false          # apenas /discovery
findings_critical: 0                # apenas /security-audit
findings_high: 0                    # apenas /security-audit
vulnerabilities_critical: 0        # apenas /dependency-check
major_updates: 0                    # apenas /dependency-check
remediation_artifact: ai-docs/...  # C2, quando aplicável
uat_result: PASS | REJECTED         # apenas /implement
---
```

Os logs são a fonte primária do `/factory-retrospective` para calcular métricas: taxa de rejeição UAT, gates bloqueados com mais frequência, tempo médio de retry por skill, descobertas sem implementação.

---

### C2 — Remediation Tasks

`/security-audit` e `/dependency-check` produzem arquivos de remediação com checkboxes:

```
ai-docs/security-remediation-YYYY-MM-DD.md
ai-docs/dependency-remediation-YYYY-MM-DD.md
```

**Estrutura:**

```markdown
# Security Remediation Tasks — YYYY-MM-DD

> Auto-generated by /security-audit. Check off items as they are fixed.

## Phase 1 — Immediate (Critical + High)
- [ ] [CRIT-1] SQL injection in views.py:142 — parameterize query
- [x] [HIGH-1] Hardcoded secret in config.py:89 — use env var

## Phase 2 — Short-term (Medium)
- [ ] [MED-1] ...
```

O `/factory-retrospective` computa a **taxa de fechamento** (`[x]` / total) por arquivo para medir progresso de remediação entre runs.

---

### C3 — Discovery → Implement Bridge Gate

Ao final do `/discovery`, o orchestrador pergunta:

```
Discovery concluído. Quer iniciar a implementação agora? [S/N]
```

- **S**: atualiza `implement_triggered: true` no log SEP e invoca `/implement` automaticamente com o blueprint gerado.
- **N**: mantém `implement_triggered: false`. O `/factory-retrospective` detecta essas descobertas como **orphaned discoveries** — planejamentos que nunca foram implementados.

Isso elimina o gap onde o blueprint existia mas a implementação nunca era iniciada, tornando o abandono visível nas métricas.

---

### C4 — Task Completion Block

Cada agente de implementação no `/implement` deve retornar um bloco estruturado ao finalizar sua tarefa:

```markdown
## Completion Block
- Task: implementar endpoint de criação de Lead
- Status: completed
- Files changed: [django/approvals/views.py, django/approvals/serializers.py]
- Tests run: docker compose exec django python -m pytest /tests/backend/unit/approvals/ -v → PASS
- Test count: 14 passed, 0 failed
```

O orchestrador usa esses blocos para validar progresso e detectar falhas silenciosas onde o agente "completou" sem rodar testes.

---

### Stack Command Detection (Step 0 do /implement)

Para garantir que os agentes usem os comandos corretos independentemente da stack do projeto, o `/implement` detecta automaticamente os comandos disponíveis antes de iniciar:

| Arquivo detectado | Comandos extraídos |
|---|---|
| `Makefile` | targets `test`, `migrate`, `run`, `build` |
| `package.json` | scripts `test`, `build`, `lint`, `dev` |
| `pyproject.toml` | configuração pytest, poetry scripts |
| `pom.xml` | `mvn test`, `mvn package` |
| `build.gradle` | `./gradlew test`, `./gradlew build` |

Os comandos detectados são injetados como `{{project_commands}}` em todos os prompts dos agentes de implementação. **Regras de CLAUDE.md têm precedência** sobre os valores detectados.

---

### Estrutura completa de artefatos SEP

```
ai-docs/
├── .squad-log/                              ← C1: logs de execução (todos os runs)
│   ├── 2026-03-24T14-30-00-discovery-abc123.md
│   ├── 2026-03-24T15-00-00-implement-def456.md
│   ├── 2026-03-24T16-00-00-security-audit-ghi789.md
│   └── 2026-03-24T17-00-00-dependency-check-jkl012.md
├── security-remediation-2026-03-24.md       ← C2: tarefas de remediação de segurança
├── dependency-remediation-2026-03-24.md     ← C2: tarefas de remediação de dependências
├── .last-retro                              ← timestamp do último /factory-retrospective
└── {feature}/
    └── blueprint.md                         ← saída do /discovery (existente)
```

---

### Como o /factory-retrospective usa os logs SEP

Quando logs SEP existem em `ai-docs/.squad-log/`, o `/factory-retrospective` extrai métricas diretamente do frontmatter YAML em vez de inferir padrões de texto:

| Métrica | Campo YAML | Descrição |
|---|---|---|
| Taxa de rejeição UAT | `uat_result: REJECTED` | % de runs do `/implement` rejeitados no gate UAT |
| Retry médio por skill | `retry_count` | Média de retries necessários por skill |
| Gates mais bloqueados | `gates_blocked` | Gates que mais frequentemente pararam o workflow |
| Orphaned discoveries | `implement_triggered: false` | Blueprints gerados mas nunca implementados |
| Taxa de remediação | `[x]` vs `[ ]` nos arquivos C2 | Progresso de fechamento de findings de segurança/deps |

Quando **não existem** logs SEP (runs anteriores ao v5.4.0), o retrospective cai automaticamente para inferência baseada em artefatos markdown e git history.
