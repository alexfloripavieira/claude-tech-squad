# Skill Selector — Decision Tree

Use this guide to choose the right skill without reading the full playbook.

> **Stack routing is automatic.** You never need to specify your stack. Every skill that spawns implementation agents detects it at preflight (Django, React, Vue, TypeScript, JavaScript, Python) and resolves the right specialist automatically.

> **LLM/AI bench is automatic.** `/squad`, `/implement`, `/security-audit`, and `/onboarding` detect LLM/AI code (OpenAI, Anthropic, LangChain, pgvector, etc.) and activate the AI specialist bench without any extra configuration.

---

## Decision Tree

```mermaid
flowchart TD
    START([What is the situation?]) --> Q1{First use in this repository?}
    Q1 -->|Yes| ONBOARDING[/onboarding]
    Q1 -->|No| Q2{Is production broken right now?}

    Q2 -->|Yes| Q3{Cloud incident / logs investigation?}
    Q3 -->|Yes| CLOUD[/cloud-debug]
    Q3 -->|No| HOTFIX[/hotfix]

    Q2 -->|No| Q4{Incident resolved — need a post-mortem?}
    Q4 -->|Yes| POSTMORTEM[/incident-postmortem]

    Q4 -->|No| Q5{Have a PR to review?}
    Q5 -->|Yes| PR[/pr-review]

    Q5 -->|No| Q6{Infrastructure changes \n(Terraform, Helm, CDK)?}
    Q6 -->|Yes| IAC[/iac-review]

    Q6 -->|No| Q7{Prompt file or AI pipeline changes?}
    Q7 -->|Yes| Q8{Reviewing prompt files specifically?}
    Q8 -->|Yes| PROMPT[/prompt-review]
    Q8 -->|No| LLMEVAL[/llm-eval]

    Q7 -->|No| Q9{Database schema changes?}
    Q9 -->|Yes| MIGRATION[/migration-plan]

    Q9 -->|No| Q10{Need to audit dependencies / CVEs?}
    Q10 -->|Yes| DEP[/dependency-check]

    Q10 -->|No| Q11{Need a full security audit?}
    Q11 -->|Yes| SEC[/security-audit]

    Q11 -->|No| Q12{Technical debt to clean up safely?}
    Q12 -->|Yes| REFACTOR[/refactor]

    Q12 -->|No| Q13{Have a bug to fix?}
    Q13 -->|Yes| Q14{Production / emergency bug?}
    Q14 -->|Yes| HOTFIX
    Q14 -->|No| BUGFIX[/bug-fix]

    Q13 -->|No| Q15{Implementation done — need to cut a release?}
    Q15 -->|Yes| RELEASE[/release]

    Q15 -->|No| Q16{Change spans multiple services / repos?}
    Q16 -->|Yes| MULTI[/multi-service]

    Q16 -->|No| Q17{Need to set up automatic lint on commits?}
    Q17 -->|Yes| LINT[/pre-commit-lint]

    Q17 -->|No| Q18{Want to review past squad executions?}
    Q18 -->|Yes| Q18b{Want AI recommendations or just a status summary?}
    Q18b -->|AI analysis| RETRO[/factory-retrospective]
    Q18b -->|Quick summary| DASH[/dashboard]

    Q18 -->|No| Q19{Have an approved blueprint to implement?}
    Q19 -->|Yes| IMPLEMENT[/implement]

    Q19 -->|No| Q20{Want the full pipeline — from problem to release?}
    Q20 -->|Yes| SQUAD[/squad]
    Q20 -->|No| DISCOVERY[/discovery]
```

---

## Reference Table

| Skill | When to use | When NOT to use | Escalate to |
|---|---|---|---|
| `/onboarding` | First use in a repo — creates `ai-docs/`, `CLAUDE.md`, security baseline | Repo already configured | n/a |
| `/discovery` | Feature still needs shaping — produces a PRD + blueprint with requirements, architecture, and test plan | Blueprint already approved | `/inception` or `/implement` |
| `/inception` | Have a PRD, need a TechSpec — technical refinement: architecture, risks, quality gates, effort estimate | No PRD yet, or TechSpec already approved | `/implement` |
| `/implement` | Approved PRD + TechSpec, ready to build — generates tasks + work-item map, then TDD-first, review, QA, docs, release | No PRD/TechSpec in `ai-docs/prd-<slug>/` | `/discovery` then `/inception` |
| `/squad` | Full end-to-end pipeline: discovery + implementation + release in one session | Implementing from existing blueprint only | `/implement` |
| `/bug-fix` | Isolated bug (1–2 files), non-emergency — writes a failing test to prove the bug before fixing it | Production is down — use `/hotfix` | `/hotfix` |
| `/hotfix` | Production is broken now — minimal patch, `hotfix/` branch, PR and deploy checklist | Planned maintenance or non-urgent bug | `/incident-postmortem` after resolving |
| `/pr-review` | Review any pull request with a specialist bench | No existing PR | `/squad` |
| `/security-audit` | Full security audit — static analysis, CVEs, secrets, OWASP | Active production incident — use `/cloud-debug` | `/cloud-debug` |
| `/dependency-check` | Check for CVEs and outdated packages | Need a full audit | `/security-audit` |
| `/refactor` | Safe technical debt reduction — writes characterization tests before refactoring | Active bugs exist — fix first | `/bug-fix` |
| `/release` | Implementation done, cut a release — notes, tag, rollback plan, SRE sign-off | Still implementing | `/squad` |
| `/incident-postmortem` | Incident resolved — rebuild timeline, root cause, 5-whys, action plan | Incident still active | `/cloud-debug` |
| `/llm-eval` | Any change to prompts, RAG pipeline, embedding model, or AI logic | No AI code in repository | n/a |
| `/prompt-review` | Review prompt files before merge — regression, injection scan, token impact | No prompt files changed | `/llm-eval` |
| `/multi-service` | Feature spans multiple repos or services — dependency map, contracts, deploy sequence | Single-service change | `/squad` |
| `/iac-review` | Before any `terraform apply`, `helm upgrade`, `cdk deploy` — blast radius, security, cost | No infrastructure changes | `/security-audit` |
| `/cloud-debug` | Active production or staging incident — collect logs, analyze stack traces, action plan | No cloud log access | `/hotfix` |
| `/migration-plan` | Database schema changes — migration strategy, rollback, safe sequencing | No schema changes | `/squad` |
| `/pre-commit-lint` | Set up auto-fix lint before commits — ruff, black, eslint, prettier, sonar | Lint already configured | n/a |
| `/factory-retrospective` | Review past squad executions — retry patterns, fallback gaps, quality trends | No prior executions in logs | n/a |
| `/dashboard` | Instant pipeline health summary — success rates, blocked gates, pending post-mortems. No agents spawned. | Want AI analysis and recommendations — use `/factory-retrospective` | `/factory-retrospective` |

---

## Quick Heuristics

| Signal | Recommended skill |
|---|---|
| "First time here" | `/onboarding` |
| "Production is down" | `/hotfix` or `/cloud-debug` |
| "I have a feature idea" | `/discovery` → `/inception` → `/implement` |
| "Have a PRD, need a TechSpec" | `/inception` |
| "I want everything at once" | `/squad` |
| "Found a bug" | `/bug-fix` (non-urgent) or `/hotfix` (emergency) |
| "PR open for review" | `/pr-review` |
| "Changed a prompt file" | `/prompt-review` + `/llm-eval` |
| "About to run `terraform apply`" | `/iac-review` first |
| "Need to cut a release" | `/release` |
| "Incident happened" | `/cloud-debug` (active) or `/incident-postmortem` (resolved) |
| "Code is messy" | `/refactor` |
| "Deps might have CVEs" | `/dependency-check` |
| "Want to improve the squad process" | `/factory-retrospective` |
| "Quick health check on recent runs" | `/dashboard` |

---

## Cost vs Scope Guide

**Choose the smallest skill that covers your task.** Bigger skills produce better results for complex work but waste tokens on simple tasks.

| Task complexity | Recommended skill | Estimated agents | Estimated tokens | Estimated cost (Opus) |
|---|---|---|---|---|
| **Fix a typo / 1-file change** | Don't use the plugin — just ask Claude directly | 0 | ~5K | ~$0.01 |
| **Bug fix (1-3 files)** | `/bug-fix` | 3-5 | 200K-400K | ~$1-3 |
| **Hotfix (production down)** | `/hotfix` | 4-6 | 300K-500K | ~$2-4 |
| **PR review** | `/pr-review` | 6-8 | 300K-600K | ~$2-5 |
| **Security audit** | `/security-audit` | 2-4 | 200K-400K | ~$1-3 |
| **Refactor (scoped)** | `/refactor` | 4-6 | 400K-800K | ~$3-6 |
| **Feature (blueprint only)** | `/discovery` | 10-14 | 800K-1.5M | ~$6-12 |
| **Feature (build from blueprint)** | `/implement` | 10-15 | 1.5M-3M | ~$10-20 |
| **Feature (end-to-end)** | `/squad` | 20-30 | 3M-5M | ~$15-30 |

**Rules of thumb:**
- If the fix is under 5 lines, **don't use a skill** — just ask Claude
- If you already know the root cause, use `/bug-fix` not `/squad`
- If you have a blueprint, use `/implement` not `/squad` (saves entire discovery phase)
- `/pr-review` is cheaper than manual review by 6 specialists — use it on every PR
- `/dashboard` and `/factory-retrospective` cost almost nothing (read-only, no agents or 1 agent)

**Anti-patterns:**
- Using `/squad` for a typo fix → wastes ~$20 on discovery + architecture for nothing
- Using `/discovery` when you already know what to build → skip to `/implement`
- Running `/security-audit` after every commit → run it weekly or before releases
- Skipping `/pr-review` to save tokens → the cheapest skill that catches real bugs
