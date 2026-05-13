# Relatório Técnico — Task 6.0

## Status

Concluída.

## Objetivo

Promover os contratos documentais novos para validação mecânica quando isso
reduz risco de regressão sem tornar o projeto excessivamente rígido.

## O Que Foi Implementado

`scripts/validate.sh` agora valida:

- presença de docs públicas essenciais:
  - `docs/SKILL-SELECTOR.md`;
  - `docs/GOVERNANCE.md`;
  - `docs/README.md`.
- presença dos cinco tiers da superfície pública em:
  - `README.md`;
  - `docs/GETTING-STARTED.md`;
  - `docs/SKILL-SELECTOR.md`;
  - `docs/MANUAL.md`;
  - `CLAUDE.md`.
- ausência de contagens públicas antigas:
  - `74 agents`;
  - `28 skills`.
- documentação de `squad-cli run` em `docs/GOVERNANCE.md`.
- documentação de "advogado do diabo" em `docs/GOVERNANCE.md`.
- presença do módulo `plugins/claude-tech-squad/bin/squad_cli/run_lifecycle.py`.
- presença do grupo `@main.group("run")` no CLI.
- presença de `adversarial_review` e `Advogado do diabo` nos skills que usam
  revisão adversarial:
  - `discovery`;
  - `implement`;
  - `squad`;
  - `refactor`;
  - `tech-debt-audit`;
  - `pentest-deep`;
  - `pr-review`;
  - `llm-eval`;
  - `iac-review`.
- documentação de "advogado do diabo" no `runtime-policy.yaml`.
- documentação de "advogado do diabo" no contrato compartilhado de orquestração.

## Arquivos Alterados

- `scripts/validate.sh`
- `ai-docs/plugin-simplification-governance-ptbr/tasks.md`

## Decisão Técnica

Foram adicionados checks de presença e consistência textual de alto valor, mas
sem validar frases completas ou ordem exata das tabelas. Isso protege os novos
contratos contra regressão e ainda permite reescrever a documentação sem quebrar
o build por detalhes editoriais.

## Validação Executada

- `bash scripts/validate.sh`
  - Resultado: `claude-tech-squad validation passed (v5.70.0, 81 agents)`.
- `bash scripts/smoke-test.sh`
  - Resultado: `claude-tech-squad smoke test passed`.

## O Que Fica Em Aberto

- Não foram adicionadas fixtures novas porque os checks documentais couberam no
  `validate.sh` e não exigiram atualização de fixture.
- Se a superfície pública passar a ser gerada por arquivo estruturado no futuro,
  o próximo passo natural é mover os tiers para YAML/JSON e validar docs contra
  essa fonte única.
