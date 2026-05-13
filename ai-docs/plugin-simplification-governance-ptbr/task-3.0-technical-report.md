# Relatório Técnico — Task 3.0

## Status

Concluída.

## Objetivo

Implementar a governança automática como runtime explícito do plugin, usando
`squad-cli run ...` para registrar e auditar o ciclo de vida completo de uma
execução com agentes.

## O Que Foi Implementado

- Novo módulo `plugins/claude-tech-squad/bin/squad_cli/run_lifecycle.py`.
- Novo grupo de comandos `squad-cli run` em
  `plugins/claude-tech-squad/bin/squad_cli/cli.py`.
- Persistência de estado em JSON no formato `<state-dir>/<run_id>.run.json`.
- Comandos:
  - `run start`;
  - `run event`;
  - `run gate`;
  - `run checkpoint`;
  - `run spawn`;
  - `run agent-done`;
  - `run finish`;
  - `run report`.
- SEP log gerado por `run finish` com:
  - `schema_version`;
  - `run_id`;
  - `skill`;
  - `status`;
  - `tokens_input`;
  - `tokens_output`;
  - `estimated_cost_usd`;
  - `total_duration_ms`;
  - `worktrees`;
  - `language_policy_applied: pt-BR`;
  - `cts_phases_completed`.
- `run spawn` retorna requisitos de prompt para garantir:
  - preâmbulo de idioma pt-BR;
  - isolamento por worktree;
  - cross-talk entre agentes em português;
  - lifecycle SEP obrigatório.
- `run start` expõe os comandos auxiliares de baixo nível:
  - `detect-team-mode.sh`;
  - `init-skill-branch.sh`;
  - `spawn-agent-worktree.sh`;
  - `cleanup-agent-worktree.sh`;
  - `finalize-skill.sh`;
  - `validate-sep-log.py`.

## Decisão Técnica

Seguimos com `squad-cli run ...` como camada de governança automática. Os
helpers shell, hooks e `runtime-policy.yaml` continuam sendo os mecanismos de
baixo nível e fontes de verdade. O CLI agora registra, audita e padroniza o
ciclo de vida, sem reimplementar bloqueios de segurança já existentes.

## Arquivos Alterados

- `plugins/claude-tech-squad/bin/squad_cli/run_lifecycle.py`
- `plugins/claude-tech-squad/bin/squad_cli/cli.py`
- `plugins/claude-tech-squad/bin/squad_cli/tests/test_run_lifecycle.py`
- `docs/GOVERNANCE.md`
- `ai-docs/plugin-simplification-governance-ptbr/prd.md`
- `ai-docs/plugin-simplification-governance-ptbr/techspec.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`

## Validação Executada

- `pytest plugins/claude-tech-squad/bin/squad_cli/tests/test_run_lifecycle.py -v`
  - Resultado: 2 testes passaram.
- `pytest plugins/claude-tech-squad/bin/squad_cli/tests -v`
  - Resultado: 30 testes passaram, 1 warning existente de coleta pytest.
- `bash scripts/validate.sh`
  - Resultado: `claude-tech-squad validation passed (v5.70.0, 81 agents)`.
- Smoke manual do lifecycle `squad-cli run start/spawn/agent-done/finish` em
  `/tmp/cts-run-smoke-state` e `/tmp/cts-run-smoke-logs`.
- `python3 plugins/claude-tech-squad/bin/validate-sep-log.py <sep-log-gerado>`
  - Resultado: passou sem violações de schema.

## O Que Ainda Falta Implementar

- Task 4.0: documentar explicitamente o papel de "advogado do diabo" como
  especialização em português do padrão `adversarial_review`.
- Task 5.0: reorganizar a superfície pública do plugin em torno de skills core
  e avançados.
- Task 6.0: atualizar validações e fixtures se os novos contratos documentais
  forem promovidos a obrigatórios.
- Evolução opcional: fazer o `squad-cli run` executar fisicamente os helpers,
  além de registrar e expor os comandos necessários.
