# PRD — Simplificação do Plugin, Governança Automática e Comunicação em Português

## Visão Geral

Após atualizar o repositório para `v5.70.0`, o `claude-tech-squad` já contém parte importante da visão original: política de idioma pt-BR, cross-talk entre agentes, worktrees por agente, watchdog, bypass lint, `/mini-squad` e detecção de modo `teammate|inline`.

Esta iniciativa agora foca em reconciliar a experiência e a documentação com a arquitetura existente. O objetivo é manter a governança forte que já foi implementada, mas remover contradições, tornar o inline fallback explicitamente válido, documentar melhor a comunicação entre agentes em português e evoluir o papel de revisão adversarial para um "advogado do diabo" claro e rastreável.

## Objetivos

- Alinhar documentação e skills com `runtime-policy.yaml::agent_teams.mode_resolution`.
- Tratar `teammate/tmux` como modo preferido e `inline` como fallback válido.
- Preservar pt-BR obrigatório para comunicação natural entre usuário, orquestrador e agentes.
- Preservar cross-talk agente-agente como requisito essencial.
- Tornar explícito o papel de "advogado do diabo" nos pontos críticos de decisão.
- Organizar a superfície pública em core e advanced, reduzindo densidade para o
  operador sem remover skills.
- Automatizar a governança por um runtime explícito, sem substituir os helpers já implementados em `v5.70.0`.
- Manter `bash scripts/validate.sh` passando durante a evolução.

## Histórias de Usuário

- Como operador, quero que a documentação diga claramente quando estou em `teammate` ou `inline`, para confiar no resultado mesmo sem panes tmux.
- Como operador, quero que os agentes conversem entre si em português, para reduzir mal-entendidos e melhorar decisões.
- Como tech lead, quero que revisões adversariais sejam nomeadas como "advogado do diabo", para saber que premissas foram desafiadas antes da execução.
- Como mantenedor, quero que os contratos centrais reflitam a base atual, para não manter instruções contraditórias em `CLAUDE.md`, skills e docs.

## Funcionalidades Principais

1. **Contrato inline/tmux reconciliado**
   - `teammate` continua sendo modo preferido quando tmux/Agent Teams estão disponíveis.
   - `inline` é fallback válido quando `detect-team-mode.sh` resolve `mode=inline`.
   - Cross-talk em inline é warning-only, conforme `runtime-policy.yaml`.

2. **Comunicação entre agentes em português**
   - Preservar `language_policy.default_locale: pt-BR`.
   - Preservar `Inter-Teammate Cross-Talk Protocol`.
   - Explicitar que mensagens naturais entre agentes devem ser em português.

3. **Advogado do diabo**
   - Nomear o padrão `adversarial_review` como papel de advogado do diabo.
   - Registrar objeções, mitigações e decisão em SEP ou relatório.

4. **Governança automática por runtime**
   - `squad-cli run start` inicia uma execução governada, registra modo, idioma, helpers e estado.
   - `squad-cli run spawn` registra worktree, branch, agente e requisitos de prompt pt-BR.
   - `squad-cli run event`, `gate` e `checkpoint` registram decisões, evidências e bloqueios.
   - `squad-cli run agent-done` fecha a participação de cada agente com tokens, merge e confiança.
   - `squad-cli run finish` gera SEP log com schema, `worktrees`, fases CTS e `language_policy_applied`.
   - `squad-cli run report` permite auditoria resumida por automação ou operador.

5. **Superfície pública core/advanced**
   - Core setup: preparar repo, rotear ticket, estimar custo e ver saúde da esteira.
   - Core delivery: corrigir bug, entregar feature pequena, planejar, refinar, implementar e rodar pipeline completo.
   - Core operations: produção, incidentes, release e handoff de contexto.
   - Advanced review/audit: revisões e auditorias especializadas.
   - Advanced AI/infra/scale: AI, banco, infraestrutura, multi-serviço e automação de processo.

## Experiência do Usuário

O usuário deve ver uma explicação consistente: o plugin prefere teammate/tmux para visibilidade e cross-talk bloqueante, mas continua válido em inline quando os requisitos não estão disponíveis. A comunicação natural permanece em português brasileiro. As tags estruturadas, comandos, paths, código e chaves YAML continuam em inglês por compatibilidade.

## Restrições Técnicas de Alto Nível

- Não quebrar `v5.70.0`.
- Não remover mecanismos recém-introduzidos: worktrees, watchdog, cross-talk, language policy, `/mini-squad`.
- Não aplicar patches antigos do stash diretamente.
- Manter `bash scripts/validate.sh` passando.
- Evoluir docs/skills sem quebrar contratos validados por grep.

## Fora de Escopo

- Reescrever a arquitetura de worktrees.
- Remover gate de tmux.
- Remover cross-talk.
- Substituir hooks de segurança por lógica Python.
- Remover helpers shell existentes; o runtime deve coordená-los e registrá-los.
