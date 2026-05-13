# Relatório Técnico — Task 4.0

## Status

Concluída.

## Objetivo

Documentar explicitamente o papel "advogado do diabo" em português como
especialização do padrão existente `adversarial_review`, mantendo a comunicação
entre agentes em pt-BR e sem criar arquitetura paralela.

## O Que Foi Implementado

- `runtime-policy.yaml` agora descreve `adversarial_review` como o papel
  operacional "advogado do diabo" em pt-BR.
- O padrão `adversarial_review.applies_to` foi expandido para cobrir todos os
  skills que já declaram pares adversariais:
  - `squad`;
  - `implement`;
  - `discovery`;
  - `refactor`;
  - `tech-debt-audit`;
  - `pentest-deep`;
  - `pr-review`;
  - `llm-eval`;
  - `iac-review`.
- O contrato compartilhado
  `plugins/claude-tech-squad/skills/_shared/orchestration-contract.md` agora
  define o comportamento obrigatório do advogado do diabo:
  - desafiar premissas;
  - expor riscos;
  - questionar alternativas;
  - pedir evidência;
  - debater trade-offs;
  - registrar objeção, mitigação e decisão final quando houver impacto.
- `docs/GOVERNANCE.md` ganhou a seção `Advogado Do Diabo`.
- Skills com pares adversariais agora usam o termo `adversarial_review /
  advogado do diabo` no próprio protocolo de cross-talk.

## Arquivos Alterados

- `plugins/claude-tech-squad/runtime-policy.yaml`
- `plugins/claude-tech-squad/skills/_shared/orchestration-contract.md`
- `docs/GOVERNANCE.md`
- `plugins/claude-tech-squad/skills/discovery/SKILL.md`
- `plugins/claude-tech-squad/skills/implement/SKILL.md`
- `plugins/claude-tech-squad/skills/squad/SKILL.md`
- `plugins/claude-tech-squad/skills/refactor/SKILL.md`
- `plugins/claude-tech-squad/skills/tech-debt-audit/SKILL.md`
- `plugins/claude-tech-squad/skills/pentest-deep/SKILL.md`
- `plugins/claude-tech-squad/skills/pr-review/SKILL.md`
- `plugins/claude-tech-squad/skills/llm-eval/SKILL.md`
- `plugins/claude-tech-squad/skills/iac-review/SKILL.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`

## Decisão Técnica

Não foi criado agente novo. O papel "advogado do diabo" é o nome público em
português do padrão já existente `adversarial_review`. Isso reduz ambiguidade
para operadores e agentes, mas preserva o desenho atual de cross-talk,
worktrees, SEP log e enforcement mode-aware.

## O Que Ainda Falta Implementar

- Task 5.0: reorganizar a superfície pública do plugin em torno de skills core
  e avançados.
- Task 6.0: atualizar validações e fixtures se novos contratos documentais forem
  promovidos a obrigatórios.
- Opcional: adicionar um check específico em `scripts/validate.sh` para garantir
  que skills com `adversarial_review` também mencionem "advogado do diabo".

## Validação Executada

- Busca textual por `advogado do diabo`, `adversarial_review` e termos
  correlatos nos skills, docs e `runtime-policy.yaml`.
- `bash scripts/validate.sh`
  - Resultado: `claude-tech-squad validation passed (v5.70.0, 81 agents)`.
