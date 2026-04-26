# Product Vision: Claude Tech Squad

## Resumo

O Claude Tech Squad esta evoluindo de um plugin com agentes especializados para uma plataforma operacional de entrega de software assistida por IA.

O plugin Claude Code continua sendo o nucleo: agents, skills, runtime policy, `squad-cli`, SDK, SEP logs, golden runs e validacoes. Em volta dele, o produto pode evoluir para um Console, API local, integracoes com tickets e uma camada de observabilidade para execucoes com agentes.

Em uma frase:

> Um sistema operacional de entrega de software com agentes especializados, governanca, observabilidade e execucao rastreavel, rodando primeiro dentro do Claude Code e evoluindo para uma plataforma de AgentOps para engenharia.

## O Que Temos Hoje

Hoje o produto e principalmente um plugin Claude Code instalavel:

- specialist agents;
- skills de delivery;
- runtime policy;
- guardrails;
- SEP logs;
- golden runs;
- `squad-cli`;
- onboarding;
- dashboard local;
- ticket planning;
- SDK Python minimo.

O valor atual esta em coordenar trabalho de engenharia dentro do Claude Code com papeis claros, contratos, validacao mecanica e evidencias persistentes.

## O Produto Que Esta Emergindo

O produto pode virar um cockpit operacional para times de engenharia.

Ele recebe entradas reais:

- tickets;
- PRDs;
- techspecs;
- incidentes;
- bugs;
- PRs;
- contexto de repositorio;
- SEP logs;
- historico de execucoes.

E produz saidas operacionais:

- plano recomendado;
- skill recomendada;
- contexto de launch;
- estimativa de custo/tokens/agentes;
- implementacao coordenada;
- revisao;
- release plan;
- postmortem;
- comentario ou atualizacao de ticket;
- SEP log auditavel.

O produto deixa de ser apenas "um conjunto de prompts/agentes" e passa a ser uma camada de operacao de engenharia com IA.

## Camadas Do Produto

### 1. Claude Code Plugin

Nucleo de execucao.

Responsabilidades:

- agents;
- skills;
- runtime policy;
- hooks;
- guardrails;
- golden runs;
- SEP logs;
- contratos de resultado.

O plugin deve continuar funcionando sozinho, sem frontend, API ou servicos externos.

### 2. squad-cli

Camada deterministica local.

Responsabilidades:

- preflight;
- health checks;
- checkpoint/resume;
- cost;
- SEP log;
- onboarding plan;
- dashboard;
- ticket plan;
- SDK smoke.

O objetivo do `squad-cli` e tirar tarefas mecanicas do LLM e manter contratos reproduziveis.

### 3. SDK Python

Ponte programatica para automacoes.

Responsabilidades:

- expor contratos publicos;
- permitir scripts/bots/APIs usarem ticket planning, dashboard e onboarding;
- oferecer erros especificos;
- serializacao deterministica;
- receber contextos externos sem duplicar regra de negocio.

O SDK nao deve lancar agents nem chamar APIs externas diretamente no primeiro momento. Ele e a camada de contrato para consumidores externos.

### 4. Console / Frontend

Interface operacional futura.

Responsabilidades:

- ticket planner visual;
- dashboard de runs;
- historico de SEP logs;
- detalhes de plano;
- filtros;
- confirmacoes humanas;
- visualizacao de custo, risco e status.

O frontend nao deve decidir skill, custo ou plano. Ele deve chamar API/SDK/plugin.

### 5. Integracoes

Camada de conexao com ferramentas reais.

Possiveis fontes:

- GitHub Issues;
- Jira;
- Linear;
- GitHub PRs;
- CI/CD;
- Slack/Teams;
- observability stacks.

As integracoes devem comecar em modo read-only. Mutacoes externas exigem preview, confirmacao explicita e log auditavel.

## Posicionamento

Possivel categoria:

> AI Delivery Operations Platform

Ou:

> AgentOps for Software Delivery

O diferencial nao e apenas "usar agentes". O diferencial e juntar:

- agentes especializados;
- contratos explicitos;
- validacao mecanica;
- SEP logs;
- golden runs;
- runtime policy;
- fallback;
- custo;
- auditoria;
- integracao com tickets;
- SDK;
- futuro console operacional.

Isso posiciona o produto como algo mais serio que um wrapper de prompts.

## Casos De Uso

### Delivery Copilot Para Times

Fluxo:

```text
Ticket -> plano -> skill recomendada -> execucao -> PR -> SEP log -> comentario no ticket
```

Exemplos:

- "Pegue PROJ-123 e diga se e `/hotfix`, `/bug-fix`, `/implement` ou `/discovery`."
- "Classifique todos os tickets High da sprint atual."
- "Agrupe tickets por skill recomendada e custo estimado."
- "Rode discovery para esse epic e gere plano de implementacao."

### Governanca De IA Em Engenharia

O produto pode provar:

- quem pediu;
- qual ticket originou o trabalho;
- qual skill rodou;
- quais agents participaram;
- quais gates bloquearam;
- quais fallbacks ocorreram;
- quanto custou;
- quais decisoes foram tomadas;
- quais artefatos foram gerados;
- qual SEP log registra a execucao.

Isso e importante para empresas que querem usar IA em engenharia sem perder controle.

### Observability Para Agentes

O produto pode responder:

- quais skills falham mais;
- quais agentes geram mais retrabalho;
- quanto custa cada tipo de execucao;
- quais tickets viram hotfix;
- quais hotfixes nao tiveram postmortem;
- quais gates bloqueiam com frequencia;
- quando fallback e acionado;
- como versoes do plugin afetam taxa de sucesso.

Essa camada pode virar um produto proprio de AgentOps.

### Engineering OS Com IA

Entradas:

- backlog;
- tickets;
- PRDs;
- incidentes;
- PRs;
- metricas;
- logs;
- docs.

Saidas:

- planos;
- techspecs;
- tasks;
- codigo;
- testes;
- reviews;
- postmortems;
- release plans;
- dashboards.

## Evolucao Por Versoes

### V1: Plugin Profissional

Estado atual/curto prazo.

Inclui:

- plugin instalavel;
- agents;
- skills;
- `squad-cli`;
- SDK basico;
- docs;
- golden runs;
- release bundle.

Objetivo:

- ser confiavel dentro do Claude Code.

### V2: Local Console

Inclui:

- frontend local;
- API local;
- dashboard;
- ticket planner;
- run history;
- SEP log browser.

Objetivo:

- dar interface operacional para individuos e times pequenos.

### V3: Team Console

Inclui:

- multiusuario;
- autenticacao;
- GitHub/Jira/Linear live;
- comentarios em tickets;
- PR integration;
- CI integration;
- RBAC;
- audit log.

Objetivo:

- operar em times reais.

### V4: AgentOps Platform

Inclui:

- metricas historicas;
- custo por skill/projeto/time;
- qualidade por fluxo;
- benchmark entre versoes do plugin;
- deteccao de regressao de agentes;
- alertas;
- comparacao inline vs tmux;
- golden runs automaticos.

Objetivo:

- gerir confiabilidade, custo e qualidade da IA em engenharia.

### V5: Autonomous Delivery Control Plane

Visao mais ambiciosa.

Inclui:

- ler backlog;
- propor plano semanal;
- agrupar tickets;
- identificar dependencias;
- estimar custo;
- recomendar ordem;
- abrir PRs;
- pedir revisao humana;
- atualizar tickets;
- gerar release.

Objetivo:

- ser o control plane de execucao de software com humanos nos gates importantes.

## Principios De Produto

1. Plugin primeiro
   - O Claude Code plugin continua sendo o nucleo.

2. Contratos antes de UI
   - Frontend e API consomem contratos existentes, nao criam logica paralela.

3. Observabilidade como feature central
   - Toda execucao importante deve gerar evidencia.

4. Read-only antes de mutacao
   - Integracoes externas devem comecar lendo dados.

5. Confirmacao explicita para efeitos externos
   - Comentarios, status e transicoes de ticket exigem confirmacao humana.

6. Auditoria sempre
   - SEP logs e eventos estruturados devem registrar o que aconteceu.

7. Custo visivel
   - Estimativa e medicao de tokens/custo fazem parte do produto.

8. Golden runs como benchmark
   - Qualidade do produto deve ser provada por cenarios reais e repetiveis.

## Roadmap Recomendado

1. Consolidar plugin como produto instalavel.
2. Fechar integracao real GitHub Issues read-only.
3. Fechar integracao real Jira read-only.
4. Criar Console local.
5. Criar observabilidade historica.
6. Adicionar atualizacao de tickets/PRs com confirmacao.
7. Criar modo team/multiusuario.
8. Transformar golden runs em benchmark continuo.
9. Evoluir para plataforma de AI Delivery Ops.

## Riscos

### Produto virar apenas UI

Mitigacao:

- manter plugin/SDK como fonte de verdade;
- frontend apenas visualiza e confirma.

### Prometer integracao live antes da maturidade

Mitigacao:

- documentar claramente o que e local, read-only, live e mutavel.

### Autonomia excessiva cedo demais

Mitigacao:

- manter confirmacao humana para mutacoes externas e gates importantes.

### Falta de prova operacional

Mitigacao:

- golden runs live e benchmarks continuos.

### Duplicacao de regras

Mitigacao:

- todas as recomendacoes de skill/custo/complexidade ficam em `squad-cli`/SDK/plugin.

## Norte Estrategico

O Claude Tech Squad pode chegar a ser uma plataforma de operacao de engenharia com IA, mas o caminho mais forte e incremental:

1. Claude Code plugin confiavel.
2. SDK e CLI como contratos.
3. Console local para operacao.
4. Integracoes reais.
5. Observabilidade e governanca.
6. AgentOps para engenharia.
7. Control plane de delivery assistido por IA.

O ponto central: o produto nao precisa abandonar Claude Code. Ele pode vencer justamente por usar Claude Code como runtime poderoso e adicionar as camadas que times e empresas precisam para confiar: contrato, controle, custo, observabilidade e evidencia.
