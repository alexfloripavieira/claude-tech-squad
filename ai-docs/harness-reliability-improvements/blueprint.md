# Discovery & Blueprint — Harness Reliability Bundle

## 0. Run metadata

- **run_id:** harness-reliability-improvements
- **skill:** discovery (streamlined bench)
- **skill_branch:** cts/skill/discovery-1778464208
- **base_commit:** 7ad00029a5fe51015b9d7c13fab1390ae38d7bdf
- **language_policy_applied:** pt-BR
- **bench_exceptions:**
  - business-analyst: skipped — PM brief sufficient para tooling interno; nenhum domínio de negócio a investigar.
  - po: skipped — priorização fixa via Waves A/B já definida pelo PM brief.
  - planner: skipped — feasibility resolvido pelo architect direto.
  - specialist_batch (frontend/backend/data architects): skipped — escopo é shell/python tooling interno (sem UI, sem schema de produto, sem multi-stack).
  - quality_batch (security-reviewer / privacy-reviewer / accessibility-reviewer / performance-engineer): skipped no /discovery — atuarão no /implement.
  - design-principles-specialist: skipped — sem decisões SOLID/coupling não-triviais; arquitetura é cross-cutting (lint/schema/CLI/policy).
  - test-planner: collapsed em tdd-specialist (papéis fundidos) — tdd-specialist assume planejamento de testes + escrita de testes RED.
- **cross_talk_audit:**
  - pm ↔ business-analyst: PM enviou cross-talk-note; BA não foi spawnado (exceção bench, registrada).
  - architect ↔ backend-architect: cross-talk-note enviada; ba-arch não spawnado (exceção bench).
  - architect ↔ data-architect: cross-talk-note enviada; da não spawnado (exceção bench — nenhuma mudança de schema).
  - test-planner ↔ tdd-specialist: collapsed (tdd-specialist absorveu o papel).
  - security-reviewer ↔ privacy-reviewer: not spawned (quality batch fica para /implement).
- **deferred to /implement:** Wave B (M3 CLI, M5 token cap), quality_batch (security/privacy/performance reviewers), docs page docs/RELIABILITY-CLI.md.

---

## 1. Product Definition (do PM brief)

### 1.1 Problema
A harness do claude-tech-squad acumulou 5 fragilidades operacionais que reduzem confiabilidade percebida:

1. **M1 — Watchdog kill silencioso:** `bin/watchdog.sh` envia SIGTERM/SIGKILL mas não verifica se o processo realmente morreu. Zumbis e processos uninterruptíveis passam despercebidos; SEP log declara "kill" sem evidência.
2. **M2 — SEP log sem schema:** `finalize-skill.sh` aceita qualquer YAML/MD. Campos críticos (`tokens_input`, `worktrees[]`, `language_policy_applied`) podem faltar silenciosamente, quebrando dashboard e retrospectiva.
3. **M3 — Sem CLI de reliability:** operador não tem comando rápido para ver "qual foi o último skill que falhou no gate X, com que retry budget restante". Hoje é grep manual em `ai-docs/.squad-log/`.
4. **M4 — Bypass policy não-linçado:** SKILL.md pode conter strings como "session-level approval" ou "skipping reviewer" sem qualquer gate. Bypass de reviewer em /implement (retrospectiva 2026-04-18) só foi descoberto post-mortem.
5. **M5 — Token budget só por skill:** `runtime-policy.yaml::cost_guardrails` limita orçamento total; não há cap por agente. Um specialist runaway consome 80% do budget e mata os demais sem aviso.

### 1.2 Outcome
- Watchdog que **prova** que matou ou registra `[Kill Failed]` com artefato `.kill-failed`.
- SEP log validado por jsonschema antes do commit final; falha bloqueante.
- CLI `squad-cli reliability` com subcomandos `last-failure`, `retry-budget`, `gate-health`.
- `validate.sh` linta strings de bypass; lista crescível em policy.
- Por-agente soft cap (default 0.30 do budget do skill); pressão emite warning (v1).

### 1.3 11 Acceptance Criteria (numerados)

| AC | Improvement | Statement |
|----|-------------|-----------|
| AC1 | M1 | `bin/watchdog.sh` re-verifica `kill -0 <pid>` após SIGKILL; emite `[Kill Confirmed]` ou `[Kill Failed]` + cria `.kill-failed` marker. |
| AC2 | M1 | `tests/watchdog-kill-test.sh` cobre processo normal e processo zumbi simulado (trap SIGTERM/SIGKILL ignorado). |
| AC3 | M2 | `hooks/sep-log.schema.json` exige `tokens_input`, `tokens_output`, `estimated_cost_usd`, `total_duration_ms`, `worktrees: list`, `language_policy_applied: pt-BR`. |
| AC4 | M2 | `bin/validate-sep-log.py` exit 0 em SEP válido, exit 5 + `[SEP Schema Violation]` em violação. |
| AC5 | M2 | `bin/finalize-skill.sh` invoca o validator; falha de schema aborta finalize com exit 5. |
| AC6 | M3 | `squad-cli reliability last-failure` retorna último SEP com `status: failed`. |
| AC7 | M3 | `squad-cli reliability retry-budget --skill <name>` lista budget restante por phase do `runtime-policy.yaml`. |
| AC8 | M3 | `squad-cli reliability gate-health` agrega taxa de aprovação por gate nos últimos 20 runs. |
| AC9 | M4 | `scripts/validate.sh` falha se um SKILL.md contém qualquer padrão em `runtime-policy.yaml::bypass_patterns` sem o marker `# bypass-lint: <pattern-source>`. |
| AC10 | M5 | `runtime-policy.yaml::cost_guardrails.per_agent_token_soft_cap: 0.30` declarado e lido por `cost.py`. |
| AC11 | M5 | Cruzar `soft_cap` emite `[Token Pressure]` warning no operator stream; severity=warning (v1; promote pós-telemetria). |

---

## 2. Architecture (do architect)

### 2.1 Decisões por improvement

#### M1 — Watchdog kill verify
- **Decisão:** após `kill -9 $pid`, executar `for i in 1..5; do kill -0 $pid 2>/dev/null || break; sleep 0.2; done`. Se ainda vivo, escrever `.kill-failed-${pid}` em `$CTS_WORKTREE_BASE/` e log `[Kill Failed] pid=$pid reason=uninterruptible`.
- **Alternativas descartadas:** `wait $pid` (não funciona para non-children); SIGCHLD handler (complexidade desnecessária).

#### M2 — SEP schema validation
- **Decisão:** schema JSON Schema 2020-12; validator Python (`jsonschema>=4.0`). SEP log permanece markdown, mas tem bloco frontmatter YAML que é validado.
- **Preflight check:** `/implement` preflight verifica `python3 -c "import jsonschema"`; ausente → T2.0 [setup] instala dependency.

#### M3 — Reliability CLI
- **Decisão:** novo módulo `squad-cli/squad_cli/reliability.py` com 3 funções puras; expor via `cli.py` subcomando `reliability`.
- **Storage:** lê `ai-docs/.squad-log/*.md` (frontmatter YAML) — mesma fonte do dashboard. Sem novo storage.

#### M4 — Bypass lint
- **Decisão:** `bypass_patterns` em `runtime-policy.yaml` (lista de strings literais; case-insensitive grep). `validate.sh` faz `grep -i -n` em cada SKILL.md; se match e linha não contém `# bypass-lint:` marker, falha.
- **Lista inicial:** `"session-level approval"`, `"skipping reviewer"`, `"bypass gate"`, `"override checkpoint"`.

#### M5 — Per-agent token cap
- **Decisão:** `cost.py` lê `cost_guardrails.per_agent_token_soft_cap` (float 0..1); por agent_run, se `agent_tokens / skill_budget > soft_cap`, emit warning event `[Token Pressure]`. Não aborta (v1).
- **Telemetria:** SEP log captura `token_pressure_events: []` para análise futura antes de promover a blocking.

### 2.2 File plan

| File | Op | Owner |
|------|----|-------|
| `plugins/claude-tech-squad/bin/watchdog.sh` | edit | backend-dev |
| `plugins/claude-tech-squad/bin/validate-sep-log.py` | create | backend-dev |
| `plugins/claude-tech-squad/bin/finalize-skill.sh` | edit | backend-dev |
| `plugins/claude-tech-squad/hooks/sep-log.schema.json` | create | backend-dev |
| `plugins/claude-tech-squad/runtime-policy.yaml` | edit (add `bypass_patterns`, `per_agent_token_soft_cap`) | backend-dev |
| `scripts/validate.sh` | edit (bypass lint) | backend-dev |
| `squad-cli/squad_cli/reliability.py` | create | backend-dev |
| `squad-cli/squad_cli/cli.py` | edit (subcommand) | backend-dev |
| `squad-cli/squad_cli/cost.py` | edit (soft cap) | backend-dev |
| `tests/watchdog-kill-test.sh` | create | tdd-specialist (this run) |
| `tests/sep-log-schema-test.sh` | create | tdd-specialist (this run) |
| `tests/bypass-lint-test.sh` | create | tdd-specialist (this run) |
| `tests/fixtures/skill-with-bypass.md` | create | tdd-specialist (this run) |
| `squad-cli/tests/test_reliability.py` | create (Wave B) | /implement |
| `squad-cli/tests/test_cost_pressure.py` | create (Wave B) | /implement |
| `docs/RELIABILITY-CLI.md` | create (Wave B) | docs-writer |

### 2.3 Sequencing — Waves

**Wave A (independent, parallelizable inside):**
- T1.x M1 watchdog kill verify
- T2.x M2 SEP schema + validator + finalize integration
- T4.x M4 bypass lint

**Wave B (depends on Wave A SEP schema for telemetry):**
- T3.x M3 reliability CLI (consumes validated SEP frontmatter)
- T5.x M5 per-agent token cap (writes `token_pressure_events` into SEP — schema must exist)

### 2.4 Test strategy hand-off
- Wave A red tests: 3 bash test files committed **this run** (RED state).
- Wave B red tests: 2 pytest files outlined; written in `/implement` T3.0 e T5.0.
- Integration: `smoke-test.sh` ganha invocação de `tests/*.sh` na fase pós-validate.

### 2.5 Risk register
- **R1:** jsonschema dependency ausente em ambiente operador → mitigado por preflight check + T2.0 [setup].
- **R2:** Bypass lint falso-positivo em docs/comentários legítimos → mitigado por marker `# bypass-lint:`.
- **R3:** Soft cap 0.30 pode ser apertado para skills com 1–2 agentes → mitigado por severity=warning v1 + telemetria antes de promote.
- **R4:** Watchdog kill verify em CI containers pode ser flaky se PID namespace estiver isolado → mitigado por timeout 1s total (5 × 0.2s).

### 2.6 Open questions (não-bloqueantes)
- Q1: bypass_patterns deve suportar regex no futuro? Decisão: começa literal; promover se demanda surgir.
- Q2: SEP schema deve ser versionado? Decisão: adicionar `schema_version: 1` field; alteração breaking incrementa.

---

## 3. Execution Plan (do techlead)

### 3.1 Task breakdown

| Task | Improvement | Description | Effort | Specialist | Depends on |
|------|-------------|-------------|--------|------------|------------|
| T1.0 | M1 | Read current `watchdog.sh`, identify kill sites | XS | backend-dev | — |
| T1.1 | M1 | Implement kill verify loop + `.kill-failed` marker | S | backend-dev | T1.0 |
| T1.2 | M1 | Make `tests/watchdog-kill-test.sh` pass | S | backend-dev + test-automation-engineer | T1.1 |
| T2.0 | M2 | Preflight: ensure `jsonschema` available; add to install docs | XS | backend-dev | — |
| T2.1 | M2 | Author `hooks/sep-log.schema.json` | S | backend-dev | T2.0 |
| T2.2 | M2 | Implement `bin/validate-sep-log.py` (CLI: file path → exit 0/5) | S | backend-dev | T2.1 |
| T2.3 | M2 | Wire validator into `finalize-skill.sh` | S | backend-dev | T2.2 |
| T2.4 | M2 | Make `tests/sep-log-schema-test.sh` pass | S | backend-dev | T2.3 |
| T4.0 | M4 | Add `bypass_patterns` list to `runtime-policy.yaml` | XS | backend-dev | — |
| T4.1 | M4 | Implement lint pass in `scripts/validate.sh` | S | backend-dev | T4.0 |
| T4.2 | M4 | Make `tests/bypass-lint-test.sh` pass | S | backend-dev | T4.1 |
| T3.0 | M3 | Author `squad-cli/tests/test_reliability.py` (RED) | S | backend-dev | T2.4 |
| T3.1 | M3 | Implement `squad-cli/squad_cli/reliability.py` (3 funcs) | M | backend-dev | T3.0 |
| T3.2 | M3 | Wire subcommand in `cli.py` | XS | backend-dev | T3.1 |
| T3.3 | M3 | Write `docs/RELIABILITY-CLI.md` | S | docs-writer | T3.2 |
| T5.0 | M5 | Author `squad-cli/tests/test_cost_pressure.py` (RED) | S | backend-dev | T2.4 |
| T5.1 | M5 | Add `per_agent_token_soft_cap: 0.30` to policy | XS | backend-dev | T5.0 |
| T5.2 | M5 | Implement pressure check in `cost.py` + SEP capture | M | backend-dev | T5.1 |
| Q.0 | quality | Multi-lens review: code-reviewer + security-reviewer + performance-engineer | M | reviewers | all Wave A+B |

**Total effort:** ~3 XS + 9 S + 3 M = aprox. 12-16h focused work.

### 3.2 Dependency graph

```
Wave A (parallel):
  M1: T1.0 → T1.1 → T1.2
  M2: T2.0 → T2.1 → T2.2 → T2.3 → T2.4
  M4: T4.0 → T4.1 → T4.2

Wave B (after Wave A SEP schema lands):
  M3: T2.4 → T3.0 → T3.1 → T3.2 → T3.3
  M5: T2.4 → T5.0 → T5.1 → T5.2

Quality gate Q.0: depends on all of the above
```

### 3.3 Required /implement specialists
- backend-dev (primary executor)
- test-automation-engineer (peer on test stabilization)
- code-reviewer (correctness/style/N+1)
- security-reviewer (subprocess invocation, schema injection surface)
- performance-engineer (cost.py hotpath, watchdog loop timing)
- docs-writer (RELIABILITY-CLI.md)

---

## 4. Test Plan (TDD-first)

### Wave A — RED tests committed this run

#### M1 — `tests/watchdog-kill-test.sh`
Strategy: spawn dois processos filhos numa sub-shell:
1. **Normal process:** `sleep 30 &` — receberá SIGTERM e morrerá; teste deve ver `[Kill Confirmed]`.
2. **Zumbi simulado:** processo que `trap '' TERM KILL` e loopa — após watchdog tentar matar, deve emitir `[Kill Failed]` e tocar `.kill-failed-<pid>`.

Assertions:
- `grep -q "\[Kill Confirmed\]" <output>` para PID 1
- `grep -q "\[Kill Failed\]" <output>` para PID 2
- `test -f $CTS_WORKTREE_BASE/.kill-failed-<pid2>`

RED reason: `watchdog.sh` atual não emite essas tags; teste falha.

#### M2 — `tests/sep-log-schema-test.sh`
Strategy: invoca `python3 plugins/claude-tech-squad/bin/validate-sep-log.py <fixture>` para três fixtures inline:
1. **Valid:** todos campos requeridos → expect exit 0.
2. **Missing tokens_input:** → expect exit 5 + stderr contém `[SEP Schema Violation]` + `tokens_input`.
3. **Wrong type worktrees:** `worktrees: "not-a-list"` → expect exit 5 + stderr contém `worktrees`.

RED reason: arquivo `validate-sep-log.py` não existe ainda; teste falha em ENOENT.

#### M4 — `tests/bypass-lint-test.sh`
Strategy: cria temp dir; copia `tests/fixtures/skill-with-bypass.md` para um caminho que `validate.sh` inspeciona; roda `bash scripts/validate.sh`; espera exit !=0 + stderr contém `bypass`.

RED reason: validate.sh atual não tem lint de bypass; teste falha (validate.sh passa quando deveria falhar).

### Wave B — outlines (escritos em /implement)

#### M3 — `squad-cli/tests/test_reliability.py`
- `test_last_failure_returns_most_recent_failed_sep()`
- `test_retry_budget_reads_from_policy_yaml()`
- `test_gate_health_aggregates_last_20_runs()`

#### M5 — `squad-cli/tests/test_cost_pressure.py`
- `test_pressure_warning_emitted_when_agent_exceeds_soft_cap()`
- `test_no_warning_below_soft_cap()`
- `test_sep_log_captures_token_pressure_events()`

---

## 5. Acceptance Criteria mapping

| AC | Test artifact | Owner agent |
|----|---------------|-------------|
| AC1 | tests/watchdog-kill-test.sh | backend-dev + test-automation-engineer |
| AC2 | tests/watchdog-kill-test.sh | backend-dev + test-automation-engineer |
| AC3 | tests/sep-log-schema-test.sh (fixture #1 happy path) | backend-dev |
| AC4 | tests/sep-log-schema-test.sh (fixtures #2, #3) | backend-dev |
| AC5 | tests/sep-log-schema-test.sh (integration via finalize) | backend-dev |
| AC6 | squad-cli/tests/test_reliability.py::test_last_failure_returns_most_recent_failed_sep | backend-dev |
| AC7 | squad-cli/tests/test_reliability.py::test_retry_budget_reads_from_policy_yaml | backend-dev |
| AC8 | squad-cli/tests/test_reliability.py::test_gate_health_aggregates_last_20_runs | backend-dev |
| AC9 | tests/bypass-lint-test.sh | backend-dev |
| AC10 | squad-cli/tests/test_cost_pressure.py (reads policy) | backend-dev |
| AC11 | squad-cli/tests/test_cost_pressure.py::test_pressure_warning_emitted_when_agent_exceeds_soft_cap | backend-dev |

---

## 6. Required /implement specialists

- backend-dev
- test-automation-engineer
- code-reviewer
- security-reviewer
- performance-engineer
- docs-writer (Wave B)

---

## 7. Definition of Done (per improvement)

### M1 — Watchdog kill verify
- [ ] `kill -0` re-check loop implemented (5 × 0.2s).
- [ ] `[Kill Confirmed]` / `[Kill Failed]` tags emitted on stdout.
- [ ] `.kill-failed-<pid>` marker created on failure.
- [ ] `tests/watchdog-kill-test.sh` passes (both fixtures).
- [ ] Code-reviewer approval.
- [ ] No regression in existing watchdog smoke tests.

### M2 — SEP schema validation
- [ ] `hooks/sep-log.schema.json` covers all required fields incl. `worktrees: list`.
- [ ] `bin/validate-sep-log.py` exit codes correct (0 / 5).
- [ ] `bin/finalize-skill.sh` aborts on schema failure.
- [ ] `tests/sep-log-schema-test.sh` passes (3 fixtures).
- [ ] `validate.sh` updated to invoke validator on existing SEP fixtures.
- [ ] jsonschema dep documented in install instructions.

### M3 — Reliability CLI
- [ ] 3 subcommands work end-to-end.
- [ ] `squad-cli/tests/test_reliability.py` passes.
- [ ] `docs/RELIABILITY-CLI.md` published.
- [ ] cli.py wires subcommand without breaking existing commands.

### M4 — Bypass lint
- [ ] `bypass_patterns` declared in `runtime-policy.yaml`.
- [ ] `validate.sh` lints every SKILL.md.
- [ ] `# bypass-lint:` marker honored.
- [ ] `tests/bypass-lint-test.sh` passes.
- [ ] No false positive against current 29 skills.

### M5 — Per-agent token cap
- [ ] `per_agent_token_soft_cap: 0.30` in policy.
- [ ] `cost.py` reads cap, computes per-agent ratio.
- [ ] `[Token Pressure]` warning emitted on threshold cross.
- [ ] SEP log captures `token_pressure_events: []`.
- [ ] severity=warning v1 (not blocking).

---

## 8. Risks & Mitigations (consolidated)

| ID | Risk | Mitigation |
|----|------|------------|
| R1 | jsonschema absent in operator env | preflight check + T2.0 install step + doc update |
| R2 | bypass lint false positives | `# bypass-lint:` marker; literal match (not regex) v1 |
| R3 | soft_cap 0.30 too tight for small skills | severity=warning v1; telemetry-driven promote |
| R4 | Watchdog kill verify flaky in CI namespaces | 1s total timeout; document container PID namespace caveat |
| R5 | SEP schema breaking changes | `schema_version: 1` field; bump on breaking edits |
| R6 | Bypass list missing real patterns | Grow freely via PR; retrospective adds entries |

---

## 9. Bridge to /implement

**Next step:**
```
/claude-tech-squad:implement ai-docs/harness-reliability-improvements/blueprint.md
```

**Execution order:**
1. Wave A in parallel (M1, M2, M4) — RED tests already committed.
2. Wave B after Wave A green (M3, M5) — RED tests written by /implement T3.0, T5.0.
3. Quality gate Q.0 multi-lens review.
4. docs-writer publishes RELIABILITY-CLI.md.
5. Release patch bump (fix: harness reliability hardening).

**Operational notes for /implement:**
- `per_agent_token_soft_cap: 0.30`
- `[Token Pressure]` severity: **warning** v1 (promote to blocking only after 10+ runs of telemetry).
- `bypass_patterns` is allowed to grow freely via subsequent PRs; lint reads policy at runtime.
- jsonschema dep: verify in preflight; if absent, T2.0 [setup] installs.

**Blueprint sign-off gate:** user approves this document before /implement starts.
