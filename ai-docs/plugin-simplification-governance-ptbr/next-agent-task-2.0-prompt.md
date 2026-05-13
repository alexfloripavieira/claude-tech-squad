# Prompt Para Novo Agente — Task 2.0

Você está no repositório `/home/alex/claude-tech-squad`, atualizado para `origin/main` em `v5.70.0`.

Antes de agir, leia:

- `ai-docs/plugin-simplification-governance-ptbr/prd.md`
- `ai-docs/plugin-simplification-governance-ptbr/techspec.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`
- `ai-docs/plugin-simplification-governance-ptbr/task-1.0-technical-report.md`

## Contexto

A Task 1.0 já foi executada. Ela reconciliou `inline` e `tmux` em:

- `CLAUDE.md`
- `README.md`
- `plugins/claude-tech-squad/skills/discovery/SKILL.md`
- `plugins/claude-tech-squad/skills/implement/SKILL.md`
- `plugins/claude-tech-squad/skills/squad/SKILL.md`

Validação passou:

```bash
bash scripts/validate.sh
# Agents found: 81
# claude-tech-squad validation passed (v5.70.0, 81 agents)
```

## Sua Tarefa

Execute a **Task 2.0 — Criar `docs/GOVERNANCE.md` como mapa da governança automática existente**.

Não invente uma nova governança. Documente a arquitetura que já existe em `v5.70.0`.

## Arquivos Que Você Deve Ler

- `plugins/claude-tech-squad/runtime-policy.yaml`
- `plugins/claude-tech-squad/skills/_shared/orchestration-contract.md`
- `plugins/claude-tech-squad/hooks/pre-tool-guard.sh`
- `plugins/claude-tech-squad/hooks/dev-flow-tmux-gate.sh`
- `plugins/claude-tech-squad/hooks/skill-active-guard.sh`
- `plugins/claude-tech-squad/hooks/stale-skill-detector.sh`
- `plugins/claude-tech-squad/bin/init-skill-branch.sh`
- `plugins/claude-tech-squad/bin/spawn-agent-worktree.sh`
- `plugins/claude-tech-squad/bin/cleanup-agent-worktree.sh`
- `plugins/claude-tech-squad/bin/finalize-skill.sh`
- `plugins/claude-tech-squad/bin/watchdog.sh`
- `plugins/claude-tech-squad/bin/validate-sep-log.py`
- `scripts/validate.sh`

## Entregáveis

1. Criar `docs/GOVERNANCE.md`.
2. O documento deve explicar, em português:
   - visão geral da governança;
   - safety gates e hooks;
   - resolução `teammate|inline`;
   - pt-BR language policy;
   - cross-talk audit;
   - worktrees por agente;
   - watchdog e timeouts;
   - bypass policy;
   - SEP log e validação de schema;
   - responsabilidades do orquestrador;
   - o que ainda fica para tasks futuras.
3. Atualizar `ai-docs/plugin-simplification-governance-ptbr/tasks.md`, marcando Task 2.0 como concluída.
4. Gerar um relatório técnico da Task 2.0 em `ai-docs/plugin-simplification-governance-ptbr/task-2.0-technical-report.md`.
5. Gerar o prompt para a próxima task em `ai-docs/plugin-simplification-governance-ptbr/next-agent-task-3.0-prompt.md`.

## Restrições

- Não altere `runtime-policy.yaml` nesta task, salvo se encontrar erro factual bloqueante.
- Não altere `scripts/validate.sh` nesta task, salvo se a validação exigir a presença de `docs/GOVERNANCE.md`.
- Não aplique o stash antigo (`stash@{0}`) diretamente.
- Preserve a política de português brasileiro para texto natural.
- Mantenha código, comandos, paths, tags estruturadas e chaves YAML em inglês quando necessário.

## Verificação Obrigatória

Execute:

```bash
bash scripts/validate.sh
```

Se alterar qualquer script executável ou hook por necessidade, execute também:

```bash
bash scripts/smoke-test.sh
```

No relatório final, inclua:

- arquivos alterados;
- resumo técnico;
- evidência de validação;
- pendências para Task 3.0.
