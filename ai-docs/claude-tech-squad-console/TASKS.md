# Resumo de Tarefas de Implementacao de Claude Tech Squad Console e Observabilidade

## Tarefas

- [X] 1.0 Congelar contratos e schemas
  - [X] 1.1 Documentar `TicketContext`, `TicketPlan`, `DashboardReport`, `SepRun` e eventos.
  - [X] 1.2 Criar fixtures JSON para Jira, Linear, GitHub, pasted e batch.
  - [X] 1.3 Adicionar validacao de schema ao smoke test.
  - [X] 1.4 Definir politica de compatibilidade dos contratos SDK/API.

- [X] 2.0 Fortalecer Fase 4 para integracoes futuras
  - [X] 2.1 Adicionar testes unitarios para adapters locais.
  - [X] 2.2 Definir interface `TicketSourceClient`.
  - [X] 2.3 Implementar fallback formal quando fonte externa falhar.
  - [X] 2.4 Adicionar payloads anonimizados reais ou sandbox para fixtures.
  - [X] 2.5 Preparar golden run de fallback sem credenciais.

- [ ] 3.0 Fortalecer Fase 5 como base da API
  - [ ] 3.1 Expandir `scripts/test-sdk.sh` ou criar suite Python formal.
  - [ ] 3.2 Validar SDK importado de release bundle empacotado.
  - [ ] 3.3 Normalizar erros com codigo, mensagem e source.
  - [ ] 3.4 Documentar API publica v1 em `docs/SDK.md`.

- [ ] 4.0 Criar Console API local
  - [ ] 4.1 Escolher framework HTTP leve.
  - [ ] 4.2 Implementar `GET /api/health`.
  - [ ] 4.3 Implementar `POST /api/tickets/plan`.
  - [ ] 4.4 Implementar `GET /api/dashboard`.
  - [ ] 4.5 Implementar `GET /api/runs`.
  - [ ] 4.6 Implementar `GET /api/runs/{run_id}`.
  - [ ] 4.7 Adicionar testes de integracao da API.

- [ ] 5.0 Criar indexador de SEP logs
  - [ ] 5.1 Definir schema SQLite inicial.
  - [ ] 5.2 Implementar parser/indexador incremental.
  - [ ] 5.3 Preservar link para Markdown original.
  - [ ] 5.4 Adicionar filtros por skill, status, ticket source e periodo.
  - [ ] 5.5 Testar com SEP logs sinteticos e golden runs existentes.

- [ ] 6.0 Criar frontend MVP
  - [ ] 6.1 Escolher stack frontend.
  - [ ] 6.2 Criar tela Dashboard.
  - [ ] 6.3 Criar tela Ticket Planner.
  - [ ] 6.4 Criar tela Plan Detail.
  - [ ] 6.5 Criar tela Run History.
  - [ ] 6.6 Criar estados vazios, erro, loading e fallback.
  - [ ] 6.7 Adicionar Playwright E2E para fluxos principais.

- [ ] 7.0 Adicionar observabilidade operacional
  - [ ] 7.1 Definir eventos estruturados.
  - [ ] 7.2 Emitir `ticket.plan.created` e `ticket.plan.failed`.
  - [ ] 7.3 Emitir eventos de fallback.
  - [ ] 7.4 Emitir eventos de indexacao de run.
  - [ ] 7.5 Expor metricas agregadas no dashboard.

- [ ] 8.0 Integrar fontes externas read-only
  - [ ] 8.1 Implementar GitHub Issues read-only.
  - [ ] 8.2 Criar golden run com GitHub Issue real ou sandbox.
  - [ ] 8.3 Implementar Jira read-only.
  - [ ] 8.4 Implementar JQL/batch real para Jira.
  - [ ] 8.5 Implementar Linear read-only quando tool/API estiver disponivel.

- [ ] 9.0 Implementar mutacoes externas com confirmacao
  - [ ] 9.1 Criar preview de comentario/status.
  - [ ] 9.2 Exigir confirmacao explicita na API e UI.
  - [ ] 9.3 Registrar audit event da confirmacao.
  - [ ] 9.4 Implementar comentario em GitHub/Jira/Linear.
  - [ ] 9.5 Implementar transicao de status apenas quando suportada e confirmada.

- [ ] 10.0 Validacao, release e documentacao
  - [ ] 10.1 Atualizar docs de release e manual sem hand-edit de artefatos gerados indevidos.
  - [ ] 10.2 Rodar `validate.sh`, `smoke-test.sh`, `dogfood-report.sh`.
  - [ ] 10.3 Rodar testes E2E Playwright.
  - [ ] 10.4 Verificar release bundle com API/frontend quando entrarem no pacote.
  - [ ] 10.5 Documentar claramente que plugin Claude Code permanece o nucleo.
