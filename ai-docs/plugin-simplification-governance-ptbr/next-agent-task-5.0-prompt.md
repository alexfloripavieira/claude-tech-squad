# Prompt Para Novo Agente — Task 5.0

Você está no repositório `/home/alex/claude-tech-squad`, após pull para
`v5.70.0`. Responda e documente tudo em português brasileiro quando for
linguagem natural.

## Contexto

As Tasks 1.0 a 4.0 já foram concluídas:

- Task 1.0 reconciliou `teammate/tmux` como modo preferido e `inline` como
  fallback válido.
- Task 2.0 criou `docs/GOVERNANCE.md`.
- Task 3.0 implementou `squad-cli run start/event/gate/checkpoint/spawn/agent-done/finish/report`.
- Task 4.0 documentou "advogado do diabo" como nome pt-BR do padrão
  `adversarial_review`.

Arquivos principais:

- `ai-docs/plugin-simplification-governance-ptbr/prd.md`
- `ai-docs/plugin-simplification-governance-ptbr/techspec.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`
- `docs/GOVERNANCE.md`
- `plugins/claude-tech-squad/runtime-policy.yaml`

## Sua Task

Execute a Task 5.0: reorganizar a superfície pública do plugin em torno de
skills core e advanced, reduzindo densidade cognitiva sem remover recursos.

## Requisitos

- Primeiro mapeie a superfície atual:
  - skills user-invocable;
  - shims em `commands/`, se existirem;
  - README/CLAUDE/docs que listam comandos ou skills.
- Proponha uma organização clara:
  - core: caminhos recomendados para uso cotidiano;
  - advanced: auditorias, reviews especializados, release, console, dashboard e
    fluxos pesados.
- Não remova arquivos nesta task sem evidência de que são obsoletos.
- Prefira documentação e agrupamento a grandes refactors.
- Preserve `/mini-squad`, `/bug-fix`, `/discovery`, `/implement` e `/squad` como
  caminhos principais se a base atual confirmar isso.
- Atualize `ai-docs/plugin-simplification-governance-ptbr/tasks.md` marcando
  Task 5.0 como concluída.
- Gere `task-5.0-technical-report.md`.
- Gere `next-agent-task-6.0-prompt.md`.

## Validação Esperada

Rode, no mínimo:

- busca textual para confirmar que a nova organização aparece em README/CLAUDE
  ou docs relevantes;
- `bash scripts/validate.sh`.

Se tocar código Python ou CLI, rode também:

- `pytest plugins/claude-tech-squad/bin/squad_cli/tests -v`.

## Cuidados

- Use `apply_patch` para editar arquivos.
- Não aplique diretamente patches antigos de `stash@{0}`.
- Não reverta mudanças do usuário.
- Mantenha a comunicação natural em pt-BR.
