# TechSpec — Reconciliar Execução, Governança e Comunicação em v5.70.0

## Resumo Executivo

A base `v5.70.0` já implementa Agent Teams mode-aware, pt-BR obrigatório, worktrees por agente, cross-talk, watchdogs e validações. A solução técnica atual é reconciliar textos e contratos que ainda falam como se tmux fosse obrigatório, sem enfraquecer os novos mecanismos.

O primeiro passo atualizou `CLAUDE.md`, `README.md` e os skills centrais (`discovery`, `implement`, `squad`) para declarar que teammate/tmux é preferido, mas inline fallback é válido quando resolvido por `detect-team-mode.sh`.

A terceira etapa implementa o runtime de governança automática em `squad-cli run ...`. Ele não substitui hooks e helpers existentes: ele cria uma camada auditável de ciclo de vida que registra start, eventos, gates, checkpoints, spawns, conclusão de agentes, finish e relatório.

## Arquitetura do Sistema

### Componentes Existentes Relevantes

- `plugins/claude-tech-squad/runtime-policy.yaml`
  - Fonte de verdade para `language_policy`, `agent_teams`, `agent_worktrees` e cross-talk.

- `plugins/claude-tech-squad/bin/detect-team-mode.sh`
  - Resolve `mode=<teammate|inline>`.

- `plugins/claude-tech-squad/skills/_shared/orchestration-contract.md`
  - Contrato compartilhado para pt-BR, worktrees, fases CTS e cross-talk audit.

- `scripts/validate.sh`
  - Enforcement de cross-talk, pt-BR, helpers de worktree, phase tags e hook de tmux.

- `plugins/claude-tech-squad/bin/squad_cli/run_lifecycle.py`
  - Estado persistente de execução governada, comandos auxiliares, worktrees, gates, checkpoints e SEP log novo com schema.

- `plugins/claude-tech-squad/bin/squad_cli/cli.py`
  - Grupo `squad-cli run` com comandos `start`, `event`, `gate`, `checkpoint`, `spawn`, `agent-done`, `finish` e `report`.

- `plugins/claude-tech-squad/skills/discovery/SKILL.md`
- `plugins/claude-tech-squad/skills/implement/SKILL.md`
- `plugins/claude-tech-squad/skills/squad/SKILL.md`
  - Ainda tinham linguagem dizendo que cada especialista roda em pane tmux, apesar do fallback inline.

## Design de Implementação

### Task 1.0

Alterar somente texto/contrato:

- `CLAUDE.md`
  - Substituir tabela "No — MUST spawn teammates" por "Mode-aware".
  - Explicar que inline é fallback válido, não bypass silencioso.

- `README.md`
  - Corrigir nota sobre `commands/`.

- Skills centrais
  - Ajustar cabeçalhos e seção `Teammate Architecture`.
  - Manter `TeamCreate` para `mode=teammate`.
  - Declarar inline subagents para `mode=inline`.
  - Preservar gates, SEP, pt-BR, worktree isolation e cross-talk audit.

### Não Alterar Na Task 1.0

- `runtime-policy.yaml`
- `scripts/validate.sh`
- hooks
- helpers de worktree
- lógica de CLI

### Task 3.0

Adicionar uma camada de runtime no CLI:

- `run start`
  - cria `run_id`;
  - persiste estado em `<state-dir>/<run_id>.run.json`;
  - registra `execution_mode`, `language_policy_applied: pt-BR`, `policy_version`, tarefa e comandos auxiliares;
  - expõe comandos de baixo nível para `detect-team-mode.sh`, `init-skill-branch.sh`, `spawn-agent-worktree.sh`, `cleanup-agent-worktree.sh`, `finalize-skill.sh` e `validate-sep-log.py`.

- `run event`
  - registra eventos de execução, comandos e evidências operacionais.

- `run gate`
  - registra gates passados ou bloqueados com motivo.

- `run checkpoint`
  - registra checkpoint e artefato associado.

- `run spawn`
  - registra agente, subagent type, worktree, branch e base commit;
  - retorna requisitos de prompt incluindo `language_policy.spawn_prompt_preamble`, cross-talk em pt-BR e SEP lifecycle.

- `run agent-done`
  - fecha a participação de um agente com status, confiança, tokens, merge e commits pendentes.

- `run finish`
  - marca status final;
  - gera SEP log com `schema_version`, `worktrees`, `language_policy_applied`, fases CTS, gates e checkpoints.

- `run report`
  - retorna resumo JSON auditável para operador, automação ou CI.

## Abordagem de Testes

- Busca textual para garantir que as proibições antigas foram removidas dos arquivos tocados.
- Testes pytest para o ciclo completo `squad-cli run start/event/gate/checkpoint/spawn/agent-done/finish/report`.
- Suíte pytest do `squad_cli` para detectar regressão nos comandos já existentes.
- `bash scripts/validate.sh`.

## Sequenciamento

1. Task 1.0 — Reconciliar inline/tmux em docs e skills centrais.
2. Task 2.0 — Criar `docs/GOVERNANCE.md` como mapa da governança já existente, sem duplicar mecanismo.
3. Task 3.0 — Implementar `squad-cli run ...` como runtime automático que coordena helpers, estado e SEP log.
4. Task 4.0 — Documentar advogado do diabo e conectá-lo ao `adversarial_review`.
5. Task 5.0 — Reorganizar superfície pública em torno de tiers core/advanced, destacando `/bug-fix`, `/mini-squad`, `/discovery`, `/inception`, `/implement` e `/squad` como core delivery.

### Task 5.0

Organizar documentação pública em uma camada de decisão antes do catálogo
completo:

- Core setup: `/onboarding`, `/from-ticket`, `/cost-estimate`, `/dashboard`.
- Core delivery: `/bug-fix`, `/mini-squad`, `/discovery`, `/inception`, `/implement`, `/squad`.
- Core operations: `/hotfix`, `/cloud-debug`, `/incident-postmortem`, `/release`, `/rollover`, `/resume-from-rollover`.
- Advanced review and audit: `/pr-review`, `/security-audit`, `/pentest-deep`, `/tech-debt-audit`, `/refactor`, `/dependency-check`.
- Advanced AI, infra, and scale: `/prompt-review`, `/llm-eval`, `/migration-plan`, `/iac-review`, `/multi-service`, `/pre-commit-lint`, `/test-bootstrap`, `/factory-retrospective`.

Arquivos de documentação do usuário devem permanecer alinhados:

- `README.md`
- `docs/GETTING-STARTED.md`
- `docs/SKILL-SELECTOR.md`
- `docs/MANUAL.md`
- `docs/README.md`
- `CLAUDE.md`

## Riscos Conhecidos

- Mudar demais os skills centrais pode quebrar validações baseadas em grep.
- Reduzir linguagem de tmux de forma excessiva pode contradizer o hook `dev-flow-tmux-gate.sh`.
- O termo "inline fallback" precisa preservar que cross-talk em inline é warning-only, não bloqueante.
- O runtime inicial registra e orienta helpers; execução física automática de cada helper pode ser aprofundada em uma etapa posterior se o projeto quiser transformar o CLI em supervisor executor.

## Arquivos Relevantes

- `CLAUDE.md`
- `README.md`
- `plugins/claude-tech-squad/skills/discovery/SKILL.md`
- `plugins/claude-tech-squad/skills/implement/SKILL.md`
- `plugins/claude-tech-squad/skills/squad/SKILL.md`
- `plugins/claude-tech-squad/runtime-policy.yaml`
- `plugins/claude-tech-squad/bin/detect-team-mode.sh`
- `plugins/claude-tech-squad/bin/squad_cli/run_lifecycle.py`
- `plugins/claude-tech-squad/bin/squad_cli/cli.py`
- `plugins/claude-tech-squad/bin/squad_cli/tests/test_run_lifecycle.py`
- `scripts/validate.sh`
