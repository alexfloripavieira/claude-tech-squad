• Estamos em /home/alex/claude-tech-squad, branch main.

  Último commit já versionado e enviado para GitHub:

  642b661 feat(plugin): add onboarding dashboard ticket sdk and live evidence

  Working tree: limpo.

  Estado Atual

  O repositório continua em v5.52.0.

  Fases implementadas/versionadas:

  - Fase 0
  - Fase 1 live golden runs
  - Fase 2 onboarding / templates CLAUDE.md
  - Fase 3 dashboard / visual reporting
  - Fase 4 ticket planning vendor-neutral
  - Fase 5 SDK Python mínimo

  Validações finais antes do commit:

  bash scripts/dogfood-report.sh
  bash scripts/validate.sh
  bash scripts/smoke-test.sh

  Resultados:

  claude-tech-squad golden runs passed
  claude-tech-squad validation passed (v5.52.0, 79 agents)
  claude-tech-squad dogfood fixtures passed
  claude-tech-squad golden run schema passed
  claude-tech-squad smoke test passed

  Fase 1

  Fase 1 está fechada no contrato atual.

  Golden runs live canônicos versionados:

  ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z
  ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z
  ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z
  ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z
  ai-docs/dogfood-runs/rollover-midimplement/2026-04-22T17-10-00Z

  Cada cenário tem os artefatos exigidos:

  - prompt.txt
  - trace.md
  - final.md
  - metadata.yaml
  - scorecard.md

  O cenário rollover-midimplement também tem:

  - rollover-brief.md
  - rollover-state.json

  Ajustes feitos para fechar a Fase 1:

  - final.md dos runs live inclui result_contract;
  - metadata.yaml inclui score: pass;
  - dogfood-report.sh escolhe apenas diretórios timestampados 20*T*Z, evitando subpastas auxiliares;
  - artefatos duplicados/não timestampados foram removidos;
  - SEP logs crus ficaram fora do versionamento.

  Observação importante: a evidência live validada é majoritariamente execution_mode: inline. tmux pane-level completo continua desejável como evidência adicional, mas não está mais
  bloqueando a Fase 1 pelo contrato atual.

  Fase 2

  Implementada e versionada: onboarding com catálogo e templates CLAUDE.md.

  Arquivos principais:

  plugins/claude-tech-squad/bin/squad_cli/onboarding.py
  plugins/claude-tech-squad/skills/onboarding/catalog.json
  plugins/claude-tech-squad/skills/onboarding/SKILL.md
  templates/claude-md/base.md
  templates/claude-md/ai-llm-section.md
  templates/claude-md/stacks/*

  Comando:

  python3 plugins/claude-tech-squad/bin/squad-cli onboarding-plan --project-root .

  O smoke test cobre onboarding-plan usando fixtures/dogfooding/llm-rag.

  Fase 3

  Implementada e versionada: dashboard aggregation + HTML report.

  Arquivos principais:

  plugins/claude-tech-squad/bin/squad_cli/dashboard.py
  plugins/claude-tech-squad/skills/dashboard/SKILL.md
  plugins/claude-tech-squad/bin/squad_cli/cli.py

  Comando:

  python3 plugins/claude-tech-squad/bin/squad-cli dashboard

  Gera:

  ai-docs/dashboard-snapshot.md
  ai-docs/dashboard.html

  O smoke test cria SEP logs sintéticos e valida Markdown + HTML.

  Fase 4

  Implementada em primeiro corte: ticket planning vendor-neutral.

  Arquivos principais:

  plugins/claude-tech-squad/bin/squad_cli/ticket.py
  plugins/claude-tech-squad/skills/from-ticket/SKILL.md
  plugins/claude-tech-squad/bin/squad_cli/cli.py

  Comando:

  python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan PROJ-123
  python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan LIN-123 --ticket-json ticket.json

  Suporta:

  - Jira: PROJ-123
  - Linear: LIN-123
  - GitHub Issue: #42 ou owner/repo#42
  - JQL entre aspas
  - texto colado

  Produz:

  - origem;
  - ticket id;
  - tipo;
  - prioridade;
  - complexidade;
  - skill recomendada;
  - estimativa de agentes/tokens/custo;
  - alternativas;
  - launch_context.

  Ainda não chama APIs reais de Jira/Linear/GitHub. É um contrato determinístico para adapters/MCP futuros.

  Fase 5

  Implementada em primeiro corte: SDK Python mínimo.

  Arquivos principais:

  plugins/claude-tech-squad/bin/squad_cli/sdk.py
  docs/SDK.md
  plugins/claude-tech-squad/bin/squad_cli/cli.py

  Comando de verificação:

  python3 plugins/claude-tech-squad/bin/squad-cli sdk-smoke \
    --project-root fixtures/dogfooding/llm-rag \
    --plugin-root plugins/claude-tech-squad

  API atual:

  from squad_cli.sdk import create_client

  client = create_client(project_root=".", plugin_root="plugins/claude-tech-squad")
  client.onboarding_plan()
  client.dashboard_report()
  client.ticket_plan("PROJ-123")

  O SDK não lança agentes e não chama APIs externas. Ele encapsula contratos determinísticos.

  Limpeza Realizada

  Foram removidos/não versionados:

  - .squad-state/**
  - .codex
  - SEP logs crus em ai-docs/.squad-log/**
  - runs antigos/duplicados 2026-04-22T12-*
  - artefatos não timestampados de hexagonal-billing
  - ai-docs/hexagonal-billing/**
  - tasks/pending-implement-hexagonal-billing.md
  - implementação gerada dentro da fixture hexagonal-billing
  - caches .pytest_cache, .ruff_cache, __pycache__, .coverage
  - live-quick-prompts.md

  .gitignore foi atualizado para evitar retorno de estado local e cache.

  O Que Falta

  Prioridade 1: consolidar documentação de release.

  Atualizar docs de release para refletir o estado atual:

  - Fase 1 live está fechada com execução inline validada;
  - tmux completo é evidência adicional desejável, não bloqueio;
  - Fases 4/5 são contratos locais, não integrações externas live;
  - commit 642b661 contém a baseline atual.

  Prioridade 2: evoluir Fase 4 para integração real.

  Próximos passos:

  - criar adapters por fonte:
      - jira.py
      - linear.py
      - github.py
      - pasted.py
  - conectar adapters aos MCP/tools reais;
  - suportar JQL/batch;
  - escrever SEP log real de /from-ticket;
  - implementar fallback quando MCP não estiver disponível;
  - adicionar atualização opcional pós-execução: comentário, status, link para SEP log.

  Prioridade 3: evoluir Fase 5 para SDK estável.

  Próximos passos:

  - definir API pública v1;
  - adicionar exceções específicas;
  - adicionar .to_json() determinístico;
  - criar exemplos executáveis;
  - criar scripts/test-sdk.sh ou testes unitários;
  - garantir empacotamento no release bundle;
  - permitir ticket_plan_from_context(context) para integrações externas.

  Prioridade 4: release intermediária.

  Antes de release:

  bash scripts/validate.sh
  bash scripts/smoke-test.sh
  bash scripts/dogfood-report.sh
  bash scripts/verify-release.sh 5.52.0
  bash scripts/build-release-bundle.sh 5.52.0

  Depois revisar se o release deve continuar em v5.52.0 ou avançar versão, já que houve mudança funcional relevante.

  Risco Principal

  O principal risco agora não é mais Fase 1 pendente. O risco é comunicar demais: Fase 4 e Fase 5 ainda são contratos locais. Elas não devem ser descritas como integração Jira/Linear/
  GitHub live ou SDK público maduro até adapters reais, exemplos e testes dedicados existirem.

  Atualização desta etapa

  Fase 4 evoluída:

  - adapters locais criados para Jira, Linear, GitHub e pasted text em plugins/claude-tech-squad/bin/squad_cli/ticket_sources/;
  - ticket-plan agora aceita JSON batch e retorna múltiplos planos quando o ticket_json contém lista;
  - ticket-plan ganhou --write-sep-log e --log-dir para registrar planejamento /from-ticket em ai-docs/.squad-log/ ou diretório alternativo;
  - smoke-test cobre batch GitHub/Jira, recomendação por adapter e escrita de SEP log;
  - from-ticket/SKILL.md documenta adapters locais, batch/JQL e confirmação explícita para mutações externas.

  Fase 5 evoluída:

  - API pública SDK_API_VERSION = "1.0";
  - exceções específicas adicionadas: SquadSDKError, TicketSourceError, CatalogError, ReportParseError;
  - modelos públicos OnboardingPlan, DashboardReport, TicketContext e TicketPlan agora expõem to_json() determinístico;
  - SDK ganhou ticket_plan_from_context(context) para integrações externas;
  - exemplos executáveis adicionados em examples/;
  - scripts/test-sdk.sh criado e executado pelo smoke-test;
  - release bundle agora inclui examples/.

  Validações executadas nesta etapa:

  python3 -m py_compile plugins/claude-tech-squad/bin/squad_cli/*.py plugins/claude-tech-squad/bin/squad_cli/ticket_sources/*.py
  bash scripts/test-sdk.sh
  bash scripts/validate.sh
  bash scripts/smoke-test.sh

  Resultado:

  claude-tech-squad validation passed (v5.53.0, 79 agents)
  claude-tech-squad dogfood fixtures passed
  claude-tech-squad golden run schema passed
  claude-tech-squad smoke test passed
