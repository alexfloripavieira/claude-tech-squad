# Skill Selector — Decision Tree

Use this guide to choose the right skill without reading the full playbook.

---

## Decision Tree

```mermaid
flowchart TD
    START([Qual é a situação?]) --> Q1{Primeiro uso neste repositório?}
    Q1 -->|Sim| ONBOARDING[/onboarding]
    Q1 -->|Não| Q2{Produção está quebrada agora?}

    Q2 -->|Sim| Q3{Incidente em cloud / logs?}
    Q3 -->|Sim| CLOUD[/cloud-debug]
    Q3 -->|Não| HOTFIX[/hotfix]

    Q2 -->|Não| Q4{Incidente já resolvido — precisa de análise?}
    Q4 -->|Sim| POSTMORTEM[/incident-postmortem]

    Q4 -->|Não| Q5{Tem um PR para revisar?}
    Q5 -->|Sim| PR[/pr-review]

    Q5 -->|Não| Q6{Tem mudanças de infraestrutura \n(Terraform, Helm, CDK)?}
    Q6 -->|Sim| IAC[/iac-review]

    Q6 -->|Não| Q7{Tem mudanças em prompts ou \nfeatures de AI?}
    Q7 -->|Sim| Q8{É revisão de arquivos de prompt?}
    Q8 -->|Sim| PROMPT[/prompt-review]
    Q8 -->|Não| LLMEVAL[/llm-eval]

    Q7 -->|Não| Q9{Tem mudanças de schema de banco?}
    Q9 -->|Sim| MIGRATION[/migration-plan]

    Q9 -->|Não| Q10{Precisa checar dependências / CVEs?}
    Q10 -->|Sim| DEP[/dependency-check]

    Q10 -->|Não| Q11{Precisa de auditoria de segurança?}
    Q11 -->|Sim| SEC[/security-audit]

    Q11 -->|Não| Q12{Tem débito técnico para refatorar?}
    Q12 -->|Sim| REFACTOR[/refactor]

    Q12 -->|Não| Q13{Tem um bug para corrigir?}
    Q13 -->|Sim| Q14{Bug em produção / emergencial?}
    Q14 -->|Sim| HOTFIX
    Q14 -->|Não| BUGFIX[/bug-fix]

    Q13 -->|Não| Q15{Implementação concluída — precisa de release?}
    Q15 -->|Sim| RELEASE[/release]

    Q15 -->|Não| Q16{Mudança abrange múltiplos serviços / repos?}
    Q16 -->|Sim| MULTI[/multi-service]

    Q16 -->|Não| Q17{Precisa configurar lint automático?}
    Q17 -->|Sim| LINT[/pre-commit-lint]

    Q17 -->|Não| Q18{Quer revisar execuções passadas da squad?}
    Q18 -->|Sim| RETRO[/factory-retrospective]

    Q18 -->|Não| Q19{Tem blueprint aprovado para implementar?}
    Q19 -->|Sim| IMPLEMENT[/implement]

    Q19 -->|Não| Q20{Quer o pipeline completo — do problema ao release?}
    Q20 -->|Sim| SQUAD[/squad]
    Q20 -->|Não| DISCOVERY[/discovery]
```

---

## Reference Table

| Skill | Quando usar | Quando NÃO usar | Escalate para |
|---|---|---|---|
| `/onboarding` | Primeiro uso em um repositório — cria `ai-docs/`, `CLAUDE.md`, baseline de segurança | Repositório já configurado | n/a |
| `/discovery` | Feature ainda precisa de forma — produz blueprint completo com requisitos, arquitetura e plano de testes | Blueprint já aprovado | `/implement` |
| `/implement` | Blueprint aprovado, pronto para construir — TDD-first, review, QA, docs, release | Sem blueprint na conversa | `/discovery` |
| `/squad` | Pipeline completo de ponta a ponta: discovery + implementação + release em uma sessão | Apenas implementar a partir de blueprint existente | `/implement` |
| `/hotfix` | Produção quebrada agora — patch mínimo, branch `hotfix/`, PR e deploy checklist | Manutenção planejada ou bug não-urgente | `/incident-postmortem` após resolver |
| `/bug-fix` | Bug isolado (1–2 arquivos), não emergencial — escreve teste que prova o bug antes de corrigir | Produção em queda — use `/hotfix` | `/hotfix` |
| `/pr-review` | Revisar qualquer pull request com bench especializado | Sem PR existente | `/squad` |
| `/security-audit` | Auditoria completa de segurança — estática, CVEs, secrets, OWASP | Incidente ativo em produção — use `/cloud-debug` | `/cloud-debug` |
| `/dependency-check` | Verificar CVEs e pacotes desatualizados | Precisa de auditoria completa | `/security-audit` |
| `/refactor` | Redução segura de débito técnico — escreve testes de caracterização antes de refatorar | Bugs ativos existem — corrija antes de refatorar | `/bug-fix` |
| `/release` | Implementação concluída, cortar release — notas, tag, rollback plan, sign-off do SRE | Ainda em implementação | `/squad` |
| `/incident-postmortem` | Incidente resolvido — reconstruir timeline, root cause, 5-whys, plano de ação | Incidente ainda ativo | `/cloud-debug` |
| `/llm-eval` | Qualquer mudança em prompts, pipeline RAG, modelo de embedding ou lógica de AI | Sem código de AI no repositório | n/a |
| `/prompt-review` | Revisar arquivos de prompt antes de merge — regressão, injection scan, impacto de tokens | Nenhum arquivo de prompt alterado | `/llm-eval` |
| `/multi-service` | Feature abrange múltiplos repositórios ou serviços — mapa de dependências, contratos, sequência de deploy | Mudança em serviço único | `/squad` |
| `/iac-review` | Antes de qualquer `terraform apply`, `helm upgrade`, `cdk deploy` — blast radius, segurança, custo | Sem mudanças de infraestrutura | `/security-audit` |
| `/cloud-debug` | Incidente ativo em produção ou staging — coleta logs, analisa stack traces, plano de ação | Sem acesso a logs de cloud | `/hotfix` |
| `/migration-plan` | Mudanças de schema de banco — estratégia de migração, rollback, sequência segura | Sem mudanças de schema | `/squad` |
| `/pre-commit-lint` | Configurar auto-fix de lint antes de commits — ruff, black, eslint, prettier, sonar | Lint já configurado | n/a |
| `/factory-retrospective` | Revisar execuções passadas da squad — padrões de retry, fallback, gaps de qualidade | Sem execuções anteriores nos logs | n/a |

---

## Quick Heuristics

| Sinal | Skill recomendada |
|---|---|
| "É a primeira vez aqui" | `/onboarding` |
| "Produção caiu" | `/hotfix` ou `/cloud-debug` |
| "Tenho uma ideia de feature" | `/discovery` → `/implement` |
| "Quero tudo de uma vez" | `/squad` |
| "Encontrei um bug" | `/bug-fix` (simples) ou `/hotfix` (emergencial) |
| "PR aberto para review" | `/pr-review` |
| "Mudei um prompt" | `/prompt-review` + `/llm-eval` |
| "Vou fazer `terraform apply`" | `/iac-review` primeiro |
| "Preciso fazer release" | `/release` |
| "Incidente aconteceu" | `/cloud-debug` (ativo) ou `/incident-postmortem` (resolvido) |
| "Código está bagunçado" | `/refactor` |
| "Deps podem ter CVEs" | `/dependency-check` |
| "Quero melhorar o processo da squad" | `/factory-retrospective` |
