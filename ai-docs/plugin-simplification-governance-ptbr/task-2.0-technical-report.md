# Relatório Técnico — Task 2.0

## Contexto

A Task 2.0 criou um documento central de governança para a base `v5.70.0`.
O objetivo foi mapear os mecanismos automáticos já existentes, não propor uma
segunda governança paralela.

A Task 1.0 já havia reconciliado `inline` e `tmux` nos contratos principais.
Esta task avançou o próximo ponto do plano: tornar explícito como a governança
realmente funciona hoje.

## O Que Foi Implementado

### 1. Novo `docs/GOVERNANCE.md`

Criado o documento `docs/GOVERNANCE.md`, em português, cobrindo:

- princípio operacional da governança;
- safety gates;
- hook `pre-tool-guard.sh`;
- resolução de modo `teammate|inline`;
- hook `dev-flow-tmux-gate.sh`;
- política de idioma pt-BR;
- cross-talk entre agentes;
- handoff de arquivos via git entre worktrees;
- worktrees por agente;
- hook `skill-active-guard.sh`;
- watchdog e timeouts;
- bypass policy;
- SEP log e schema validation;
- stale skill detection;
- validação estrutural via `scripts/validate.sh`;
- responsabilidades do orquestrador;
- pontos que ainda ficam para evolução.

### 2. Atualização Do Backlog

Atualizado `ai-docs/plugin-simplification-governance-ptbr/tasks.md`:

- Task 2.0 marcada como concluída.
- P3 e P4 continuam pendentes.

## Arquitetura Documentada

O documento deixa claro que a governança atual é distribuída entre:

- `plugins/claude-tech-squad/runtime-policy.yaml`;
- `plugins/claude-tech-squad/skills/_shared/orchestration-contract.md`;
- hooks em `plugins/claude-tech-squad/hooks/`;
- helpers em `plugins/claude-tech-squad/bin/`;
- SEP logs em `ai-docs/.squad-log/`;
- validações em `scripts/validate.sh`.

## O Que Não Foi Alterado

Por desenho, esta task não alterou:

- `runtime-policy.yaml`;
- hooks;
- helpers shell;
- `scripts/validate.sh`;
- `squad-cli`;
- skills.

A task é documental, mas amarrada ao comportamento real da base atual.

## O Que Falta Implementar

### Task 3.0 — Avaliar `squad-cli run ...`

Ainda precisamos decidir se os comandos abaixo agregam valor ou duplicam a
arquitetura atual:

```bash
squad-cli run start
squad-cli run event
squad-cli run gate
squad-cli run checkpoint
squad-cli run finish
squad-cli run report
```

A análise deve comparar essa ideia com:

- `init-skill-branch.sh`;
- `spawn-agent-worktree.sh`;
- `cleanup-agent-worktree.sh`;
- `finalize-skill.sh`;
- `validate-sep-log.py`;
- SEP logs atuais;
- dashboard atual.

### Task 4.0 — Advogado Do Diabo

O padrão `adversarial_review` existe, mas o papel "advogado do diabo" ainda
precisa ser nomeado e documentado explicitamente em português.

### Task 5.0 — Superfície Pública

Ainda falta reorganizar README/Skill Selector para destacar caminhos core e
avançados, especialmente com `/mini-squad`.

## Evidência De Verificação

Validação executada:

```bash
bash scripts/validate.sh
```

Resultado:

```text
Agents found: 81
claude-tech-squad validation passed (v5.70.0, 81 agents)
```

## Arquivos Alterados Nesta Task

- `docs/GOVERNANCE.md`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`

## Estado Do Working Tree

Além dos arquivos da Task 2.0, o working tree ainda contém as mudanças da Task
1.0 e os artefatos de planejamento:

- `CLAUDE.md`
- `README.md`
- `plugins/claude-tech-squad/skills/discovery/SKILL.md`
- `plugins/claude-tech-squad/skills/implement/SKILL.md`
- `plugins/claude-tech-squad/skills/squad/SKILL.md`
- `ai-docs/plugin-simplification-governance-ptbr/`
- `docs/GOVERNANCE.md`

O stash antigo continua preservado apenas como referência:

```text
stash@{0}: wip-before-origin-main-reassessment
```
