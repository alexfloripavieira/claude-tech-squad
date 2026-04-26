# Tech Spec: Claude Tech Squad Console e Observabilidade

## Resumo Executivo

A solucao sera uma aplicacao local composta por API fina, frontend operacional e indexador de SEP logs. A API consome o SDK Python e, quando necessario, invoca `squad-cli`; o frontend apenas visualiza contratos e solicita acoes. As regras de planejamento continuam em `squad_cli.ticket`, `squad_cli.sdk`, skills e runtime policy.

O MVP deve priorizar modo local/read-only: planejar tickets, visualizar dashboard, listar runs e consultar detalhes. Integracoes live e mutacoes externas entram depois, com confirmacao explicita e auditoria.

## Arquitetura do Sistema

### Visao Geral dos Componentes

- Claude Code Plugin
  - Fonte de verdade para agents, skills, runtime policy e contratos.
  - Continua funcionando sem frontend.

- SDK Python (`squad_cli.sdk`)
  - Facade publica para `onboarding_plan`, `dashboard_report`, `ticket_plan` e `ticket_plan_from_context`.
  - Base para API e automacoes.

- Console API
  - API local HTTP.
  - Encapsula SDK, indexa SEP logs e fornece endpoints para frontend.
  - Nao duplica regras de recomendacao de skill.

- SEP Log Indexer
  - Le `ai-docs/.squad-log/*.md`.
  - Extrai frontmatter, resumo e metadados.
  - Popula banco local para consultas rapidas.

- Banco Local
  - SQLite no MVP.
  - Armazena indice de runs, planos, tickets e eventos.
  - Markdown original continua no filesystem.

- Frontend Console
  - UI operacional para ticket planning, dashboard e run history.
  - Chama apenas a API.

- External Source Adapters
  - GitHub/Jira/Linear read-only inicialmente.
  - Convertem resposta externa para `TicketContext`.

Fluxo de dados:

```text
Frontend -> Console API -> SDK/CLI -> Plugin contracts
                         -> SEP logs -> SQLite index -> Frontend
External APIs -> Adapters -> TicketContext -> TicketPlan
```

## Design de Implementacao

### Interfaces Principais

```python
class ConsoleService:
    def plan_ticket(self, request: TicketPlanRequest) -> TicketPlanResponse: ...
    def list_runs(self, filters: RunFilters) -> RunListResponse: ...
    def get_run(self, run_id: str) -> RunDetailResponse: ...
    def dashboard(self, limit: int = 30) -> DashboardResponse: ...
```

```python
class TicketSourceClient:
    source: str
    def fetch_ticket(self, identifier: str) -> dict: ...
    def to_context(self, payload: dict) -> TicketContext: ...
```

```python
class EventSink:
    def emit(self, event_type: str, payload: dict) -> None: ...
```

### Modelos de Dados

Principais modelos de dominio:

- `TicketContext`
- `TicketPlan`
- `DashboardReport`
- `SepRun`
- `RunEvent`
- `ExternalUpdatePreview`
- `ExternalUpdateResult`

Tabelas SQLite propostas:

```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    skill TEXT NOT NULL,
    status TEXT NOT NULL,
    ticket_source TEXT,
    ticket_id TEXT,
    timestamp TEXT,
    sep_log_path TEXT NOT NULL,
    estimated_cost_usd REAL,
    tokens_input INTEGER,
    tokens_output INTEGER
);
```

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    run_id TEXT,
    ticket_id TEXT,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

```sql
CREATE TABLE ticket_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_source TEXT NOT NULL,
    ticket_id TEXT NOT NULL,
    recommended_skill TEXT NOT NULL,
    complexity_tier TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### Endpoints de API

- `GET /api/health`
  - Retorna status da API, paths configurados e versao do SDK.

- `GET /api/dashboard?limit=30`
  - Retorna `DashboardReport`.

- `GET /api/runs`
  - Lista runs indexados com filtros por skill, status, source e periodo.

- `GET /api/runs/{run_id}`
  - Retorna detalhe do run e conteudo/metadata do SEP log.

- `POST /api/tickets/plan`
  - Recebe `raw`, `ticket_json` ou `text`.
  - Retorna `TicketPlan` ou lista de planos.

- `POST /api/tickets/fetch`
  - Busca ticket externo em modo read-only.
  - Retorna payload bruto e contexto normalizado.

- `POST /api/tickets/update-preview`
  - Gera preview de comentario/status.
  - Nao executa mutacao.

- `POST /api/tickets/update-confirmed`
  - Executa mutacao externa apos confirmacao.
  - Registra evento auditavel.

## Pontos de Integracao

- GitHub Issues
  - Preferir GitHub App ou token local fora do repo.
  - Inicialmente read-only: issue, labels, body, comments.

- Jira
  - Usar MCP/tool existente quando disponivel ou API REST configurada.
  - Suportar issue key e JQL.

- Linear
  - Usar MCP/tool quando disponivel ou API configurada.

Tratamento de erro:

- Falha de credencial retorna erro normalizado com fallback sugerido.
- Timeout externo nao bloqueia modo pasted/JSON.
- Mutacao externa exige confirmacao e gera audit event.

## Abordagem de Testes

### Testes Unidade

- Adapters GitHub/Jira/Linear para payloads reais anonimizados.
- Conversao de JSON externo para `TicketContext`.
- Serializacao `.to_json()`.
- Erros SDK/API normalizados.
- Indexador SEP log.

### Testes de Integracao

- API chamando SDK real.
- API planejando ticket single e batch.
- API lendo SEP logs sinteticos.
- SQLite indexando runs.
- Release bundle importando SDK e exemplos.

### Testes de E2E

- Playwright para:
  - abrir dashboard;
  - planejar ticket colado;
  - abrir detalhe do plano;
  - listar runs;
  - verificar estado vazio quando nao ha SEP logs;
  - garantir que nenhuma mutacao externa ocorre sem confirmacao.

## Sequenciamento de Desenvolvimento

### Ordem de Construcao

1. Congelar schemas e fixtures
   - Necessario antes de API/UI para evitar duplicacao de contrato.

2. Criar Console API local
   - Primeiro com `health`, `dashboard`, `tickets/plan` e `runs`.

3. Criar indexador SQLite de SEP logs
   - Habilita filtros e historico navegavel.

4. Criar frontend MVP
   - Dashboard, Ticket Planner, Plan Detail e Run History.

5. Adicionar observability events
   - Eventos estruturados para planejamento, falha, fallback e update.

6. Integrar GitHub read-only
   - Menor friccao para golden run no proprio repo.

7. Integrar Jira/Linear read-only
   - Depois que contratos e fallback estiverem firmes.

8. Adicionar preview/confirmacao de mutacoes externas
   - Comentarios/status apenas apos confirmacao explicita.

9. Golden runs live
   - Provar fluxo UI/API/CLI com ticket real/sandbox e fallback.

### Dependencias Tecnicas

- Python 3 atual do repo.
- FastAPI ou alternativa leve para API local.
- SQLite.
- Frontend React/Vue conforme decisao futura.
- Playwright para E2E.
- Credenciais externas opcionais fora do repo.

## Monitoramento e Observabilidade

Eventos estruturados:

- `ticket.plan.created`
- `ticket.plan.failed`
- `ticket.fetch.started`
- `ticket.fetch.failed`
- `run.indexed`
- `run.completed`
- `run.failed`
- `fallback.invoked`
- `external_update.previewed`
- `external_update.confirmed`
- `external_update.failed`

Metricas iniciais:

- runs por skill;
- taxa de sucesso;
- custo estimado por skill;
- tokens input/output;
- gates bloqueados;
- fallbacks por fonte;
- tickets planejados por fonte;
- tempo medio por run;
- hotfixes sem postmortem.

Logs:

- JSON logs na API.
- `trace_id` por request.
- `run_id` e `ticket_id` em eventos relacionados.

## Consideracoes Tecnicas

### Decisoes Principais

- Frontend nao duplica regra de negocio.
  - Justificativa: evita divergencia com plugin/CLI.

- SQLite antes de Postgres.
  - Justificativa: MVP local, simples e auditavel.

- Markdown SEP log continua fonte auditavel.
  - Justificativa: preserva contrato atual e revisabilidade em Git.

- Integracoes live comecam read-only.
  - Justificativa: reduz risco de mutacao indevida.

### Riscos Conhecidos

- Risco: UI virar segunda implementacao do plugin.
  - Mitigacao: toda decisao vem do SDK/CLI.

- Risco: ticket externo conter prompt injection.
  - Mitigacao: tratar ticket como dado nao confiavel, sanitizar HTML e destacar origem.

- Risco: credenciais vazarem.
  - Mitigacao: nunca persistir no repo, usar env/local secret store.

- Risco: SEP logs nao terem schema uniforme suficiente.
  - Mitigacao: schema validator e fixtures antes da UI avancada.

- Risco: escopo crescer para executor autonomo.
  - Mitigacao: MVP read-only/planejamento, mutacoes com confirmacao.

### Conformidade com Skills Padroes

- `/discovery`: refinar contratos, riscos e arquitetura antes de implementacao.
- `/implement`: construir API, indexador e UI MVP.
- `/squad`: coordenar frontend, backend, SDK e observabilidade quando o trabalho for paralelo.
- `/security-audit`: revisar credenciais, prompt injection, RBAC e mutacoes externas.
- `/from-ticket`: usar o proprio fluxo de tickets como entrada para desenvolvimento futuro.
- `/dashboard`: manter compatibilidade com relatorios atuais.

### Arquivos relevantes e dependentes

- `plugins/claude-tech-squad/bin/squad_cli/sdk.py`
- `plugins/claude-tech-squad/bin/squad_cli/ticket.py`
- `plugins/claude-tech-squad/bin/squad_cli/ticket_sources/`
- `plugins/claude-tech-squad/bin/squad_cli/dashboard.py`
- `plugins/claude-tech-squad/bin/squad_cli/sep_log.py`
- `plugins/claude-tech-squad/skills/from-ticket/SKILL.md`
- `plugins/claude-tech-squad/skills/dashboard/SKILL.md`
- `scripts/test-sdk.sh`
- `scripts/smoke-test.sh`
- `docs/SDK.md`
- `ai-docs/.squad-log/`
- `ai-docs/dogfood-runs/`
