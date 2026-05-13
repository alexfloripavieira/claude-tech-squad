# Relatório Técnico — Task 5.0

## Status

Concluída.

## Objetivo

Reduzir a densidade cognitiva da superfície pública do plugin, agrupando os 29
skills em tiers core/advanced sem remover capacidades.

## O Que Foi Implementado

- Criada a organização pública em cinco tiers:
  - Core setup;
  - Core delivery;
  - Core operations;
  - Advanced review and audit;
  - Advanced AI, infra, and scale.
- `README.md` agora apresenta essa superfície antes do catálogo completo.
- `docs/GETTING-STARTED.md` agora orienta usuários novos pelos tiers e expande
  os caminhos comuns, incluindo `/bug-fix` e `/mini-squad`.
- `docs/SKILL-SELECTOR.md` ganhou seção `Core vs Advanced Surface` e a tabela de
  referência foi ampliada para cobrir todos os skills user-invocable.
- `docs/MANUAL.md` ganhou a mesma organização core/advanced, uma referência
  completa dos skills e correção de contagem de 74 para 81 agents.
- `docs/README.md` ganhou quick reference alinhado com core setup/core delivery.
- `CLAUDE.md` agora registra que a classificação pública deve permanecer
  sincronizada entre README, Getting Started, Skill Selector e Manual.
- `docs/GETTING-STARTED.md` foi corrigido de 28 para 29 skills.

## Arquivos Alterados

- `README.md`
- `docs/GETTING-STARTED.md`
- `docs/SKILL-SELECTOR.md`
- `docs/MANUAL.md`
- `docs/README.md`
- `CLAUDE.md`
- `ai-docs/plugin-simplification-governance-ptbr/prd.md`
- `ai-docs/plugin-simplification-governance-ptbr/techspec.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`

## Decisão Técnica

Não removemos skills nem shims. A mudança é de apresentação e roteamento
cognitivo: o operador vê primeiro os caminhos recomendados e só depois o
catálogo avançado. Isso mantém compatibilidade com a superfície pública
existente enquanto reduz a chance de escolher `/squad` para tarefas pequenas.

## O Que Ainda Falta Implementar

- Task 6.0: atualizar validações/fixtures se os novos contratos documentais
  forem promovidos a obrigatórios.
- Opcional: adicionar check em `scripts/validate.sh` para garantir que a tabela
  core/advanced permaneça sincronizada entre README, Getting Started, Skill
  Selector, Manual e CLAUDE.

## Validação Executada

- Busca textual confirmando que `Core setup`, `Core delivery`, `Core operations`,
  `Advanced review and audit` e `Advanced AI, infra` aparecem nas docs públicas
  alinhadas.
- Busca textual confirmando que não sobraram ocorrências de `74 agents` ou
  `28 skills` nas docs públicas.
- `bash scripts/validate.sh`
  - Resultado: `claude-tech-squad validation passed (v5.70.0, 81 agents)`.
