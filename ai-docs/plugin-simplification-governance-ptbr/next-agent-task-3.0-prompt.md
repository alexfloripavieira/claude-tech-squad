# Prompt Para Novo Agente — Task 3.0

Você está no repositório `/home/alex/claude-tech-squad`, atualizado para
`origin/main` em `v5.70.0`, com as Tasks 1.0 e 2.0 já implementadas.

Antes de agir, leia:

- `ai-docs/plugin-simplification-governance-ptbr/prd.md`
- `ai-docs/plugin-simplification-governance-ptbr/techspec.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`
- `ai-docs/plugin-simplification-governance-ptbr/task-1.0-technical-report.md`
- `ai-docs/plugin-simplification-governance-ptbr/task-2.0-technical-report.md`
- `docs/GOVERNANCE.md`

## Contexto

A base `v5.70.0` já possui governança automática via:

- helpers shell;
- hooks;
- SEP logs;
- watchdog;
- worktrees por agente;
- cross-talk audit;
- `validate-sep-log.py`;
- `scripts/validate.sh`.

A proposta original imaginava comandos como:

```bash
squad-cli run start
squad-cli run event
squad-cli run gate
squad-cli run checkpoint
squad-cli run finish
squad-cli run report
```

A Task 3.0 deve decidir, tecnicamente, se esses comandos ainda devem ser
implementados ou se duplicariam a arquitetura atual.

## Sua Tarefa

Execute a **Task 3.0 — Avaliar lifecycle `squad-cli run ...` contra helpers já existentes**.

Esta task é uma análise técnica com recomendação documentada. Não implemente o
CLI ainda, a menos que a análise encontre uma lacuna pequena e inequívoca que
precise de ajuste documental.

## Arquivos Que Você Deve Ler

- `plugins/claude-tech-squad/bin/squad_cli/cli.py`
- `plugins/claude-tech-squad/bin/squad_cli/sep_log.py`
- `plugins/claude-tech-squad/bin/squad_cli/dashboard.py`
- `plugins/claude-tech-squad/bin/init-skill-branch.sh`
- `plugins/claude-tech-squad/bin/spawn-agent-worktree.sh`
- `plugins/claude-tech-squad/bin/cleanup-agent-worktree.sh`
- `plugins/claude-tech-squad/bin/finalize-skill.sh`
- `plugins/claude-tech-squad/bin/validate-sep-log.py`
- `plugins/claude-tech-squad/runtime-policy.yaml`
- `docs/GOVERNANCE.md`

## Perguntas Que A Análise Deve Responder

1. `squad-cli run start/event/gate/checkpoint/finish/report` resolveria uma lacuna real?
2. Quais responsabilidades já estão cobertas pelos helpers shell?
3. Quais responsabilidades já estão cobertas por SEP logs e dashboard?
4. Existe risco de criar duas fontes de verdade?
5. Se o CLI for útil, ele deve ser:
   - wrapper fino sobre os helpers existentes;
   - API de leitura/relatório;
   - ou substituto gradual dos scripts?
6. Qual opção é recomendada para a próxima task?

## Entregáveis

1. Criar `ai-docs/plugin-simplification-governance-ptbr/task-3.0-cli-lifecycle-decision.md`.
2. Atualizar `ai-docs/plugin-simplification-governance-ptbr/tasks.md`, marcando Task 3.0 como concluída.
3. Gerar relatório técnico em `ai-docs/plugin-simplification-governance-ptbr/task-3.0-technical-report.md`.
4. Gerar prompt para a próxima task em `ai-docs/plugin-simplification-governance-ptbr/next-agent-task-4.0-prompt.md`.

## Critério De Recomendação

Prefira a opção que reduz complexidade e evita duplicação.

Uma recomendação aceitável pode ser:

- não criar `squad-cli run ...` agora;
- documentar os helpers como fonte de verdade;
- adicionar no futuro apenas comandos de relatório/leitura se houver demanda.

Mas valide isso lendo o código atual antes de concluir.

## Verificação Obrigatória

Execute:

```bash
bash scripts/validate.sh
```

No relatório final, inclua:

- arquivos alterados;
- resumo da decisão;
- evidência de validação;
- recomendação para a Task 4.0.
