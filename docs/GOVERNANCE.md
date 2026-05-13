# Governance

Este documento mapeia a governança automática existente no `claude-tech-squad`.
O ponto de entrada operacional é `squad-cli run ...`, que registra o ciclo de
vida da execução e coordena a evidência. Ele não substitui a fonte de verdade:
`plugins/claude-tech-squad/runtime-policy.yaml`, os hooks em
`plugins/claude-tech-squad/hooks/`, os helpers em `plugins/claude-tech-squad/bin/`
e os contratos embutidos nos `SKILL.md` continuam sendo os mecanismos de baixo
nível.

## Princípio Operacional

A governança deve ser mecânica sempre que possível:

- hooks bloqueiam ações perigosas;
- `squad-cli run` registra start, eventos, gates, checkpoints, spawns,
  conclusão de agentes, finish e relatório;
- helpers criam branches, worktrees, cleanup e finalização;
- watchdogs encerram agentes travados;
- SEP logs registram evidência;
- `scripts/validate.sh` garante que os contratos estão conectados.

O prompt ainda descreve o comportamento esperado, mas não é a única barreira de
segurança.

## Runtime `squad-cli run`

O runtime de governança automática vive em
`plugins/claude-tech-squad/bin/squad_cli/run_lifecycle.py` e é exposto pelo grupo
`squad-cli run`:

- `squad-cli run start --skill <skill> --task <tarefa>` cria o `run_id`,
  executa `detect-team-mode.sh`, registra `execution_mode`, aplica
  `language_policy_applied: pt-BR`, persiste o estado e emite os helpers que
  devem ser usados pela execução.
- `squad-cli run mode` diagnostica o modo atual (`inline` ou `teammate`) e
  explica o motivo com checks de tmux, sessão, envs e versão do Claude Code.
- `squad-cli run event --run-id <id> --type <tipo> --value <valor>` registra
  comandos, decisões e evidências operacionais.
- `squad-cli run gate --run-id <id> --name <gate> --status <status>` registra
  gates passados ou bloqueados com razão.
- `squad-cli run checkpoint --run-id <id> --step <fase>` registra fases e
  artefatos associados.
- `squad-cli run spawn --run-id <id> --agent <nome> ...` registra agente,
  subagent type, worktree, branch, base commit e peers. A resposta inclui um
  `spawn_prompt` pronto para usar no primeiro bloco do Agent, com pt-BR,
  worktree, cross-talk, SEP e orientações específicas do papel.
- `squad-cli run agent-done --run-id <id> --agent <nome> ...` fecha a
  participação do agente com status, confiança, tokens, merge e commits
  pendentes.
- `squad-cli run finish --run-id <id> --status <status>` finaliza o estado,
  escreve SEP log com `schema_version`, `worktrees`, `cts_phases_completed` e
  `language_policy_applied: pt-BR`, e valida automaticamente o SEP log com
  `validate-sep-log.py`.
- `squad-cli run report --run-id <id>` retorna um resumo JSON auditável.

O estado fica em `<state-dir>/<run_id>.run.json`. O SEP log fica no diretório
passado por `--log-dir`, por padrão `ai-docs/.squad-log`, com nome canônico
`YYYYMMDDTHHMMSSZ-<skill>-<run_id>.md`. O timestamp vem do `run start`, então
`run finish` é idempotente: chamadas repetidas atualizam o mesmo arquivo em vez
de criar duplicatas.

## Safety Gates

O hook `plugins/claude-tech-squad/hooks/pre-tool-guard.sh` é o bloqueio mecânico
para comandos destrutivos executados via Bash.

Ele bloqueia, entre outros:

- SQL destrutivo como `DROP` e `TRUNCATE`;
- `git push --force`;
- push direto para branches protegidas;
- `git commit --no-verify`;
- `terraform destroy`, `pulumi destroy` e `cdk destroy`;
- remoção de aplicações como `heroku apps:destroy` e `tsuru app-remove`;
- `rm -rf /`;
- `eval` com expansão variável;
- acesso direto a banco de produção.

Esses bloqueios existem para reduzir dependência de obediência textual dos
agentes. Quando uma ação perigosa for realmente necessária, ela deve ser
transformada em gate explícito para o operador, com rollback, evidência e razão.

## Resolução De Modo

O helper `plugins/claude-tech-squad/bin/detect-team-mode.sh` resolve o modo de
execução antes de `TeamCreate`:

- `mode=teammate`: tmux está disponível, Claude Code já foi iniciado dentro de
  tmux, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` e
  `CLAUDE_CODE_TEAMMATE_MODE=tmux` estão ativos, e a versão do Claude Code
  atende ao mínimo configurado.
- `mode=inline`: algum pré-requisito está ausente ou o usuário não optou por
  teammate mode.

O modo `inline` é o padrão. O modo `teammate` é opt-in para visibilidade,
panes separados e cross-talk bloqueante. Em `inline`, o workflow continua, mas a
fiscalização de cross-talk é rebaixada para warning conforme
`runtime-policy.yaml::agent_teams.cross_talk_protocol.enforcement_by_mode`.

O hook `plugins/claude-tech-squad/hooks/dev-flow-tmux-gate.sh` já não
interrompe a execução com uma escolha manual. Ele apenas deixa o prompt
seguir; a resolução real de `teammate` versus `inline` acontece no preflight
via `bin/detect-team-mode.sh`.

## Política De Idioma

`runtime-policy.yaml::language_policy` define pt-BR como requisito forte para
linguagem natural:

- mensagens entre teammates;
- campos narrativos de `result_contract`;
- relatórios do orquestrador;
- prompts de gate;
- campos narrativos de SEP log.

Permanecem em inglês por compatibilidade:

- código;
- comandos shell;
- caminhos de arquivo;
- identificadores;
- chaves YAML estruturadas;
- tags de log como `[Preflight Start]`;
- mensagens de commit e títulos/corpos de PR.

Todo spawn de `Agent(...)` deve receber o preâmbulo
`language_policy.spawn_prompt_preamble`, e todo SEP log deve registrar
`language_policy_applied: pt-BR`.

## Cross-Talk Entre Agentes

`runtime-policy.yaml::agent_teams.cross_talk_protocol` exige que skills de
dev-flow declarem `## Inter-Teammate Cross-Talk Protocol`.

O protocolo garante que teammates conversem diretamente entre si, não apenas
com o lead. Cada skill lista seus pares obrigatórios, por exemplo:

- TDD Specialist e desenvolvedor para handoff de teste;
- backend, frontend e test automation para contratos cross-layer;
- revisores de segurança, performance, privacidade e acessibilidade para
  revisão adversarial.

Antes de escrever o SEP log, o lead audita a mailbox. Par obrigatório sem
`SendMessage` vira `cross-talk-missing`:

- em `mode=teammate`, isso abre gate bloqueante;
- em `mode=inline`, isso vira warning e o pipeline continua.

Quando um agente precisa entregar arquivo a outro, o handoff acontece por git:
o emissor informa `from_branch`, `commit_sha` e `file_paths`; o receptor busca a
branch local e faz checkout dos arquivos dentro do próprio worktree.

## Advogado Do Diabo

O papel "advogado do diabo" é o nome operacional em pt-BR do padrão
`runtime-policy.yaml::agent_teams.cross_talk_protocol.patterns.adversarial_review`.
Ele não é um agente novo obrigatório nem uma segunda arquitetura de governança:
é uma especialização dos pares de revisão adversarial já declarados nos skills.

Quando um par estiver marcado como `adversarial_review`, os agentes devem trocar
mensagens diretas em português para desafiar:

- premissas técnicas e de produto;
- riscos ocultos;
- alternativas descartadas cedo demais;
- falta de evidência;
- trade-offs entre segurança, performance, privacidade, acessibilidade,
  manutenibilidade e corretude;
- severidade de achados antes da síntese final.

O objetivo é melhorar a decisão, não bloquear por preferência pessoal. Uma
objeção útil precisa trazer evidência, impacto e uma mitigação possível. Quando
ela muda escopo, severidade ou direção de implementação, o lead registra no SEP
log ou relatório:

- objeção levantada;
- resposta ou mitigação;
- decisão final;
- agente que aceitou ou rejeitou o ponto.

## Worktrees Por Agente

`runtime-policy.yaml::agent_worktrees` define isolamento por worktree para cada
spawn de agente.

O fluxo tem quatro fases:

1. `init-skill-branch.sh <skill>` cria a branch da skill no worktree principal.
2. `spawn-agent-worktree.sh <skill> <agent> <agent_id>` cria um worktree isolado
   por agente.
3. `cleanup-agent-worktree.sh <worktree_path>` mescla commits do agente de volta
   para a branch da skill usando `--no-ff`, remove o worktree e apaga a branch do
   agente quando possível.
4. `finalize-skill.sh <skill_branch>` garante que não sobraram worktrees,
   branches de agente ou estado efêmero antes de finalizar.

O hook `plugins/claude-tech-squad/hooks/skill-active-guard.sh` bloqueia edições
diretas no worktree principal enquanto uma skill está ativa. Mutação durante a
skill deve acontecer dentro do worktree do agente, exceto operações do lead
explicitamente permitidas.

## Watchdog E Timeouts

`plugins/claude-tech-squad/bin/watchdog.sh` é o daemon de proteção para runs
longas.

Ele lê marcadores em `ai-docs/.squad-log/.agents/*.spawned` e aplica limites:

- tempo máximo por agente;
- tempo máximo da skill inteira;
- limpeza best-effort do worktree quando um agente passa do limite;
- escrita de marcadores como `.killed` e `.skill-timed-out`.

O watchdog é backstop. O lead ainda precisa monitorar ativamente agentes, emitir
`[Teammate Timeout]` quando detectar stall e abrir gate quando houver falha
estrutural.

## Bypass Policy

`runtime-policy.yaml::failure_handling.bypass_policy` proíbe bypass silencioso de
revisores e papéis críticos.

Bypass de reviewer, QA, security reviewer, privacy reviewer, accessibility
reviewer, TDD specialist e test automation engineer exige gate explícito no chat.
Preferências de sessão como "sem perguntas" ou "modo autônomo" não autorizam
bypass. O evento precisa ser registrado em `bypasses_observed`.

`scripts/validate.sh` também possui lint de frases proibidas para evitar que
skills voltem a permitir bypass silencioso por texto.

## SEP Log E Schema

O SEP log é a trilha de auditoria de uma execução. Ele deve registrar campos como:

- `run_id`;
- `skill`;
- `status`;
- tokens e custo quando medidos;
- `worktrees`;
- `language_policy_applied`;
- fases CTS concluídas;
- timeouts e bypasses observados quando existirem.

`plugins/claude-tech-squad/bin/validate-sep-log.py` valida o frontmatter YAML dos
logs quando PyYAML está disponível. Falhas de schema emitem
`[SEP Schema Violation]`.

## Stale Skill Detection

`plugins/claude-tech-squad/hooks/stale-skill-detector.sh` roda em `SessionStart`.
Ele procura sentinel de skill ativa em `ai-docs/.squad-log/.active-skill` e avisa
quando uma execução anterior não finalizou limpidamente.

O hook não bloqueia, mas orienta recuperação via `finalize-skill.sh`, limpeza de
worktrees, prune e remoção de estado efêmero.

## Validação Estrutural

`scripts/validate.sh` garante que a governança está conectada. Entre outros
checks, ele valida:

- presença dos helpers de worktree;
- política de idioma pt-BR;
- protocolo de cross-talk nos skills aplicáveis;
- modo inline como padrão e tmux como display opt-in;
- fallback inline declarado;
- hook `dev-flow-tmux-gate.sh` registrado;
- phase tags CTS nos dev-flow skills;
- keywords de watchdog, timeout e bypass;
- tool allowlists e contratos de agentes.

## Responsabilidades Do Orquestrador

O lead/orquestrador deve operar pelo `squad-cli run`:

- iniciar a execução com `run start`;
- registrar comandos relevantes com `run event`;
- registrar gates explícitos com `run gate`;
- registrar fases com `run checkpoint`;
- registrar worktrees por agente com `run spawn`;
- fechar cada agente com `run agent-done`;
- finalizar com `run finish`;
- revisar o resumo com `run report`;
- comunicar gates e relatórios ao usuário em português.

## O Que Ainda Fica Para Evolução

Este documento descreve a governança existente e o runtime implementado. As
próximas evoluções são:

- reorganizar a superfície pública do plugin para destacar caminhos core e
  avançados;
- aprofundar, se necessário, a execução física dos helpers pelo CLI em vez de
  somente registrar os comandos e orientar a execução;
- atualizar fixtures e validações se novos contratos documentais forem
  promovidos a obrigatórios.
