# Prompt Para Novo Agente — Task 4.0

Você está no repositório `/home/alex/claude-tech-squad`, após pull para
`v5.70.0`. Responda e documente tudo em português brasileiro quando for
linguagem natural.

## Contexto

As Tasks 1.0, 2.0 e 3.0 já foram concluídas:

- Task 1.0 reconciliou `CLAUDE.md`, `README.md` e os skills centrais
  `discovery`, `implement` e `squad` para declarar que `teammate/tmux` é modo
  preferido e `inline` é fallback válido.
- Task 2.0 criou `docs/GOVERNANCE.md` como mapa da governança automática.
- Task 3.0 implementou o runtime `squad-cli run ...` com comandos
  `start/event/gate/checkpoint/spawn/agent-done/finish/report`.

Arquivos principais do plano:

- `ai-docs/plugin-simplification-governance-ptbr/prd.md`
- `ai-docs/plugin-simplification-governance-ptbr/techspec.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`
- `docs/GOVERNANCE.md`

## Sua Task

Execute a Task 4.0: documentar explicitamente o papel de "advogado do diabo" em
português como especialização do padrão existente `adversarial_review`.

## Requisitos

- Não invente uma arquitetura paralela se `adversarial_review` já existir.
- Procure primeiro por `adversarial_review`, `adversarial`, `critic`,
  `reviewer`, `devil`, `diabo` e termos próximos.
- Identifique onde o papel deve aparecer:
  - docs do operador;
  - contratos compartilhados;
  - skills com revisão adversarial;
  - agentes relevantes, se houver agente específico.
- O papel deve deixar claro:
  - nome público em pt-BR: "advogado do diabo";
  - função: desafiar premissas, riscos, escopo, alternativas e falhas de
    evidência;
  - obrigação de comunicar em português com outros agentes e com o orquestrador;
  - obrigação de registrar objeções, mitigação e decisão no relatório ou SEP log;
  - diferença entre discordância útil e bloqueio arbitrário.
- Preserve `runtime-policy.yaml` e validações existentes, a menos que uma
  mudança mínima seja claramente necessária.
- Atualize `ai-docs/plugin-simplification-governance-ptbr/tasks.md` marcando
  Task 4.0 como concluída.
- Gere `task-4.0-technical-report.md`.
- Gere `next-agent-task-5.0-prompt.md`.

## Validação Esperada

Rode, no mínimo:

- busca textual confirmando que "advogado do diabo" aparece nos arquivos
  relevantes;
- `bash scripts/validate.sh`.

Se tocar código Python ou CLI, rode também:

- `pytest plugins/claude-tech-squad/bin/squad_cli/tests -v`.

## Cuidados

- Use `apply_patch` para editar arquivos.
- Não aplique diretamente patches antigos de `stash@{0}`.
- Não reverta mudanças do usuário.
- Mantenha a comunicação natural em pt-BR.
