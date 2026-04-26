• Estamos em /home/alex/claude-tech-squad, branch main, working tree limpo.

  Últimos commits relevantes:

  - 8fca9db feat(plugin): evolve ticket planning sdk and console docs
  - 0a2adfc chore: prepare release v5.54.0
  - 70015d9 docs: update ticket sdk and console documentation

  Estado atual validado:

  bash scripts/validate.sh

  Resultado:

  claude-tech-squad validation passed (v5.54.0, 79 agents)

  Estado Geral

  O plugin está em v5.54.0.

  Implementado e versionado:

  - Fase 0: baseline do plugin, runtime policy, contracts e validações.
  - Fase 1: golden runs live canônicos.
  - Fase 2: onboarding e templates CLAUDE.md.
  - Fase 3: dashboard Markdown/HTML baseado em SEP logs.
  - Fase 4: ticket planning vendor-neutral com adapters locais.
  - Fase 5: SDK Python v1 mínimo e exemplos.
  - Planejamento futuro: Console/Frontend próprio e observabilidade.

  Fase 1

  Fechada no contrato atual.

  Golden runs live versionados:

  - ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z
  - ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z
  - ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z
  - ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z
  - ai-docs/dogfood-runs/rollover-midimplement/2026-04-22T17-10-00Z

  Cada run tem:

  - prompt.txt
  - trace.md
  - final.md
  - metadata.yaml
  - scorecard.md

  O cenário rollover-midimplement também tem:

  - rollover-brief.md
  - rollover-state.json

  Observação importante: a evidência validada é majoritariamente execution_mode: inline. Evidência tmux pane-level completa continua desejável, mas não bloqueia o contrato atual.

  Fase 2

  Onboarding implementado.

  Arquivos principais:

  - plugins/claude-tech-squad/bin/squad_cli/onboarding.py
  - plugins/claude-tech-squad/skills/onboarding/catalog.json
  - plugins/claude-tech-squad/skills/onboarding/SKILL.md
  - templates/claude-md/base.md
  - templates/claude-md/ai-llm-section.md
  - templates/claude-md/stacks/*

  Comando:

  python3 plugins/claude-tech-squad/bin/squad-cli onboarding-plan --project-root .

  Função prática:

  - detecta stack;
  - detecta feature AI/LLM;
  - escolhe template CLAUDE.md;
  - sugere especialistas;
  - sugere checks de saúde.

  Fase 3

  Dashboard implementado.

  Arquivos principais:

  - plugins/claude-tech-squad/bin/squad_cli/dashboard.py
  - plugins/claude-tech-squad/skills/dashboard/SKILL.md

  Comando:

  python3 plugins/claude-tech-squad/bin/squad-cli dashboard

  Gera:

  - ai-docs/dashboard-snapshot.md
  - ai-docs/dashboard.html

  Função prática:

  - lê SEP logs;
  - calcula saúde por skill;
  - mostra taxa de sucesso;
  - lista runs recentes;
  - detecta hotfixes aguardando postmortem;
  - gera Markdown e HTML.

  Fase 4

  Ticket planning evoluído.

  Antes era apenas contrato local. Agora tem camada estruturada com adapters locais.

  Arquivos principais:

  - plugins/claude-tech-squad/bin/squad_cli/ticket.py
  - plugins/claude-tech-squad/bin/squad_cli/ticket_sources/__init__.py
  - plugins/claude-tech-squad/bin/squad_cli/ticket_sources/base.py
  - plugins/claude-tech-squad/bin/squad_cli/ticket_sources/jira.py
  - plugins/claude-tech-squad/bin/squad_cli/ticket_sources/linear.py
  - plugins/claude-tech-squad/bin/squad_cli/ticket_sources/github.py
  - plugins/claude-tech-squad/bin/squad_cli/ticket_sources/pasted.py
  - plugins/claude-tech-squad/skills/from-ticket/SKILL.md

  Comandos:

  python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan PROJ-123
  python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan LIN-123 --ticket-json ticket.json
  python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan --ticket-json tickets.json --write-sep-log

  Suporta:

  - Jira key, como PROJ-123;
  - Linear id, como LIN-123;
  - GitHub issue, como #42 ou owner/repo#42;
  - JQL/texto colado;
  - JSON normalizado;
  - JSON capturado de Jira/Linear/GitHub;
  - batch quando ticket_json contém lista;
  - escrita opcional de SEP log de planejamento.

  Produz:

  - source;
  - ticket id;
  - tipo;
  - prioridade;
  - complexidade;
  - skill recomendada;
  - estimativa de agents/tokens/custo;
  - alternativas;
  - contexto pronto para skill downstream;
  - SEP log opcional.

  Importante: ainda não chama APIs reais de Jira/Linear/GitHub. Os adapters normalizam payloads capturados por MCP/API externa ou JSON local. Integração live ainda é trabalho futuro.

  Fase 5

  SDK Python v1 mínimo implementado.

  Arquivos principais:

  - plugins/claude-tech-squad/bin/squad_cli/sdk.py
  - docs/SDK.md
  - scripts/test-sdk.sh
  - examples/sdk_ticket_plan.py
  - examples/sdk_dashboard_report.py
  - examples/sdk_onboarding_plan.py

  API atual:

  from squad_cli.sdk import create_client

  client = create_client(
      project_root=".",
      plugin_root="plugins/claude-tech-squad",
  )

  client.onboarding_plan()
  client.dashboard_report()
  client.ticket_plan("PROJ-123")
  client.ticket_plan_from_context(context)

  Adicionado:

  - SDK_API_VERSION = "1.0"
  - SquadSDKError
  - TicketSourceError
  - CatalogError
  - ReportParseError
  - .to_json() determinístico nos modelos públicos;
  - helper to_json(model);
  - exemplos executáveis;
  - testes SDK em scripts/test-sdk.sh;
  - exemplos incluídos no release bundle.

  Função prática:

  - scripts externos conseguem usar os mesmos contratos do plugin;
  - futuros bots/API/frontend podem chamar SDK sem duplicar regra de negócio;
  - SDK não lança agents;
  - SDK não chama APIs externas diretamente;
  - SDK trabalha sobre contratos determinísticos.

  Documentação Atualizada

  Atualizado e versionado:

  - README.md
  - plugins/claude-tech-squad/README.md
  - docs/GETTING-STARTED.md
  - docs/SDK.md
  - CHANGELOG.md
  - ai-docs/resumo-tecnico.md

  Também foram criados artefatos de planejamento futuro:

  - ai-docs/claude-tech-squad-console/PRD.md
  - ai-docs/claude-tech-squad-console/TECHSPEC.md
  - ai-docs/claude-tech-squad-console/TASKS.md

  Esses documentos planejam:

  - frontend próprio;
  - API local;
  - indexador de SEP logs;
  - observability dashboard;
  - integrações live;
  - preservação do plugin Claude Code como núcleo.

  Console / Frontend Futuro

  Planejado, ainda não implementado.

  Objetivo: criar uma interface operacional sobre o plugin, sem substituir o Claude Code plugin.

  Arquitetura planejada:

  Claude Code Plugin
    ├─ skills
    ├─ agents
    ├─ runtime-policy
    ├─ squad-cli
    └─ SEP logs

  SDK Python
    └─ contratos determinísticos

  API local
    └─ chama SDK / squad-cli

  Frontend
    └─ mostra tickets, planos, runs e observabilidade

  Telas propostas para MVP:

  - Dashboard;
  - Ticket Planner;
  - Plan Detail;
  - Run History.

  A regra arquitetural é: frontend não decide skill, custo ou plano sozinho. Ele chama SDK/plugin.

  O Que Falta

  Prioridade 1: validação completa pós-release

  Rodar a escada completa em v5.54.0:

  bash scripts/validate.sh
  bash scripts/test-sdk.sh
  bash scripts/smoke-test.sh
  bash scripts/dogfood-report.sh
  bash scripts/verify-release.sh 5.54.0
  bash scripts/build-release-bundle.sh 5.54.0

  Até agora, depois do rebase para v5.54.0, foi confirmado:

  bash scripts/validate.sh

  Prioridade 2: Fase 4 integração real

  Implementar integração live, começando read-only:

  - GitHub Issues real;
  - Jira issue real;
  - Jira JQL real;
  - Linear real quando API/tool estiver disponível;
  - fallback formal quando credenciais/tools falharem;
  - golden run com ticket real/sandbox;
  - golden run de fallback sem credenciais.

  Depois:

  - comentário no ticket;
  - transição de status;
  - link para SEP log;
  - sempre com confirmação explícita.

  Prioridade 3: Fase 5 maturidade do SDK

  Evoluir de SDK mínimo para base estável:

  - schemas públicos versionados;
  - testes unitários formais;
  - erros com code, message, source;
  - documentação completa dos modelos;
  - validação de import a partir do release bundle;
  - política de compatibilidade semântica;
  - client config;
  - logging estruturado.

  Prioridade 4: Console/API/Observabilidade

  Implementar conforme PRD/TechSpec:

  - API local;
  - indexador SQLite de SEP logs;
  - frontend MVP;
  - filtros de runs;
  - eventos estruturados;
  - dashboard operacional;
  - Playwright E2E;
  - integrações read-only;
  - mutações externas com preview/confirm.

  Prioridade 5: tmux evidence

  A Fase 1 está fechada no contrato atual, mas ainda falta como melhoria:

  - capturar evidência tmux pane-level completa;
  - provar execução real de teammates em panes;
  - registrar artefatos com logs de orquestração multi-pane;
  - comparar inline vs teammate mode.

  Riscos Atuais

  O principal risco não é funcionalidade quebrada; é comunicação de maturidade.

  Fase 4:

  - Está pronta para planejamento local/adapters.
  - Ainda não é integração Jira/Linear/GitHub live completa.

  Fase 5:

  - Está pronta como SDK mínimo v1.
  - Ainda não é SDK público maduro com compatibilidade ampla, empacotamento isolado e testes formais extensos.

  Console:

  - Está planejado com PRD/TechSpec/TASKS.
  - Ainda não está implementado.

  Estado Final

  Resumo curto:

  - Plugin: operacional e validado em v5.54.0.
  - Fases 0-5: implementadas.
  - Fase 4: adapters locais e batch prontos; live APIs pendentes.
  - Fase 5: SDK v1 mínimo pronto; maturidade/empacotamento avançado pendente.
  - Docs: README, Getting Started, SDK docs, CHANGELOG e plano do Console atualizados.
  - Próximo grande bloco: integração live + API/frontend/observabilidade.