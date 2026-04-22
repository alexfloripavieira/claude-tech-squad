• Estamos no repositório /home/alex/claude-tech-squad, ainda em v5.52.0.

  Estado Atual

  Fases implementadas:

  - Fase 0
  - Fase 1 live golden runs validados
  - Fase 2 onboarding / CLAUDE.md
  - Fase 3 dashboard / visual reporting
  - Fase 4 ticket planning Jira/Linear/GitHub
  - Fase 5 SDK Python mínimo

  Validações executadas e passando:

  bash scripts/validate.sh
  bash scripts/smoke-test.sh
  bash scripts/dogfood-report.sh

  Resultados relevantes:

  claude-tech-squad validation passed (v5.52.0, 79 agents)
  claude-tech-squad dogfood fixtures passed
  claude-tech-squad golden run schema passed
  claude-tech-squad smoke test passed
  claude-tech-squad golden runs passed

  Fase 1

  Fase 1 live está fechada para os 5 cenários principais:

  - layered-monolith: ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z
  - hexagonal-billing: ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z
  - hotfix-checkout: ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z
  - llm-rag: ai-docs/dogfood-runs/llm-rag/2026-04-22T16-33-43Z
  - rollover-midimplement: ai-docs/dogfood-runs/rollover-midimplement/2026-04-22T17-10-00Z

  Os artefatos validam com dogfood-report.sh e smoke-test.sh.

  Evidência confirmada:

  - gates e checkpoints registrados nos traces;
  - SEP logs reais em ai-docs/.squad-log/;
  - traces reais;
  - finais reais com result_contract;
  - metadata com execution_mode;
  - no rollover, rollover-brief.md e rollover-state.json dentro da pasta timestampada;
  - schema SEP: 7 logs validados OK.

  Observação: a evidência live validada é majoritariamente execution_mode inline. O cenário hexagonal-billing registra discovery com teammate orchestration e implementação inline; tmux pane-level completo continua sendo uma evidência adicional possível, mas não bloqueia mais o fechamento da Fase 1 conforme o contrato atual.

  Fase 2

  Implementada: onboarding com catálogo e templates CLAUDE.md.

  Arquivos principais:

  - templates/claude-md/base.md
  - templates/claude-md/ai-llm-section.md
  - templates/claude-md/stacks/*
  - plugins/claude-tech-squad/skills/onboarding/catalog.json
  - plugins/claude-tech-squad/bin/squad_cli/onboarding.py

  Comando:

  python3 plugins/claude-tech-squad/bin/squad-cli onboarding-plan --project-root .

  Detecta stack, template, especialistas, health checks e ai_feature.

  Fase 3

  Implementada: dashboard aggregation + HTML report.

  Arquivos principais:

  - plugins/claude-tech-squad/bin/squad_cli/dashboard.py
  - plugins/claude-tech-squad/skills/dashboard/SKILL.md
  - plugins/claude-tech-squad/bin/squad_cli/cli.py

  Comando:

  python3 plugins/claude-tech-squad/bin/squad-cli dashboard

  Gera:

  - ai-docs/dashboard-snapshot.md
  - ai-docs/dashboard.html
  - SEP log do dashboard em ai-docs/.squad-log/, salvo quando não usado --no-write-sep-log

  O smoke test cobre logs SEP sintéticos, Markdown e HTML.

  Fase 4

  Implementada em primeiro corte local/contractual: ticket planning vendor-neutral.

  Arquivos principais:

  - plugins/claude-tech-squad/bin/squad_cli/ticket.py
  - plugins/claude-tech-squad/skills/from-ticket/SKILL.md
  - plugins/claude-tech-squad/bin/squad_cli/cli.py

  Novo comando:

  python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan PROJ-123
  python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan LIN-123 --ticket-json ticket.json

  Suporta detecção/normalização de:

  - Jira: PROJ-123
  - Linear: LIN-123
  - GitHub Issue: #42 ou owner/repo#42
  - JQL entre aspas
  - texto colado

  Produz:

  - source;
  - ticket id;
  - tipo;
  - prioridade;
  - complexidade;
  - skill recomendada;
  - estimativa de agentes/tokens/custo;
  - alternativas;
  - launch_context para skills downstream.

  Ainda não é integração live com Jira/Linear/GitHub APIs. O helper assume que a captura externa real será feita por MCP ou por outro consumidor que injete JSON normalizado.

  Fase 5

  Implementada em primeiro corte: SDK Python mínimo.

  Arquivos principais:

  - plugins/claude-tech-squad/bin/squad_cli/sdk.py
  - docs/SDK.md
  - plugins/claude-tech-squad/bin/squad_cli/cli.py

  Novo comando de verificação:

  python3 plugins/claude-tech-squad/bin/squad-cli sdk-smoke \
    --project-root fixtures/dogfooding/llm-rag \
    --plugin-root plugins/claude-tech-squad

  API exposta:

  from squad_cli.sdk import create_client

  client = create_client(project_root=".", plugin_root="plugins/claude-tech-squad")
  client.onboarding_plan()
  client.dashboard_report()
  client.ticket_plan("PROJ-123")

  O SDK não lança agentes e não chama APIs externas. Ele encapsula os contratos determinísticos existentes.

  Validações Adicionadas

  validate.sh agora cobre:

  - catálogo de onboarding;
  - templates CLAUDE.md;
  - módulo dashboard.py;
  - módulo ticket.py;
  - módulo sdk.py;
  - comando dashboard;
  - comando ticket-plan;
  - comando sdk-smoke;
  - skill from-ticket.

  smoke-test.sh agora cobre:

  - onboarding-plan;
  - dashboard;
  - ticket-plan com fixture Linear/LLM;
  - sdk-smoke;
  - golden run scaffold;
  - release bundle;
  - release metadata;
  - render scripts;
  - contratos de agentes/skills.

  Working Tree

  Há mudanças acumuladas de várias fases, incluindo arquivos modificados e não rastreados. Importante: parte disso já existia antes das últimas alterações, conforme o resumo anterior.

  Mudanças recentes desta etapa:

  - plugins/claude-tech-squad/bin/squad_cli/ticket.py
  - plugins/claude-tech-squad/bin/squad_cli/sdk.py
  - plugins/claude-tech-squad/bin/squad_cli/cli.py
  - plugins/claude-tech-squad/skills/from-ticket/SKILL.md
  - scripts/validate.sh
  - scripts/smoke-test.sh
  - docs/SDK.md
  - README.md
  - docs/GETTING-STARTED.md
  - ai-docs/resumo-tecnico.md

  Também continuam presentes mudanças/untracked de fases anteriores, como:

  - templates/claude-md/**
  - plugins/claude-tech-squad/bin/squad_cli/onboarding.py
  - plugins/claude-tech-squad/bin/squad_cli/dashboard.py
  - plugins/claude-tech-squad/skills/onboarding/catalog.json
  - ai-docs/dogfood-runs/**
  - ai-docs/benchmarks/**
  - ai-docs/keel-handoff/**

  O Que Falta

  Prioridade 1: consolidar docs de release.

  Deixar explícito antes de qualquer release intermediária:

  - Fase 1 agora tem evidência live inline validada para os cinco cenários;
  - tmux pane-level completo é evidência adicional desejável, não requisito pendente do contrato atual;
  - Fases 4/5 são contratos locais, não integrações externas live completas.

  Prioridade 2: evoluir Fase 4 para integração externa real.

  Próximos passos prováveis:

  - conectar ticket-plan ao fluxo MCP real de Jira/Linear/GitHub;
  - validar campos reais retornados pelas ferramentas;
  - registrar SEP logs reais de /from-ticket;
  - testar fallback quando MCP não está disponível;
  - cobrir updates pós-execução, como comentário/status no ticket.

  Prioridade 3: evoluir Fase 5 para SDK mais formal.

  Possíveis próximos passos:

  - estabilizar versionamento do SDK;
  - definir contrato público em docs;
  - adicionar exemplos executáveis;
  - adicionar testes unitários dedicados, se o repo passar a aceitar suíte Python;
  - expor modelos de erro;
  - empacotar como parte do release bundle se for objetivo publicar.

  Risco Principal

  O maior risco continua sendo interpretar os golden runs atuais como prova live completa. Eles provam contrato, estrutura e baseline validada, mas ainda não provam execução real de teammate/
  tmux, gates interativos e SEP logs live de ponta a ponta.


› faça um plano da evolução da fase 4 e 5


• Plano Fase 4

  Objetivo: transformar o ticket-plan atual de contrato local em integração operacional real com Jira, Linear e GitHub Issues.

  1. Congelar o contrato atual
      - Manter TicketContext, TicketPlan e launch_context como contrato base.
      - Documentar campos obrigatórios, opcionais e defaults.
      - Adicionar exemplos JSON para Jira, Linear e GitHub em scripts/test-fixtures/.
  2. Adicionar adapters por fonte
      - Criar camada ticket_sources/ ou equivalente:
          - jira.py
          - linear.py
          - github.py
          - pasted.py
      - Cada adapter deve converter a resposta externa para TicketContext.
      - Nenhum adapter deve decidir skill; decisão continua centralizada em ticket.py.
  3. Integrar com MCP/tools reais
      - Jira: ler issue por key e buscar filhos de Epic.
      - Linear: ler issue por identifier.
      - GitHub: ler issue por owner/repo#number.
      - Quando a ferramenta não existir ou falhar, cair para fallback de texto colado sem bloquear.
  4. Suportar batch/JQL
      - Para JQL ou listas de tickets, retornar múltiplos TicketPlan.
      - Classificar cada item e sugerir ordem de execução.
      - Para Epic ou sprint, agrupar por skill recomendada.
  5. Publicação pós-execução
      - Após uma skill rodar, permitir update opcional:
          - comentário com resumo;
          - link para SEP log;
          - status sugerido;
          - subtasks criadas quando aplicável.
      - Updates sempre exigem confirmação explícita.
  6. Observabilidade
      - /from-ticket deve escrever SEP log real com:
          - ticket_source
          - ticket_id
          - recommended_skill
          - skill_launched
          - ticket_updated
          - fallback usado ou não
      - Dashboard deve conseguir agrupar execuções por origem de ticket futuramente.
  7. Validação
      - Smoke com fixtures offline.
      - Golden run live com pelo menos:
          - 1 Jira ticket real ou sandbox;
          - 1 GitHub Issue real/local;
          - 1 fallback sem credenciais.
      - Documentar explicitamente o que é fixture e o que é live.

  Plano Fase 5

  Objetivo: transformar o SDK mínimo em uma API estável para automações externas e release bundle.

  1. Definir API pública v1
      - Congelar:
          - create_client()
          - onboarding_plan()
          - dashboard_report()
          - ticket_plan()
      - Separar classes internas de modelos públicos.
      - Documentar compatibilidade semântica.
  2. Adicionar modelos de erro
      - Criar exceções específicas:
          - SquadSDKError
          - TicketSourceError
          - CatalogError
          - ReportParseError
      - Evitar que consumidores tenham que tratar exceções genéricas de json, Path ou parser.
  3. Adicionar serialização estável
      - Todos os retornos públicos devem ter:
          - .to_dict()
          - .to_json()
      - Garantir JSON determinístico para automações e CI.
  4. Criar exemplos executáveis
      - examples/sdk_ticket_plan.py
      - examples/sdk_dashboard_report.py
      - examples/sdk_onboarding_plan.py
      - Rodar esses exemplos no smoke test ou em validação dedicada.
  5. Adicionar testes unitários
      - Testar:
          - detecção de fontes;
          - normalização de tickets;
          - recomendação de skill;
          - SDK facade;
          - erros previsíveis.
      - Se o repo continuar sem suíte Python formal, criar script shell scripts/test-sdk.sh.
  6. Empacotamento
      - Garantir que sdk.py, ticket.py, exemplos e docs entram no release bundle.
      - Verificar import via:

        PYTHONPATH=plugins/claude-tech-squad/bin python3 -c "from squad_cli.sdk import create_client"
  7. Integração com Fase 4
      - O SDK deve conseguir receber adapters externos:

        client.ticket_plan_from_context(context)
      - Isso permite que qualquer integração MCP/API use o SDK sem depender do CLI.
  8. Critério de pronto
      - validate.sh passa.
      - smoke-test.sh passa.
      - Exemplos SDK passam.
      - Docs deixam claro:
          - SDK não lança agentes;
          - SDK não chama APIs externas diretamente;
          - SDK trabalha sobre contratos determinísticos;
          - integrações live ficam nos adapters/Fase 4.

  Sequência Recomendada

  1. Primeiro estabilizar contratos e fixtures da Fase 4.
  2. Depois criar API pública/erros da Fase 5.
  3. Em seguida adicionar adapters externos da Fase 4.
  4. Só então fazer golden runs live com tickets reais.
  5. Por fim, atualizar docs de release e preparar bundle.
