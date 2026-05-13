# Prompt Para Novo Agente — Task 6.0

Você está no repositório `/home/alex/claude-tech-squad`, após pull para
`v5.70.0`. Responda e documente tudo em português brasileiro quando for
linguagem natural.

## Contexto

As Tasks 1.0 a 5.0 já foram concluídas:

- Task 1.0 reconciliou `teammate/tmux` como modo preferido e `inline` como
  fallback válido.
- Task 2.0 criou `docs/GOVERNANCE.md`.
- Task 3.0 implementou `squad-cli run start/event/gate/checkpoint/spawn/agent-done/finish/report`.
- Task 4.0 documentou "advogado do diabo" como nome pt-BR do padrão
  `adversarial_review`.
- Task 5.0 reorganizou a superfície pública em tiers core/advanced nas docs.

Arquivos principais:

- `README.md`
- `docs/GETTING-STARTED.md`
- `docs/SKILL-SELECTOR.md`
- `docs/MANUAL.md`
- `docs/README.md`
- `CLAUDE.md`
- `docs/GOVERNANCE.md`
- `plugins/claude-tech-squad/runtime-policy.yaml`
- `plugins/claude-tech-squad/bin/squad_cli/run_lifecycle.py`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`

## Sua Task

Execute a Task 6.0: atualizar validações e fixtures se os novos contratos
documentais devem virar contratos obrigatórios.

## Requisitos

- Primeiro rode `bash scripts/validate.sh` para obter baseline.
- Inspecione `scripts/validate.sh` e scripts relacionados antes de alterar.
- Decida quais novos contratos merecem validação mecânica. Candidatos:
  - docs públicas mencionarem os cinco tiers core/advanced;
  - contagem 81 agents / 29 skills não regredir;
  - skills com `adversarial_review` mencionarem "advogado do diabo";
  - runtime `squad-cli run` estar documentado em `docs/GOVERNANCE.md`;
  - `tasks.md` refletir Tasks 1.0 a 5.0 concluídas.
- Se adicionar validação, faça testes primeiro quando for prático.
- Atualize fixtures somente quando um script existente exigir.
- Rode validação final:
  - `bash scripts/validate.sh`;
  - `pytest plugins/claude-tech-squad/bin/squad_cli/tests -v` se tocar Python;
  - `bash scripts/smoke-test.sh` se tocar validação estrutural ampla.
- Marque Task 6.0 como concluída em
  `ai-docs/plugin-simplification-governance-ptbr/tasks.md`.
- Gere `task-6.0-technical-report.md`.

## Cuidados

- Use `apply_patch` para editar arquivos.
- Não aplique diretamente patches antigos de `stash@{0}`.
- Não reverta mudanças do usuário.
- Mantenha a comunicação natural em pt-BR.
