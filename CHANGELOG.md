# Changelog

## [5.33.0] - 2026-04-05 — Automated feature release

### Added

- Add boundary text and Absolute Prohibitions to stack specialists
## [5.32.1] - 2026-04-05 — Automated maintenance release

### Changed

- Document stack-aware routing and stack-agnostic skills
## [5.32.0] - 2026-04-05 — Automated feature release

### Added

- Extend stack-aware routing to bug-fix, hotfix, refactor, and pr-review skills
## [5.31.0] - 2026-04-05 — Automated feature release

### Added

- Stack-aware orchestration — auto-route to specialist agents based on detected project stack
## [5.30.1] - 2026-04-05 — Automated maintenance release

### Changed

- Add agent and skill contracts, runtime policy, and safety docs; ignore PRD.md
- Sync after manual release v5.30.0 [skip-release]
## [5.30.0] - 2026-04-05 — Stack Specialists integration: 12 new agents for Django, React, Vue, Python, TypeScript, JavaScript, and Shell stacks

### Added

**Stack Specialist agents (12 new agents — 62 → 74 total):**
Twelve specialized agents previously developed for Django-centric projects are now part of the plugin: `django-pm`, `tech-lead`, `django-backend`, `django-frontend`, `code-reviewer`, `qa-tester`, `react-developer`, `vue-developer`, `python-developer`, `typescript-developer`, `javascript-developer`, and `shell-developer`. Each carries `result_contract`, `Documentation Standard — Context7 First, Repository Fallback`, and `Absolute Prohibitions` (for execution agents). Context7 and Playwright tool declarations are explicit in frontmatter where applicable.

**Context7 and Playwright tools in `frontend-dev`, `qa`, `mobile-dev` frontmatter:**
Existing plugin agents `frontend-dev`, `qa`, and `mobile-dev` now declare explicit Playwright tool lists in their YAML frontmatter, enabling visual verification and E2E flows. `frontend-dev` and `mobile-dev` also gain Context7 for library lookups.

**Context7 tools in `techlead` and `architect` frontmatter:**
`techlead` and `architect` now declare Context7 resolve and query tools in their frontmatter, enabling technology validation before any recommendation is finalized.

**`README.md` Stack Specialists section:**
New section documents all 12 stack specialist agents by category (Django, React/Vue, Python, TypeScript/JavaScript, Shell/Automation) with MCP coverage table and recommended delivery order.

**`docs/MANUAL.md` Section 6 — Stack Specialists table:**
Section 6 updated from 61 to 74 agents. New Stack Specialists tables added with Context7 and Playwright coverage columns per agent.

### Fixed

**`scripts/verify-release.sh` and `scripts/prepare-release-metadata.sh` MANUAL.md version regex:**
Both scripts contained a Portuguese regex (`\*\*Versão:\*\*`) to extract and update the version in `docs/MANUAL.md`. After the MANUAL.md translation to English in v5.29.0, this regex silently failed — `verify-release.sh` could not confirm the version and `prepare-release-metadata.sh` would not update it during automated releases. Both now use the English regex (`\*\*Version:\*\*`), matching `validate.sh` which was fixed in the same translation sprint.

## [5.29.0] - 2026-04-02 — Automated feature release

### Added

- Add TeamCreate and team_name to all skills for teammate visibility
## [5.28.0] - 2026-04-02 — Automated feature release

### Added

- Automate release metadata and operator publish flow (#2)
## [5.27.0] - 2026-04-02 — Publish automático a partir de main

### Changed

**Release agora nasce de `main`, não de tag manual:**
`.github/workflows/release.yml` foi ajustado para disparar em push para `main` quando os arquivos de metadados de release mudam. O workflow:
- resolve a versão a partir de `plugin.json`
- roda `scripts/smoke-test.sh`
- valida metadados com `scripts/verify-release.sh`
- gera bundle e checksum
- cria e faz push da tag automaticamente
- cria a GitHub Release com os assets

**Documentação de release alinhada ao fluxo real:**
`docs/RELEASING.md` e `README.md` agora deixam explícito que o caminho oficial é mergear os metadados de release em `main`; a pipeline faz o resto.

**Validador endurecido para o fluxo de branch publish:**
`scripts/validate.sh` agora falha se o workflow de release não estiver configurado para publicar a partir de `main`.

## [5.26.0] - 2026-04-02 — Publish pipeline completo em GitHub Actions

### Added

**Scripts de publish e release verification:**
Adicionados:
- `scripts/verify-release.sh`
- `scripts/build-release-bundle.sh`

Eles validam alinhamento entre `marketplace.json`, `plugin.json`, `MANUAL.md` e `CHANGELOG.md`, além de gerar bundle `.tar.gz` e checksum `.sha256` para cada release.

### Changed

**Workflow de tag agora é um publish pipeline completo:**
`.github/workflows/release.yml` foi refeito para:
- rodar `scripts/smoke-test.sh`
- validar metadados de release
- gerar release bundle e checksum
- publicar ou atualizar a GitHub Release
- anexar os artefatos da release

**Smoke test agora cobre scripts de publish:**
`scripts/smoke-test.sh` passou a validar `verify-release.sh` e `build-release-bundle.sh` em diretório temporário.

**Release manual deixou de ser o caminho principal:**
`docs/RELEASING.md`, `README.md` e `scripts/release.sh` foram alinhados para deixar explícito que o caminho oficial é a automação do GitHub Actions. O script local continua apenas como fallback.

**Hygiene de build:**
`dist/` passou a ser ignorado no `.gitignore`.

## [5.25.0] - 2026-04-02 — CI no mesmo bar local, governance files e bootstrap de golden runs

### Added

**Bootstrap de golden runs reais:**
Adicionado `scripts/start-golden-run.sh`, que gera a estrutura de captura para um cenário em `ai-docs/dogfood-runs/<scenario>/<timestamp>/` com `prompt.txt`, `trace.md`, `final.md`, `metadata.yaml` e `scorecard.md`.

**Governance files de repositório:**
Adicionados:
- `CONTRIBUTING.md`
- `SECURITY.md`
- `.github/CODEOWNERS`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug-report.md`
- `.github/ISSUE_TEMPLATE/workflow-change.md`

Esses arquivos formalizam ownership, mudança por classe, evidência exigida, validação e tratamento de vulnerabilidades.

**Diretórios de artefatos inicializados:**
Adicionados `.gitkeep` para `ai-docs/.squad-log/` e `ai-docs/dogfood-runs/`, com `.gitignore` ajustado para ignorar o conteúdo gerado sem perder a estrutura do repositório.

### Changed

**CI do GitHub agora roda no mesmo bar do ambiente local:**
`.github/workflows/validate.yml` e `.github/workflows/release.yml` passaram a usar `scripts/smoke-test.sh`, eliminando o gap entre validação local e remota.

**Smoke test agora verifica scaffolding real de golden runs:**
`scripts/smoke-test.sh` passou a executar `start-golden-run.sh` em diretório temporário e validar a geração dos artefatos esperados.

**Validador endurecido novamente:**
`scripts/validate.sh` agora exige governance files, templates, bootstrap scripts, `.gitkeep` dos diretórios de artefato e a presença de `smoke-test.sh` nos workflows do GitHub.

**Documentação atualizada:**
`README.md` e `docs/GOLDEN-RUNS.md` agora incluem o fluxo de scaffolding com `start-golden-run.sh`.

## [5.24.0] - 2026-04-02 — Golden runs, operating system de engenharia e hygiene de release

### Added

**Golden-run contract real:**
`scripts/dogfood-report.sh` valida runs reais capturados em `ai-docs/dogfood-runs/` com base no manifesto `fixtures/dogfooding/scenarios.json`. Cada cenário agora define `required_trace_lines`, `forbidden_strings` e `artifact_contract`.

**Docs de governança e operação:**
Adicionados `docs/GOLDEN-RUNS.md` e `docs/ENGINEERING-OPERATING-SYSTEM.md`, formalizando scorecards, classes de mudança, evidência exigida por workflow, cadência de revisão e métricas operacionais.

**Templates de organização de engenharia:**
Adicionados:
- `templates/rfc-template.md`
- `templates/service-readiness-review.md`
- `templates/golden-run-scorecard.md`

### Changed

**Release pipeline endurecido:**
`scripts/release.sh` passou a rodar `scripts/smoke-test.sh` em vez de apenas `validate.sh`, elevando o bar mínimo antes de qualquer tag.

**Smoke test agora cobre schema de golden runs:**
`scripts/smoke-test.sh` passou a executar `scripts/dogfood-report.sh --schema-only`.

**`.gitignore` alinhado com artefatos gerados:**
Agora ignora `ai-docs/.squad-log/`, `ai-docs/dogfood-runs/`, `__pycache__/` e `.pytest_cache/`.

**Docs centrais atualizadas:**
`README.md`, `docs/GETTING-STARTED.md` e `docs/RELEASING.md` agora refletem a escada de validação, o contracto de golden runs e o operating model.

## [5.23.0] - 2026-04-02 — Dogfooding pack local, fixtures versionados e script de validação

### Added

**Dogfooding pack local em `fixtures/dogfooding/`:**
O repositório agora inclui três cenários versionados e reproduzíveis:
- `layered-monolith`
- `hexagonal-billing`
- `hotfix-checkout`

Cada fixture traz `README.md`, `CLAUDE.md` e estrutura mínima de código para forçar o comportamento esperado da squad sem depender de um repositório externo.

**Manifesto de cenários:**
`fixtures/dogfooding/scenarios.json` centraliza prompts, workflow esperado, arquitetura esperada e agentes relevantes para os três cenários.

**Script `scripts/dogfood.sh`:**
Valida o dogfood pack local, checa estrutura dos fixtures, regras arquiteturais mínimas e referências inválidas. Também suporta `--print-prompts` para imprimir o prompt pack de teste.

### Changed

**Smoke test agora cobre o dogfood pack:**
`scripts/smoke-test.sh` passou a executar `scripts/dogfood.sh`, tornando os fixtures parte do contrato estático do plugin.

**Validador endurecido novamente:**
`scripts/validate.sh` agora exige a presença de `scripts/dogfood.sh`, `fixtures/dogfooding/scenarios.json` e dos três fixtures principais.

**Documentação atualizada:**
`README.md` e `docs/DOGFOODING.md` agora apontam para o pack local, os caminhos dos fixtures e os comandos oficiais de validação e impressão dos prompts.

## [5.22.0] - 2026-04-02 — Runtime policy central, fallback matrix, checkpoint/resume e SEP resiliente

### Added

**`runtime-policy.yaml` como fonte única de verdade operacional:**
O plugin agora centraliza budgets de retry, classificação de severidade, fallback matrix, regras de checkpoint/resume e métricas de confiabilidade em `plugins/claude-tech-squad/runtime-policy.yaml`.

**Checkpoint/resume nos workflows principais:**
`/discovery`, `/implement` e `/squad` agora definem checkpoints explícitos, emitem `[Checkpoint Saved]` e podem retomar de checkpoints anteriores com `[Resume From]` quando o contexto não mudou materialmente.

**SEP log para `/squad`:**
O workflow end-to-end completo agora grava `ai-docs/.squad-log/{timestamp}-squad-{run_id}.md`, incluindo `runtime_policy_version`, `checkpoint_cursor`, `fallback_invocations`, `teammate_reliability` e `release_result`.

### Changed

**Falha dupla agora consulta fallback antes de abrir gate:**
Os protocolos de falha silenciosa em `/discovery`, `/implement` e `/squad` passaram a consultar a fallback matrix antes de pedir decisão do usuário. Isso reduz abortos desnecessários e evita retry cego.

**Budgets e loops críticos conectados à política central:**
Review, QA, conformance, quality bench e UAT agora documentam explicitamente o uso da runtime policy para retries, fallback e retomada.

**`/factory-retrospective` enriquecido com métricas de resiliência:**
O retrospective agora lê `checkpoint_cursor`, `resume_from`, `fallback_invocations` e `teammate_reliability`, permitindo medir onde a esteira quebra, retoma e substitui agentes.

**Validação e smoke test endurecidos novamente:**
`scripts/validate.sh` e `scripts/smoke-test.sh` agora falham se faltarem `runtime-policy.yaml`, se os orquestradores perderem `Runtime Resilience Contract` ou `Checkpoint / Resume Rules`, se o `/squad` perder seu SEP log, ou se a documentação de trace perder linhas de fallback/resume/checkpoint.

## [5.21.0] - 2026-04-02 — Arquitetura por perfil, especialista Hexagonal, validação mais rígida e loops fechados

### Added

**Novo agente `hexagonal-architect`:**
Hexagonal Architecture deixa de ser implícita e passa a ser uma especialização explícita. O time agora tem um especialista dedicado para Ports & Adapters quando essa escolha for deliberada, sem forçar esse estilo em todos os repositórios.

### Changed

**Arquitetura repo-aware nos agentes centrais:**
`architect`, `backend-architect`, `backend-dev`, `tdd-specialist`, `reviewer`, `design-principles-specialist` e `techlead` agora trabalham com `{{architecture_style}}` em vez de impor Hexagonal como padrão universal. O fluxo passa a preservar o padrão real do repositório por default.

**`/discovery`, `/implement` e `/squad` propagam `{{architecture_style}}` e `{{lint_profile}}`:**
Os orquestradores agora extraem essas variáveis e as repassam para arquitetura, implementação, review e conformance. Isso torna a squad mais assertiva em stacks heterogêneas.

**`/implement` com budgets explícitos de retry:**
Review, QA, conformance e UAT agora têm limites e gates formais, eliminando loops abertos no workflow de implementação.

**Validador endurecido:**
`scripts/validate.sh` agora falha se:
- `MANUAL.md` estiver fora da versão do plugin
- qualquer agente fora do `incident-manager` expuser a tool `Agent`
- qualquer `subagent_type` sair do namespace `claude-tech-squad:*`
- qualquer agente não tiver `Result Contract`
- `discovery`, `implement` ou `squad` perderem `Preflight Gate` ou `Agent Result Contract`

**Preflight gate nos workflows principais:**
`/discovery`, `/implement` e `/squad` agora emitem preflight explícito com `execution_mode`, `architecture_style`, `lint_profile` e `docs_lookup_mode` antes de criarem times ou iniciarem fases.

**Agent Result Contract padronizado:**
Todos os agentes agora terminam com um bloco `result_contract`, usado como critério estrutural no protocolo de retries. Isso torna falha silenciosa e output inválido mais fáceis de detectar.

**Context7 com fallback formal:**
O padrão de documentação deixa de ser "mandatory or fail" e passa a ser "Context7 first, repository fallback". Se Context7 estiver indisponível, o agente declara fallback e segue com evidência do repositório + assumptions explícitas.

**Smoke test e dogfooding guide:**
Adicionados `scripts/smoke-test.sh` e `docs/DOGFOODING.md` para validar contratos estáticos, cenários layered, hexagonal e hotfix, e ausência de regressões documentais.

### Fixed

**`/hotfix` usava `subagent_type = "code-debugger"` fora do namespace do plugin:**
O root-cause step agora usa um subagente válido do próprio plugin.

**Exposição indevida da tool `Agent` em agentes não-orquestradores:**
`analytics-engineer`, `code-quality`, `cost-optimizer`, `devops`, `observability-engineer`, `platform-dev` e `sre` deixaram de expor `Agent`, alinhando runtime com a regra documental de que apenas `incident-manager` pode fan-outar agentes diretamente.

## [5.20.0] - 2026-03-31 — Segunda auditoria: release failure protocol, feature_slug, pm-uat conformance, squad mappings completos

### Fixed

**`/release` — Teammate Failure Protocol adicionado:**
O único skill que spawna agentes sem Teammate Failure Protocol. Adicionada seção completa com detecção de falha silenciosa, re-spawn automático e gate [R]/[S]/[X] ao usuário na segunda falha consecutiva.

**`/discovery` — `{{feature_slug}}` extraído no Step 1 (antes de qualquer uso):**
`feature_slug` era usado em Step 12b (feature flag), Step 13b (ADR paths) e Step 14 (SEP log) mas nunca era definido. Agora extraído no Step 1 como kebab-case do request do usuário, disponível em todo o run.

**`/implement` — `pm-uat` recebe `{{conformance_output}}` do TechLead Conformance Audit:**
PM UAT validava ACs contra `qa_output` e `quality_bench_output` mas não contra `conformance_output`. Agora recebe os três, com instrução explícita de mapear cada AC para evidência + PASS/MISSING.

**`/squad` — Mapeamentos Phase 1 completos (specialist batch + quality baseline batch):**
Tabela de mapeamentos Phase 1 continha apenas 11 agentes da chain principal. Specialist batch (16 agentes: backend-arch, frontend-arch, api-designer, data-arch, ux-designer, devops, ci-cd, dba, ai-engineer, rag-engineer, etc.) e quality baseline batch (5 agentes: security-baseline, privacy-baseline, compliance-baseline, perf-baseline, observability-baseline) agora têm mapeamentos explícitos name→subagent_type.

## [5.19.0] - 2026-03-31 — Quality Bench em /refactor, reviewer gates em /multi-service e /migration-plan, SEP logs completos, contexto do docs-writer, feature flag antes do TDD

### Added

**`/refactor` — Quality Bench (Step 7b) após reviewer APPROVED:**
Código refatorado agora passa por security-reviewer, privacy-reviewer, performance-engineer e code-quality antes de ser considerado pronto. Issues BLOCKING reenviam para o agente de implementação com mandato de correção. Sem essa gate, código refatorado saía sem auditoria de segurança/privacidade/perf.

**`/multi-service` — Reviewer Gate (Step 7b) após SRE e antes do delivery package:**
Reviewer agora valida contratos cross-service, sequência de deploy, estratégia de rollback e plano de testes de integração antes de o pacote de entrega ser gerado. Issues identificados são resolvidos com o integration-engineer ou architect antes de avançar.

**`/migration-plan` — Reviewer Gate (Step 6b) e SEP log:**
Reviewer agora valida scripts de rollback, ordenação de migrations, steps de validação de dados e operações irreversíveis antes de salvar o plano. SEP log adicionado ao final — permite que `/factory-retrospective` rastreie histórico de migration plans.

**`/bug-fix` — SEP log (Step 6b):**
Cada bug fix agora grava log estruturado em `ai-docs/.squad-log/` com root cause, arquivos alterados, evidência de teste e resultado do reviewer. `/factory-retrospective` pode agora detectar padrões de bugs recorrentes.

**`/cloud-debug` — SEP log (Step 7b):**
Diagnósticos de produção agora são registrados em `ai-docs/.squad-log/` com severidade, hipótese de root cause, serviços afetados e se escalou para hotfix. Garante rastreabilidade de todos os incidentes investigados.

**`/implement` — docs-writer recebe contexto completo (Step 8):**
docs-writer agora recebe `{{acceptance_criteria}}`, `{{test_plan}}`, `{{qa_output}}` e `{{conformance_output}}` além da implementação e arquitetura. Permite documentar o mapeamento AC → comportamento implementado → teste que cobre.

**`/implement` — extração de variáveis no Step 1:**
`{{feature_slug}}`, `{{acceptance_criteria}}`, `{{test_plan}}` e `{{architecture}}` agora são extraídos do blueprint no Step 1 antes de qualquer spawn. Elimina o `{{feature_slug}}` undefined no SEP log e garante que todos os agentes downstream recebem essas variáveis.

**`/discovery` — Feature Flag Assessment movido para Step 12b (antes do TDD Specialist):**
Feature Flag Assessment executava após o TDD Specialist, impedindo que testes flag-gated fossem planejados. Agora roda antes (Step 12b), passa `{{feature_flag_strategy}}` para o TDD Specialist, que inclui ciclos red-green para flag=false e flag=true quando necessário.

## [5.18.0] - 2026-03-31 — Code quality em todos os fluxos e resolução obrigatória de issues do Quality Bench

### Added

**`/implement` e `/squad` — Quality Bench Issue Resolution Loop (Step 7b):**
Após todos os agentes do Quality Bench retornarem, os findings agora são classificados por severidade: **BLOCKING** (vulns de segurança OWASP, vazamento de PII, violações de privacidade, erros de lint que quebram CI, falhas WCAG A/AA) e **WARNING** (regressões de performance, riscos de integração, dívida de qualidade). Se houver issues BLOCKING: os agentes de implementação relevantes são re-spawnados com mandato de correção, e apenas os reviewers que sinalizaram o problema são re-executados — max 2 ciclos de fix. Se após 2 ciclos ainda houver BLOCKING: gate ao usuário `[A]ccept com tech debt documentado / [X]Abort`. Se apenas WARNINGs: summary apresentado ao usuário com `[A]ccept / [F]ix before advancing`. Garante que issues reais encontrados pelos revisores especializados não sejam silenciosamente ignorados.

**`/hotfix` Step 8 — Security risk fix loop:**
Quando security-reviewer retorna RISK, agora há obrigatoriedade de correção antes de avançar. O agente de implementação é re-spawnado com o issue de segurança como mandato, e o security-reviewer é re-executado para confirmar CLEAR. Se RISK persistir após tentativa: gate ao usuário `[A]ccept risk (documentar) / [X]Abort`.

**`/implement`, `/squad`, `/bug-fix`, `/hotfix` — code-quality e lint em todos os fluxos de código:**
Todos os workflows que geram código agora incluem o agente `code-quality` com `{{lint_command}}` detectado no Step 0. Bug-fix tem Lint Gate explícito após QA PASS. Hotfix inclui lint check inline no agente de implementação. Quality Bench do /implement e /squad inclui `code-quality` como membro permanente.

## [5.17.0] - 2026-03-31 — Contexto acumulado completo, ai_feature determinístico, especialistas estruturados, fallback de comandos

### Fixed

**`/discovery` — Architect e TechLead recebem contexto acumulado completo:**
Architect recebia apenas `{{planner_output}}` e `{{po_output}}`, perdendo o contexto de produto do PM e as regras de domínio do BA. TechLead igualmente. Ambos agora recebem `{{pm_output}}` e `{{ba_output}}` além dos demais outputs — eliminando redesenho de contexto e inconsistências arquiteturais por falta de informação de produto.

**`/squad` — `ai_feature` com default explícito e gate quando ambíguo:**
`ai_feature` nunca tinha default — se o grep não encontrava nada, a variável ficava undefined e o bench de AI nunca era ativado. Agora: default `false`, só vira `true` se grep retorna resultados. Se detecção é ambígua: gate ao usuário `[Y]es / [N]o` antes de spawnar qualquer agente de AI.

**`techlead` agent — `### Specialists Required` com nomes exatos:**
O TechLead listava especialistas em campo livre (`Specialist Inputs Needed`) sem formato definido. Discovery Step 9 dependia disso para spawn — mas sem estrutura, o orquestrador interpretava nomes arbitrários. Agora TechLead retorna `### Specialists Required` com lista de nomes exatos do conjunto válido de agentes e razão por especialista.

**`/implement` Step 0 — gate quando comandos não detectados:**
Se nenhum signal file (`Makefile`, `package.json`, `pyproject.toml`, etc.) continha targets reconhecíveis, `{{test_command}}` ficava undefined e agentes rodavam comandos errados silenciosamente. Agora: emite `[Gate] Commands Unknown` e bloqueia todos os spawns até o usuário confirmar os comandos manualmente.

## [5.16.0] - 2026-03-31 — Workflow hardening: max retries, contexto de projeto, gate criteria, batch tracking

### Fixed

**`/squad` e `/implement` — max_retries em todos os loops:**
Reviewer (max 3 ciclos), QA (max 2), Conformance Audit (max 2) e UAT (max 2) agora têm teto de iterações. Após o limite: gate ao usuário com `[A]ccept as-is / [X]Abort`. Elimina loops infinitos.

**`/implement` — `{{test_command}}` e `{{build_command}}` injetados nos agentes de implementação:**
Comandos detectados no Step 0 agora são passados explicitamente no prompt de cada agente de implementação (backend-dev, frontend-dev, platform-dev). Agentes não inferem mais `pytest`, `npm test` etc. — usam o comando real do projeto.

**`/implement` — techlead-audit com output format estruturado e `[Teammate Done]`:**
O Step 6b (Conformance Audit) agora exige output format com seções obrigatórias: `Verdict`, `Workstream Coverage`, `Architecture Violations`, `TDD Compliance`, `Requirements Traceability`, `Gaps`. O orquestrador valida a estrutura antes de avançar e emite `[Teammate Done] techlead-audit`.

**`/bug-fix` — TechLead root cause com output format estruturado:**
TechLead no bug-fix agora retorna: `Root Cause`, `Affected Files`, `Fix Strategy`, `Scope Assessment`, `Escalation`. Elimina o problema de `{{affected_files}}` undefined no agente de implementação downstream.

**`/discovery` — Gates 1–4 com pass/fail criteria objetivos:**
Cada gate agora tem checklist de critérios de aprovação (ex: Gate 1 — mínimo 3 ACs mensuráveis, escopo delimitado, métricas observáveis). Se usuário rejeitar: instrução explícita de qual gap comunicar antes de re-spawn.

**`/discovery` — Batch completion tracking em specialist-bench e quality-baseline:**
Após `[Batch Spawned]`, agora há wait explícito com `[Batch Completed] N/N agents returned`. Batches paralelos não avançam mais sem confirmação de que todos os agentes retornaram.

## [5.15.0] - 2026-03-31 — Teammate Failure Protocol universal em todos os 16 skills com agentes

### Added

**Teammate Failure Protocol — todos os 16 skills que spawnam agentes:**
Adicionada seção `## Teammate Failure Protocol` em `discovery`, `squad`, `implement`, `multi-service`, `iac-review`, `pr-review`, `security-audit`, `hotfix`, `bug-fix`, `refactor`, `onboarding`, `llm-eval`, `migration-plan`, `incident-postmortem`, `cloud-debug` e `prompt-review`. O protocolo define: (1) detecção de falha silenciosa (resposta vazia, erro ou output sem estrutura esperada); (2) re-spawn automático na primeira falha; (3) gate ao usuário com opções [R]etry / [S]kip / [X]Abort na segunda falha consecutiva; (4) aviso explícito que skip em agente sequencial degrada TODOS os agentes downstream; (5) agentes de batch podem ser skipped individualmente sem bloquear o lote, mas o risco é registrado no relatório final; (6) nenhum step avança até todos os teammates do step atual terem retornado output válido, sido explicitamente skipped, ou o run ter sido abortado.

**`/discovery` skill — `[Teammate Retry]` adicionado ao Operator Visibility Contract:**
O discovery não emitia `[Teammate Retry]` no contrato de visibilidade. Adicionado para consistência com squad e implement.

## [5.14.0] - 2026-03-31 — TechLead Conformance Audit obrigatório após QA em /implement e /squad

### Added

**`/implement` skill — Step 6b: TechLead Conformance Audit (gate obrigatório):**
Adicionado step `techlead-audit` entre QA PASS e Quality Bench. O TechLead audita: (1) cobertura de workstreams — todos os workstreams do plano de execução foram implementados; (2) conformidade arquitetural — o código segue as decisões de arquitetura (camadas Hexagonais, boundaries de DB, contratos de API); (3) TDD compliance — testes falhantes foram escritos antes do código de produção em cada ciclo; (4) rastreabilidade de requisitos — cada critério de aceitação mapeia para comportamento implementado e teste passando. Gate: CONFORMANT avança para Quality Bench; NON-CONFORMANT retorna com gaps específicos → re-implementação → re-review → re-QA → re-audit.

**`/squad` skill — Phase 2: TechLead Conformance Audit adicionado ao fluxo:**
Fluxo de Phase 2 atualizado para incluir `techlead-audit` (subagent_type: `techlead`) entre QA e Quality Bench, com mapeamento explícito no registro de teammates e no execution log.

## [5.13.0] - 2026-03-31 — fix: agent name resolution em /squad + TDD Mandate obrigatório em todos os agentes de implementação

### Fixed

**`/squad` skill — resolução de agentes com alias curto (Phase 1 e Phase 2):**
O template genérico `subagent_type="claude-tech-squad:<role>"` era aplicado com nomes curtos que não existem como agentes válidos, causando erro "Agent not found" ao spawnar teammates. Corrigido adicionando tabelas de mapeamento explícito (name → subagent_type) para todas as fases. Aliases afetados: `ba` → `business-analyst`, `design-principles` → `design-principles-specialist`, `tdd-impl` → `tdd-specialist`, `security-rev` → `security-reviewer`, `privacy-rev` → `privacy-reviewer`, `perf-eng` → `performance-engineer`, `access-rev` → `accessibility-reviewer`, `integ-qa` → `integration-qa`, `jira-confluence` → `jira-confluence-specialist`, `pm-uat` → `pm`.

**`/onboarding` skill — agente de security audit inexistente:**
Step 5 referenciava `claude-tech-squad:security-auditor` que não existe no squad. Corrigido para `claude-tech-squad:security-reviewer`.

### Changed

**`frontend-dev` agent — TDD Mandate adicionado:**
O agente não tinha seção de TDD Mandate explícita, apenas um campo de output `### Tests Written (TDD)`. Adicionado TDD Mandate com ciclo red-green-refactor por camada (component/unit → integration/e2e), bloqueando implementação antes de testes falhantes.

**`platform-dev` agent — TDD Mandate adicionado:**
O agente não tinha nenhuma referência a TDD. Adicionado TDD Mandate com ciclo red-green-refactor por camada (unit com mocks de fila/serviço externo → integration), e campo `### Tests Written (TDD)` no Handoff Protocol.

**TDD Mandate adicionado a 9 agentes de implementação restantes:**
Os agentes `ai-engineer`, `data-engineer`, `integration-engineer`, `security-engineer`, `search-engineer`, `growth-engineer`, `devex-engineer`, `ml-engineer` e `rag-engineer` não tinham nenhuma referência a TDD. Todos receberam seção `## TDD Mandate` com regra red-green-refactor, proibição de código de produção antes de teste falhante, e instrução de mock para dependências externas em testes unitários.

## [5.12.1] - 2026-03-31 — /implement: mandatory quality bench completion checks and failure recovery

### Fixed

**`/implement` — mandatory quality bench completion checks:**
Quality Bench steps lacked explicit completion checks, allowing the orchestrator to advance to the docs/UAT phase before all quality bench agents had returned. Added mandatory wait and completion verification after each parallel quality bench batch, plus failure recovery steps: if a quality bench agent returns empty output, re-spawn once; if it fails again, present `[R]etry / [S]kip / [X]Abort` gate. Prevents silent quality bench bypass.

## [5.12.0] - 2026-03-25 — /bug-fix: perfumaria guard e critérios de blocker no reviewer

### Changed

**`/bug-fix` skill — PERFUMARIA GUARD (Step 4 — backend-dev/frontend-dev):**
O prompt do agente de implementação agora proíbe explicitamente qualquer melhoria cosmética ou estrutural que não seja a causa direta do bug: extração de helpers, eliminação de duplicação, renomeação, reorganização de funções, refactors de SRP/DRY. O diff de um bug fix deve ser a menor mudança possível que faz o teste falhar passar. Refactors sugeridos pelo reviewer devem ser adiados — nunca implementados sob um commit de bug fix.

**`/bug-fix` skill — critérios de BLOCKER no reviewer (Step 6):**
O reviewer agora recebe critérios explícitos que separam findings bloqueantes de não-bloqueantes. CHANGES REQUESTED só é permitido por: fix não resolve a causa raiz, regressão introduzida, crash, estado compartilhado corrompido, ou teste não passa. DRY violations, extração de helper, estilo, e micro-otimizações de performance são sempre LOW/NIT e nunca bloqueiam APPROVED. O workflow aplica somente findings bloqueantes ao iterar; sugestões de melhoria são ignoradas.

## [5.11.0] - 2026-03-25 — Context7 obrigatório em todos os 60 agentes

### Changed

**Documentation Standard — Context7 Mandatory** (todos os 60 agentes):
Todo agente da squad agora é obrigado a consultar documentação atualizada via Context7 antes de usar qualquer biblioteca, framework ou API externa — independente da stack. O fluxo mandatório é: (1) resolver o ID da lib com `resolve-library-id`, (2) buscar a documentação relevante com `query-docs`. Se o Context7 não tiver documentação para a lib, o agente deve declarar explicitamente e sinalizar suposições. Aplica-se a: npm, PyPI, Go modules, Maven, SDKs de cloud (AWS, GCP, Azure), frameworks (Django, React, Spring, Rails, etc.), drivers de banco, e qualquer integração de terceiros. Elimina o uso de assinaturas de API, nomes de métodos e comportamentos default baseados em dados de treinamento.

## [5.10.0] - 2026-03-25 — /multi-service e /iac-review: pipeline completa para sistemas distribuídos e infraestrutura

### Added

**`/multi-service` skill** (novo):
Coordena o delivery de features que atravessam múltiplos repositórios e serviços. Mapeia o grafo de dependências entre serviços, analisa mudanças de contrato (REST, gRPC, eventos, schemas), detecta breaking changes e produz estratégia de versionamento, gera sequência de deploy segura (staging → produção em ordem de dependência), e avalia blast radius por serviço. Spawna `integration-engineer` para análise de contratos, `architect` para design cross-service (Saga, outbox, circuit breakers), `techlead` para sequência de entrega, e `sre` para blast radius e rollback. Gate obrigatório antes de qualquer deploy: todos os contract tests devem passar antes de produção.

**`/iac-review` skill** (novo):
Revisa mudanças de Infrastructure as Code antes do apply. Detecta automaticamente o stack (Terraform, Pulumi, CloudFormation, CDK, Ansible, Helm, Kubernetes). Roda análise estática (tfsec, checkov, kubesec), spawna `devops` para blast radius e ordem de apply, `cloud-architect` para segurança IAM e postura de rede (wildcard permissions, portas abertas para 0.0.0.0/0, recursos públicos sem auth), e `cost-optimizer` para estimativa de impacto de custo. Produz sequência de apply segura com checklist de pré-apply (backup, staging first, on-call). Gate que bloqueia se houver finding crítico de segurança ou blast radius HIGH sem confirmação explícita.

## [5.9.0] - 2026-03-25 — LLM Excellence: /llm-eval, /prompt-review, llm-safety-reviewer, AI auto-detection no /squad

### Added

**`/llm-eval` skill** (new):
Evaluation suite como gate de CI para features de LLM. Descobre datasets de eval existentes, detecta framework (RAGAS, DeepEval, PromptFoo), executa métricas de qualidade (faithfulness, answer_relevance, context_precision, hallucination_rate), compara contra baseline, e emite PASS/FAIL/REGRESSION. Spawna `llm-eval-specialist` para plano de evals e `rag-engineer` para review de qualidade de retrieval. CI gate bloqueia release se houver regressão acima do threshold.

**`/prompt-review` skill** (new):
Review de mudanças em prompts como code review. Faz diff do prompt atual vs. versão anterior (git), roda testes de regressão nos exemplos golden, escaneia vulnerabilidades de prompt injection (direto e indireto via documentos recuperados), estima impacto no custo de tokens, e produz veredicto APPROVED/CHANGES REQUESTED/BLOCKED. Versiona o prompt aprovado em `ai-docs/prompt-versions/`.

**`llm-safety-reviewer` agent** (new):
Especialista em segurança específica de LLM — distinto do `security-reviewer` genérico. Cobre: prompt injection direto e indireto, jailbreak resistance, tool call authorization (allowlist + human gate para operações destrutivas), PII leakage via outputs do modelo, system prompt leakage, data exfiltration em sistemas agentic, e outputs LLM usados como código executável. Inclui matriz de injection surface e tool authorization.

**AI auto-detection no `/squad`** (Step 1):
Ao iniciar, `/squad` agora detecta automaticamente uso de LLM/AI no repositório (OpenAI, Anthropic, LangChain, LlamaIndex, pgvector, etc.). Se detectado: adiciona `ai-engineer`, `rag-engineer`, `prompt-engineer` ao batch de especialistas na Phase 1; adiciona `llm-safety-reviewer` ao quality bench na Phase 2; spawna `llm-eval-specialist` para gate de evals antes da UAT.

### Changed

**`ai-engineer` agent** — expandido com LLM App Excellence Checklist: model pinning, context window budget, least privilege on context, fallback strategy, output schema validation, structured outputs, hallucination mitigation, output content filtering, token cost estimation, prompt caching, semantic caching, model routing, streaming, LLM tracing (LangSmith/Langfuse/Helicone), latency SLOs, token usage monitoring, golden dataset requirement, regression gate, agent loop safety (max_iterations, tool allowlist, human-in-the-loop gates).

**`security-reviewer` agent** — adicionada seção LLM-Specific Security Checks com scan automatizado para input interpolation vulnerabilities, tool definitions sem allowlist, e tabela de threat surface LLM.

**`rag-engineer` agent** — adicionados RAG Quality Gates: thresholds mínimos RAGAS (faithfulness ≥ 0.80, answer_relevance ≥ 0.75, context_precision ≥ 0.70), proteção contra knowledge base poisoning, embedding model version pinning, e context window safety.

## [5.8.0] - 2026-03-24 — Global Safety Contract: CI gate, staging gate, backup gate, PII safety, supply chain, .squad-log gitignore

### Changed (safety)

**Global Safety Contract expanded to all 16 skills:**
All 13 skills that were missing the Global Safety Contract now carry it. The 3 original skills (discovery, implement, squad) were also updated with new prohibited items. Every skill now explicitly prohibits: `git commit --no-verify`, `eval()` / shell injection, production deploys without staging verification, migrations without backup confirmation, and tag creation on failing CI.

**CI hard gate in `/release`:**
Step 3 (CI validation) now HARD BLOCKS release if CI status is `failure` or `cancelled`. Previously only emitted a warning. Release cannot proceed to tagging until CI is green. If CI status is unavailable, user must explicitly accept the risk at the confirmation gate (logged as `ci_unknown_override: true` in SEP log).

**Mandatory staging gate in `/hotfix`:**
Step 11 (deploy checklist) now requires staging deploy + verification before production deploy. Skipping staging requires explicit "SKIP STAGING" text from the user with a reason, which is logged in the SEP log. Per the safety contract: "even in emergencies, a staging verification catches broken deploys before they compound the incident."

**Backup verification gate in `/migration-plan`:**
New Step 5b added before the migration plan is finalized. For staging/production migrations: requires confirmed backup date/time, storage location, and restore-test status. High-risk migrations (irreversible, type changes with data loss, >1M rows) additionally require a written rollback script and confirmation it was tested.

**PII safety in `/hotfix`, `/cloud-debug`, `/incident-postmortem`:**
Global Safety Contract in these skills now explicitly requires masking tokens, email addresses, and credentials before passing log content to agents. Agents must not store PII in responses or SEP logs.

**Safety constraints injected into agent prompts:**
Implementation agent prompts in `/bug-fix`, `/hotfix`, and `/release` now carry explicit safety constraints inline — ensuring rules reach agents even when the skill-level contract is not directly visible to the spawned subagent.

**Supply chain check in `/dependency-check`:**
New Step 2b scans newly added packages for typosquatting, suspicious new packages (< 6 months old), and unusual install-time permissions. Supply chain risks surface as Critical findings alongside CVEs.

**`.squad-log/` gitignore protection in `/onboarding`:**
Step 3 now ensures `ai-docs/.squad-log/` is added to `.gitignore` during project bootstrap. Prevents SEP execution logs (which may contain CVEs and security findings) from being committed to the repository.

**Staging deploy sequence in `/release` confirmation gate:**
Step 7 confirmation gate now explicitly shows the required deploy sequence: staging first → verify → then production. Release notes template updated to include staging step in deploy checklist.

## [5.7.0] - 2026-03-24 — Proactive integrations: ADR, feature flags, load test, cost analysis, runbooks, run chains

### Added

**ADR auto-generation** (`/discovery` — Step 13b):
After blueprint confirmation, generates one Architecture Decision Record per significant tradeoff made during the discovery chain. Written to `ai-docs/{feature}/adr/ADR-NNN-{slug}.md`. No user prompt — runs automatically. Fields: context, decision, alternatives considered, consequences.

**Feature flag assessment** (`/discovery` — Step 13c):
After blueprint confirmation, evaluates whether the feature needs a rollout flag, safety flag, experiment flag, or entitlement flag. If yes, adds a Feature Flag Strategy section to the blueprint with flag name, type, default value, rollout plan, and cleanup timeline.

**Load test agent** (`/implement` — quality bench):
Conditionally spawns `performance-engineer` for load test planning when the implementation adds or modifies HTTP endpoints, message queues, or batch jobs. Produces baseline, stress, and spike test plans with ready-to-run scripts (k6, Locust, Artillery) when tools are available.

**Cost analysis on every release** (`/release` — Step 5b):
`cost-optimizer` runs automatically before the final confirmation gate on every release. Checks for N+1 queries, unthrottled external API calls, expensive async jobs, and new storage operations. Returns CLEAR or RISK. RISK findings are added to release notes and highlighted at the confirmation gate.

**Feature flag audit on release** (`/release` — Step 5c):
Before the confirmation gate, detects feature flag references in the diff and checks for pending state changes (enable, disable, remove). Adds flag management steps to the deploy checklist automatically.

**Runbook auto-generation** (`/incident-postmortem` — Step 6b):
After action items are consolidated, automatically generates an operational runbook for every P1 item. Written to `ai-docs/runbook-{service}.md` (appended if exists). Each runbook section includes trigger, preconditions, step-by-step commands, verification, rollback, and escalation path. No user prompt — runs automatically.

**Post-mortem prompt after hotfix** (`/hotfix` — Step 12b):
After the deploy checklist gate, always prompts: "Quer iniciar o post-mortem agora? [S/N]". If yes, passes `parent_run_id` and pre-fills context. If no, records `postmortem_recommended: true` in the SEP log so `/factory-retrospective` detects unreviewed incidents.

**`parent_run_id` in SEP logs** (all skills):
All SEP logs now carry a `parent_run_id` field. Enables `/factory-retrospective` to reconstruct full run chains: `discovery → implement → hotfix → incident-postmortem`. Also tracks `adrs_generated`, `feature_flag_required`, `load_test_run`, `runbook_generated` fields.

**Hotfix-without-postmortem detection** (`/factory-retrospective`):
Detects `hotfix` logs with `postmortem_recommended: true` that have no matching `incident-postmortem` log via `parent_run_id`. Surfaces as "unreviewed incidents" in the retrospective report.

**Run chain reconstruction** (`/factory-retrospective`):
Groups SEP logs by `parent_run_id` to build full incident/feature chains. Makes it possible to see: "this hotfix originated from this feature, caused this incident, led to this post-mortem, produced these action items".

## [5.6.0] - 2026-03-24 — /onboarding, /release, /incident-postmortem, /refactor

### Added

**`/onboarding` skill** (new):
Bootstraps a new repository for squad usage. Detects stack from project files, creates `ai-docs/` structure with SEP log directory, generates a `CLAUDE.md` template with detected commands, runs initial security and dependency baseline scans, and produces a `ai-docs/project-baseline-YYYY-MM-DD.md` with health summary and recommended first steps. First command to run in any new repo.

**`/release` skill** (new):
Standalone release preparation. Builds a categorized change inventory from git log and merged PRs, validates CI/CD status, spawns `release` agent for rollback plan and deploy checklist, spawns `sre` for blast radius assessment, generates internal and user-facing release notes, creates the version tag, and optionally publishes a GitHub release. Confirmation gate before tag creation. NO-GO from release agent or SRE halts the workflow.

**`/incident-postmortem` skill** (new):
Structured blameless post-mortem after production incidents. Reconstructs timeline from git history and user-provided artifacts, spawns `incident-manager` for root cause + 5-whys + contributing factors analysis, spawns `sre` for reliability and observability gap assessment, generates prioritized action items (P1/P2/P3), and produces a shareable post-mortem document at `ai-docs/postmortem-YYYY-MM-DD-{slug}.md`. Completes the incident lifecycle started by `/hotfix` and `/cloud-debug`.

**`/refactor` skill** (new):
Test-guarded incremental refactoring. Spawns `design-principles-specialist` for analysis and step-by-step plan, writes characterization tests that lock current behavior before any code changes, executes each refactor step individually with test verification, rolls back or gates on test failures, and runs `reviewer` on the final result. Core rule: behavior does not change — if behavior must change, escalate to `/squad`.

## [5.5.0] - 2026-03-24 — UAT rejection loop, coverage gate, /pr-review, /hotfix, cache sync

### Added

**`/pr-review` skill** (new):
Full pull request review workflow. Fetches the PR diff, detects relevant specialist reviewers from changed files (reviewer, security-reviewer, privacy-reviewer, performance-engineer, accessibility-reviewer, api-designer, dba), spawns them in parallel, consolidates findings, presents summary, and posts inline review threads to GitHub via the API. Uses `--input` with a JSON file to avoid the HTTP 422 array serialization bug from `--field`. Writes SEP log on completion.

**`/hotfix` skill** (new):
Emergency fix workflow for production breaks. Intake gate → stack detection → hotfix branch → code-debugger root cause analysis → root cause confirmation gate → minimal patch → reviewer gate → optional security spot-check → commit + PR → deploy checklist. Faster than `/bug-fix` for known breaks. Escalate to `/squad` if fix requires more than 5 files or reveals a design flaw.

**UAT rejection loop** (`implement`):
When PM returns REJECTED, the workflow no longer silently stops. The orchestrator extracts the specific gaps, presents them to the user with options [R]e-queue or [S]kip, and if re-queued, spawns the relevant implementation agents again with the rejection gaps as context. Increments `retry_count` in the SEP log.

**Coverage gate** (`implement` — Step 9b):
Between QA PASS and PM UAT, a new coverage gate checks test coverage delta. If coverage dropped, the gate presents uncovered files and blocks UAT until the user chooses [C]ontinue anyway or [T]est more (re-runs QA with coverage gap as context). Gate is skipped silently when no coverage tool is available.

**Cache sync after retrospective recommendations** (`factory-retrospective` — Step 7b):
After applying approved skill changes, the retrospective detects the installed plugin cache path and copies modified SKILL.md files automatically. If the cache is not found, emits a warning with the reinstall command.

### Changed

- `implement`: step numbering updated — coverage gate is Step 9b, UAT re-queue loop is inserted after Step 10

## [5.4.0] - 2026-03-24 — Squad Execution Protocol (SEP): Observability, Continuity, and Remediation Contracts

### Added

**Squad Execution Protocol (SEP)** — four stack-agnostic contracts that close the observability and continuity gaps identified in the factory retrospective. All changes are additive new steps in existing skills; no existing behavior removed.

**Contrato 1 — Execution Log** (`discovery`, `implement`, `security-audit`, `dependency-check`):
Every skill now writes a structured YAML-frontmatter log entry to `ai-docs/.squad-log/` on completion. Logs include: `skill`, `timestamp`, `status`, `retry_count`, `gates_blocked`, `uat_result`, `implement_triggered`, `output_artifact`. The `factory-retrospective` reads these logs as its primary data source instead of inferring patterns from git history.

**Contrato 2 — Remediation Tasks** (`security-audit`, `dependency-check`):
Both audit skills now generate a companion `ai-docs/security-remediation-YYYY-MM-DD.md` and `ai-docs/dependency-remediation-YYYY-MM-DD.md` file with checkbox task lists organized by severity. The `factory-retrospective` counts `- [ ]` vs `- [x]` items across runs to compute remediation closure rate.

**Contrato 3 — Discovery → Implement Bridge Gate** (`discovery`):
After the blueprint confirmation gate, `/discovery` now presents an explicit "Quer iniciar a implementação agora? [S/N]" prompt. If yes, `/implement` is invoked immediately with the blueprint path. If no, the execution log records `implement_triggered: false`, which the `factory-retrospective` surfaces as an orphaned discovery.

**Contrato 4 — Task Status Protocol** (`implement`):
Each implementation agent now returns a mandatory `Completion Block` (task name, status, files changed, test command result) before the orchestrator advances to the Reviewer phase. Blocks are aggregated in the execution log.

**Stack Command Detection** (`implement` — Step 0):
Before any teammate is spawned, `/implement` detects the project's real commands from `Makefile`, `package.json`, `pyproject.toml`, `pom.xml`, or `build.gradle`. Detected commands — or overrides from `CLAUDE.md` — are injected into every implementation agent prompt. Agents never infer test/migrate/lint commands; they receive them explicitly.

**`factory-retrospective` SEP-aware Step 1**:
Step 1 now reads `ai-docs/.squad-log/` as the primary source. Computes: average `retry_count` per skill, orphaned discovery rate, open remediation items, `uat_result: REJECTED` rate. Falls back to git/markdown inference when no SEP logs exist (backward compatible with pre-5.4.0 runs).

### Fixed

- `factory-retrospective`: was blind to teammate-mode runs (no persistent artifacts). Now reads `.squad-log/` which is written by all skills regardless of teammate vs inline mode.

## [5.3.0] - 2026-03-24 — Sequencing Model Consistency: 40 Agent Handoff Protocol Rewrites

### Changed

**Handoff Protocol rewrite across 40 of 59 agents.** Every agent that previously used `Agent tool` in its Handoff Protocol to chain directly to the next agent (Model B) has been rewritten to return structured output to the orchestrator (Model A). This eliminates double-execution risk, context loss, and safety contract bypass paths.

**Subtypes fixed:**
- **B1 — Forward-chain agents (26):** Handoff Protocol invoked `Agent tool` with `subagent_type` to spawn the next agent directly. Rewritten to return output to the orchestrator.
- **B2 — Return-via-Agent-tool agents (12):** Used `Agent tool` in the Handoff Protocol to return results. Rewritten to plain structured output.
- **B3 — Implicit chain agents (2):** `mobile-dev` and `data-engineer` had implicit chaining patterns. Rewritten to return to orchestrator.
- **techlead:** Full strip of orchestration logic — now a pure specialist. No longer spawns or sequences other agents.

**Exemptions:**
- `incident-manager`: Retains `Agent tool` usage — legitimate fan-out pattern for coordinating multiple specialists during active incidents.

**Additional fixes:**
- `cost-optimizer`: Mid-body DBA delegation via `Agent tool` converted to recommendation text. Cost-optimizer now recommends DBA involvement instead of spawning it.
- `scripts/validate.sh`: New self-chaining detection rule — fails if any agent file (except `incident-manager`) contains `subagent_type:` references.

### Fixed

- `docs/GETTING-STARTED.md`: Agent count corrected from 55 to 59. Roster table updated with 3 missing agents: `solutions-architect`, `growth-engineer` (Business & Growth), and `developer-relations` (Docs / DX).
- `CHANGELOG.md`: v5.2.0 entry arithmetic corrected from "58 required agents" to "59 required agents".

## [5.2.2] - 2026-03-24 — Safety Guardrails: Absolute Prohibitions — second pass (7 more agents)

### Changed

**Absolute Prohibitions blocks** added to 7 more agents after a full audit of every agent in the roster:

- `chaos-engineer`: NEVER run experiments in production without confirmed maintenance window, on-call present, and documented abort procedure. NEVER inject faults that cause data loss. Staging is the default — production requires explicit confirmation per experiment.
- `security-engineer`: NEVER revoke production tokens without replacement ready. NEVER disable auth or CORS protections. NEVER add WAF rules to production without staging validation. NEVER log or hardcode secrets.
- `cost-optimizer`: NEVER delete storage buckets, cloud databases, or production instances. NEVER disable monitoring to save cost. All deletions require DevOps/SRE verification before execution.
- `ml-engineer`: NEVER promote models to production without rollback procedure. NEVER delete model versions serving production traffic. NEVER overwrite training datasets without a versioned backup. Model deployment follows the same standards as a code release.
- `mobile-dev`: NEVER submit directly to App Store or Play Store production track. NEVER roll out to 100% of users without staged rollout. NEVER hardcode secrets. NEVER disable certificate pinning as a workaround. App store submissions are irreversible for users.
- `frontend-dev`: NEVER commit to main/develop directly. NEVER merge without approved review. NEVER hardcode credentials. NEVER disable CSP or XSS protections as a workaround.
- `techlead`: As execution authority, NEVER authorize any specialist to take a prohibited action without explicit written user confirmation. Surfaces all such decisions to the user with a clear risk summary before proceeding.

**Full audit verdict:** 13 agents now have Absolute Prohibitions (dba, devops, ci-cd, release, incident-manager, data-engineer, backend-dev, platform-dev, sre, chaos-engineer, security-engineer, cost-optimizer, ml-engineer, mobile-dev, frontend-dev, techlead = 16 total). The 3 skill orchestrators (discovery, implement, squad) carry the Global Safety Contract. All remaining agents are pure review/design/analysis with no execution authority.

## [5.2.1] - 2026-03-24 — Safety Guardrails: Absolute Prohibitions across all dangerous agents

### Added

**Absolute Prohibitions blocks** added to every agent and orchestrator that can take destructive actions. Each block explicitly lists forbidden operations and requires written user confirmation before proceeding — regardless of incident urgency or business pressure.

**Agents hardened:**
- `dba`: DROP DATABASE, DROP TABLE, TRUNCATE, backup deletion, destructive migrations without rollback
- `devops`: tsuru app-remove, cloud resource deletion (EC2, RDS, S3, clusters), rm -rf, terraform destroy, stopping prod services
- `ci-cd`: merge without approved PR, force push to protected branches, disable quality gates, skip hooks with --no-verify
- `release`: deploy without tested rollback plan, skip staging validation, merge without PR approval
- `incident-manager`: all of the above, plus queue deletion and token revocation — explicitly states that incident urgency does not override these rules
- `data-engineer`: DROP TABLE/DATABASE, S3/GCS bucket deletion, Kafka/Kinesis topic deletion, dbt --full-refresh on prod, disabling CDC streams
- `backend-dev`: destructive migrations without rollback script, committing directly to main/develop, removing auth as a workaround, hardcoding secrets
- `platform-dev`: purging message queues with unprocessed messages, terminating workers with active tasks, removing feature flags, deleting cron schedules
- `sre`: approving deployment without rollback plan, disabling SLO alerting, approving unsafe migrations, silencing monitoring — explicitly states business pressure does not override these rules

**Global Safety Contract** added to the 3 main skill orchestrators:
- `skills/discovery/SKILL.md`
- `skills/implement/SKILL.md`
- `skills/squad/SKILL.md`

The contract propagates to every teammate spawned by these workflows. It covers the same forbidden operations plus an explicit note: **no deadline, incident, or business pressure overrides this contract.**

## [5.2.0] - 2026-03-24 — 3 Business Agents + Hardened Validation (59 total)

### Added
- `solutions-architect`: Customer-facing technical architect for enterprise integrations, pre-sales, RFPs, and PoCs. Distinct from internal architect.
- `growth-engineer`: Experimentation infrastructure, A/B testing, feature flags, funnel instrumentation, and growth loop implementation. Distinct from analytics-engineer.
- `developer-relations`: External developer community, SDK publishing, tutorials, technical content, and developer feedback loops. Distinct from tech-writer and devex-engineer.

### Changed
- `scripts/validate.sh`: Hardened from 6 checks to full validation — now validates version consistency between `marketplace.json` and `plugin.json`, all 10 required skills, all 59 required agents (by name), frontmatter (`name:` + `description:`) on every agent and skill file, and required documentation files. Outputs agent count on success.

## [5.1.2] - 2026-03-24 — Documentation complete for v5.1

### Changed
- `docs/MANUAL.md`: updated from v4.1.0 to v5.1.1 — 55 agents, teammate mode setup, updated architecture diagrams, LLM/AI alternative flows in quick reference
- `docs/EXECUTION-TRACE.md`: added teammate mode trace examples with `[Team Created]`, `[Teammate Spawned]`, `[Gate]`, `[Batch Spawned]`, `[Teammate Done]` terminology; added tmux troubleshooting section
- `docs/OPERATIONAL-PLAYBOOK.md`: expanded from 7 to 15 scenarios — added RAG chatbot, multi-agent MCP, monitoring/observability dashboards, hybrid search, and mobile feature scenarios

## [5.1.1] - 2026-03-24 — Auto-update distribution pipeline

### Fixed
- `marketplace.json` estava travado em `4.2.0` desde a release inicial, tornando todas as versões subsequentes (`4.2.1`, `5.0.0`, `5.1.0`) invisíveis para usuários com `autoUpdate: true`. Corrigido para `5.1.0`.

### Added
- `.github/workflows/release.yml`: workflow do GitHub Actions disparado em tags `v*.*.*`. Valida o plugin, verifica consistência de versões entre `marketplace.json`, `plugin.json` e a tag, e cria um GitHub Release com as notas extraídas do `CHANGELOG.md`.
- `scripts/release.sh`: script de release em um comando. Faz bump de `marketplace.json` e `plugin.json`, valida, checa entrada no `CHANGELOG.md`, commita, cria a tag e faz push. Uso: `./scripts/release.sh 5.2.0`.
- `docs/RELEASING.md`: atualizado com o processo automatizado completo e explicação de como o `autoUpdate` funciona para os usuários.

## [5.1.0] - 2026-03-24 — 16 New Specialist Agents (55 total)

Expanded the squad from 39 to 55 agents covering LLM/AI stacks, monitoring, cloud, security, mobile, data, search, and developer experience.

### Added

**LLM / AI Specialists**
- `prompt-engineer`: Prompt design, chain-of-thought, token optimization, prompt caching, versioning, regression testing
- `rag-engineer`: Full RAG stack — chunking, embedding, vector stores, hybrid search, reranking, HyDE, RAPTOR, agentic RAG
- `agent-architect`: Multi-agent orchestration, MCP (Model Context Protocol), tool use contracts, ReAct/Plan-Execute/MRKL loops, Claude Agent SDK, LangChain/LlamaIndex/AutoGen/CrewAI
- `llm-eval-specialist`: RAGAS, DeepEval, TruLens, hallucination detection, regression suites, LLM-as-judge, production quality monitoring
- `conversational-designer`: Dialog flows, intent architecture, persona, fallback strategies, conversation memory, escalation paths
- `ml-engineer`: Fine-tuning (LoRA/QLoRA), training pipelines, MLOps, model registry, serving, drift monitoring

**Infrastructure & Operations**
- `monitoring-specialist`: Grafana, New Relic, Datadog dashboards; APM; SLO/error budget tracking; alert tuning; LLM cost and quality dashboards
- `cloud-architect`: VPC/networking topology, IAM strategy, multi-region HA, DR planning, Well-Architected review across AWS/GCP/Azure
- `security-engineer`: Implements OAuth2/OIDC/MFA, WAF rules, SAST/DAST pipeline integration, threat modeling, secrets management
- `chaos-engineer`: Fault injection, circuit breaker validation, degraded-mode testing, LLM dependency resilience, game days

**Mobile & Data**
- `mobile-dev`: React Native, Flutter, iOS (SwiftUI), Android (Compose) — offline, push, deep links, app store deployment
- `data-engineer`: ETL/ELT pipelines, Kafka, Spark, dbt, Airflow, data quality (Great Expectations), CDC, lakehouse

**Search**
- `search-engineer`: Elasticsearch/OpenSearch full-text, faceted search, relevance tuning, autocomplete, hybrid keyword+vector

**Documentation & Developer Experience**
- `tech-writer`: User guides, public API references, tutorials, customer changelogs, onboarding docs (distinct from docs-writer)
- `devex-engineer`: Local dev setup, CLI tooling, scaffolding, Makefile targets, contribution workflows, onboarding experience
- `design-system-engineer`: Component libraries, design tokens, Storybook, theming, Figma/Pencil → code contract, accessibility at component layer

## [5.0.0] - 2026-03-24 — BREAKING: TeamCreate-Based Teammate Architecture

Skills `discovery`, `implement`, and `squad` now spawn each specialist as a real Claude Code teammate via `TeamCreate` + `Agent(team_name=...)`, giving every specialist its own tmux pane. This replaces the previous inline `Agent` tool chain where all agents ran in the same process without visual separation.

### Changed
- `skills/discovery/SKILL.md`: rewritten to use `TeamCreate` + teammate spawning. Each specialist (PM, BA, PO, Planner, Architect, TechLead, specialist batch, quality batch, Design Principles, Test Planner, TDD Specialist) gets its own tmux pane. Gates remain at PO, Planner, TechLead, and TDD Specialist.
- `skills/implement/SKILL.md`: rewritten to use `TeamCreate` + teammate spawning. TDD Specialist, implementation batch, Reviewer, QA, quality bench, Docs Writer, Jira/Confluence, and PM UAT each run in their own pane. Retry loops preserved.
- `skills/squad/SKILL.md`: rewritten as the full end-to-end pipeline using a single persistent team across Discovery, Implementation, and Release phases. All 20+ specialists spawn in individual panes.

### Migration
- Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in env
- Requires `CLAUDE_CODE_TEAMMATE_MODE=tmux` in `~/.claude/settings.json` for pane visibility
- Without these env vars, teammates fall back to in-process execution

## [4.2.1] - 2026-03-24

### Fixed
- `plugin.json`: removed `skills` and `agents` arrays that caused manifest validation error ("Invalid input") in Claude Code. Skills and agents are now auto-discovered from directory structure, matching the format used in prior versions.

## [4.2.0] - 2026-03-24

### Added
- `docs/MANUAL.md`: complete technical manual covering all 10 skills, all 40 agents, full pipeline diagrams, user gates reference, and quick-reference guide

## [4.1.0] - 2026-03-24

### Added
- Handoff Protocol to all 25 remaining specialist agents — no agent is a dead end
- Architecture sub-chains: backend-architect → ai-engineer or data-architect → dba; frontend-architect → ux-designer; api-designer → integration-engineer
- Ops chain: platform-dev → devops → ci-cd → sre → release → techlead
- Quality bench reporters (all report to techlead): security-reviewer, privacy-reviewer, compliance-reviewer, accessibility-reviewer, performance-engineer, observability-engineer, analytics-engineer, integration-qa
- incident-manager orchestrates parallel sre + devops + observability-engineer; calls techlead for post-incident code fixes
- cost-optimizer calls dba for query costs; reports to sre or techlead
- code-quality reports back to reviewer
- test-automation-engineer reports to tdd-specialist or qa depending on caller

## [4.0.0] - 2026-03-24 — BREAKING: Chain-Driven Team Architecture

The squad now operates as an autonomous agent chain. Skills are entry points; agents call each other forward using the Agent tool.

Discovery chain: pm → business-analyst → po [gate] → planner [gate] → architect → techlead [gate] → specialist bench → design-principles-specialist → test-planner → tdd-specialist [gate]

Build chain: techlead → tdd-specialist → impl batch → reviewer → qa → techlead (quality) → quality bench → docs-writer → jira-confluence-specialist → pm [UAT gate]

Release chain (/squad only): release → sre

### Changed
- All key agents have Handoff Protocol sections
- Skills simplified to chain starters only
- techlead is the technical orchestrator for both blueprint and build phases
- impl agents call reviewer when done; reviewer calls qa or back to impl; qa calls techlead or back to impl

## [3.0.0] - 2026-03-24

### Changed
- All orchestrator agents use explicit Agent tool invocations
- Agents outside their scope use user-facing language to redirect, not silent absorption

## [2.9.0] - 2026-03-24

### Changed (scope deduplication)
- platform-dev: narrowed to workers, queues, tooling, integration glue
- devops: blast radius removed (→ sre); owns infrastructure config
- sre: owns blast radius, SLO, rollback, canary; delegates infra to devops, incidents to incident-manager
- qa: lint and TDD gates removed (→ reviewer); owns behavioral validation only
- observability-engineer: ops observability only; product metrics → analytics-engineer
- analytics-engineer: product analytics only; infra metrics → observability-engineer
- cost-optimizer: DB query analysis removed (→ dba); owns cloud/API/storage costs

## [2.8.0] - 2026-03-24

### Added
- Agent incident-manager: production incident orchestration — triage, severity, coordination, mitigation, post-mortem
- Agent cost-optimizer: cloud and application cost specialist

### Changed
- devops upgraded to full specialist with real tool access

## [2.7.0] - 2026-03-24

### Added
- Skill bug-fix: root cause → failing test → fix → real validation → review
- Agent code-quality: strategic quality ownership — lint config, tech debt, standards, metrics

## [2.6.0] - 2026-03-24

### Added
- Skill security-audit: real bandit / pip-audit / npm audit execution
- Skill migration-plan: data-architect + dba coordination
- Skill cloud-debug: observability-engineer + sre + techlead
- Skill dependency-check: real outdated/vulnerable dependency scanning
- Skill factory-retrospective: self-improvement via execution log analysis
- jira-confluence-specialist: real Atlassian API calls via MCP (17 tools)

### Changed
- qa and security-reviewer now execute real tools for backpressure

## [2.5.0] - 2026-03-24

### Added
- Hexagonal Architecture as default in all architecture and implementation agents
- Skill pre-commit-lint: auto-fix lint before commits
- Lint Compliance Gate in qa and reviewer
- TDD Compliance Gate in reviewer

### Changed
- TDD-first mandatory in all agents
- po: Post-Implementation Audit required before sign-off
- pm: UAT maps each AC to concrete evidence

## [2.4.0]

- /squad TDD-first by default for code changes
- Test Plan and TDD Delivery Plan required before build starts

## [2.3.0]

- Added tdd-specialist: drives development from failing tests
- Added design-principles-specialist: SOLID, Clean Architecture, Hexagonal guardrails

## [2.2.0]

- Added visible orchestration lines (phase changes, handoffs, retries, parallel batches)
- Mandatory Agent Execution Log in all workflow outputs

## [2.1.0]

- Clarified product positioning vs claude-config
- Added validation workflow, release documentation, license

## [2.0.0]

- Expanded plugin into a full specialist technology squad
