# Resumo de Tarefas de Implementação — Reconciliar v5.70.0

## Pendências Mapeadas Após Pull Para v5.70.0

- [x] P1. Corrigir `CLAUDE.md`, que ainda dizia que `/implement`, `/squad`, `/discovery`, `/refactor`, `tech-debt-audit` e `pentest-deep` eram `No — MUST spawn teammates`, apesar de o próprio arquivo documentar inline fallback.
- [x] P2. Corrigir cabeçalhos e arquitetura de `discovery`, `implement` e `squad`, que ainda diziam que cada especialista roda em pane tmux, apesar do fallback inline em `runtime-policy.yaml`.
- [x] P3. Nomear/documentar explicitamente o papel de "advogado do diabo" em português como especialização do padrão existente `adversarial_review`.
- [x] P4. Implementar a governança automática com `squad-cli run start/event/gate/checkpoint/spawn/agent-done/finish/report`, usando helpers shell/hooks/SEP como mecanismos de baixo nível.
- [x] P5. Reescrever PRD/TechSpec/Tasks contra `v5.70.0`, sem reaplicar diretamente os artefatos antigos do stash.

## Tarefas

- [x] 1.0 Alinhar contrato inline/tmux e corrigir documentação contraditória
- [x] 2.0 Criar `docs/GOVERNANCE.md` como mapa da governança automática existente
- [x] 3.0 Implementar lifecycle `squad-cli run ...` como runtime de governança automática
- [x] 4.0 Documentar advogado do diabo como especialização do `adversarial_review`
- [x] 5.0 Reorganizar superfície pública em torno de core/advanced skills
- [x] 6.0 Atualizar validações/fixtures se as docs novas exigirem contratos adicionais
