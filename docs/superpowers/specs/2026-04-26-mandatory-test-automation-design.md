# Mandatory Test Automation — Design Spec

**Date:** 2026-04-26
**Status:** Draft (pending user review)
**Repo:** claude-tech-squad
**Change class:** B (PR-A) + C (PR-B, PR-C) — see Rollout

---

## 1. Problem

Today the squad's implementation skills (`squad`, `implement`, `refactor`, `bug-fix`, `hotfix`) reference test agents inconsistently and have no mechanical enforcement that tests are written for new code. When the squad operates on a repository without test infrastructure, it proceeds silently, accumulating tech debt that surfaces only in production. The three failure modes:

1. **Inconsistency** — skills do not always invoke test agents in the same order, and `validate.sh` cannot detect omissions.
2. **Weak gate** — even when invoked, no mechanism blocks the pipeline if the diff contains new production code without paired tests.
3. **Legacy debt** — repos without test infrastructure pass through the squad with no proposal to bootstrap, perpetuating the gap.

## 2. Goals

- Make the test gate mechanically enforceable across all 5 implementation skills.
- Block any pipeline run that produces production code without paired tests, unless the operator explicitly approves a documented exemption.
- Detect repos without test infrastructure at preflight and propose a bootstrap plan; track repos that have been bootstrapped to avoid re-prompting.
- Honor the inviolable principle **propose-never-silent**: every skip is a visible proposal, registered as tech debt, with an automatic follow-up task.

## 3. Non-goals

- Not enforcing TDD ordering via commit-by-commit verification (aspirational, hard to validate mechanically).
- Not enforcing minimum coverage percentage as BLOCKING (kept as WARNING signal only).
- Not bootstrapping testing in IaC, migrations, or non-implementation skills (out of scope).
- Not replacing the existing `test-automation-engineer` or `tdd-specialist` agents — design composes them.

## 4. Architecture

Three cooperating pillars, each in its natural architectural layer:

```
PILAR A — ENFORCEMENT (CI-level, structural)
  scripts/validate.sh
    └─ checks 5 SKILL.md call tdd-specialist + test-automation-engineer in correct order
    └─ checks runtime-policy.yaml has `mandatory_test_gate` block

PILAR C — BOOTSTRAP (preflight, runtime)
  squad-cli/preflight.py + test_gate.detect_test_infra
  /claude-tech-squad:test-bootstrap (standalone skill, opt-in)
  task_memory.test_infra_bootstrapped flag (1st-contact vs subsequent)

PILAR B — GATE (runtime, BLOCKING during feature)
  hooks/test-gate.sh (PostToolUse, after impl phase)
    └─ calls squad-cli/test_gate.py evaluate
    └─ BLOCKING: production file new/changed with no paired test
    └─ WARNING: coverage delta dropped > threshold
```

Inviolable principle across all three: **propose-never-silent**.

## 5. Pillar A — Enforcement (validate.sh)

### 5.1 Changes to `scripts/validate.sh`

Adds `validate_test_gate_contract()` invoked after existing validations. For each skill in `MANDATORY_TEST_GATE_SKILLS=("squad" "implement" "refactor" "bug-fix" "hotfix")`:

1. **Required agents present** — grep for `subagent_type: "claude-tech-squad:tdd-specialist"` AND `subagent_type: "claude-tech-squad:test-automation-engineer"` in SKILL.md. Fail if either is missing.
2. **Correct order** — line number of `tdd-specialist` invocation < line of any dev agent (`backend-dev`, `frontend-dev`, `django-backend`, `react-developer`, `vue-developer`, `mobile-dev`, `python-developer`, `typescript-developer`, `javascript-developer`, `shell-developer`) < line of `test-automation-engineer`. Fail on inversions.
3. **Test Gate section declared** — SKILL.md contains `### Test Gate (Mandatory)` block with reference to `runtime-policy.yaml#mandatory_test_gate`.
4. **Exemption protocol documented** — if SKILL.md declares an exemption (only `hotfix` initially), it must contain `### Test Gate Exemption Protocol` section describing the proposal + registration + follow-up flow.

### 5.2 Changes to `runtime-policy.yaml`

New top-level key:

```yaml
mandatory_test_gate:
  enabled: true
  enforce_level: warning  # warning | blocking — flips to blocking after shadow period
  skills_in_scope: [squad, implement, refactor, bug-fix, hotfix]
  required_agents:
    pre_impl: tdd-specialist
    post_impl: test-automation-engineer
  non_code_extensions: [.md, .yaml, .yml, .json, .toml, .txt, .lock]
  auto_generated_paths:
    - "**/migrations/*.py"
    - "**/dist/**"
    - "**/build/**"
    - "*.generated.*"
    - "**/__pycache__/**"
  coverage_warning_threshold: 0.02
  exemption_protocols:
    hotfix:
      flag: "--skip-tests"
      requires_proposal: true
      requires_followup_task: true
      auto_followup_days: 7
  bootstrap_policy:
    first_contact: human_gate_with_proposal
    subsequent: incremental_automatic
    unknown_stack: human_gate_default_no
```

`validate.sh` adds `mandatory_test_gate` to `RUNTIME_POLICY_REQUIRED_KEYS`.

### 5.3 Changes to documentation

`docs/SKILL-CONTRACT.md` gains "Test Gate Contract" paragraph listing the 4 requirements above for any skill in `MANDATORY_TEST_GATE_SKILLS`.

### 5.4 Per-skill SKILL.md edits

Each of the 5 SKILL.md files gains:
- `### Test Gate (Mandatory)` block (or `### Test Gate Exemption Protocol` for `hotfix`).
- Updated agent chain placing `tdd-specialist` before dev phase and `test-automation-engineer` after dev phase, before reviewer.

Differentiation:

| Skill | tdd-specialist role | test-automation-engineer role |
|---|---|---|
| `squad` | TDD-first formal contract | full validation + edge cases |
| `implement` | TDD-first formal contract | full validation + edge cases |
| `refactor` | characterization tests for current behavior | validates refactor preserves behavior |
| `bug-fix` | failing test that reproduces bug (already pattern) | edge cases, regression coverage |
| `hotfix` | rapid test proposal; exemption available | full or skipped per exemption protocol |

## 6. Pillar B — Gate (runtime)

### 6.1 New module `squad-cli/test_gate.py`

```python
class StackFingerprint:  # reuses stack_detect.py
    language: str
    framework: str | None
    test_framework: str | None
    test_dirs: list[str]

class TestInfraStatus(Enum):
    PRESENT_AND_CONFIGURED = "present"
    PARTIAL = "partial"
    ABSENT = "absent"
    UNKNOWN = "unknown"

class GateVerdict(Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCKING = "blocking"

class TestGate:
    def detect_stack(repo_root) -> StackFingerprint: ...
    def detect_test_infra(repo_root, stack) -> TestInfraStatus: ...
    def check_paired_tests(diff_files, stack) -> list[UnpairedFile]: ...
    def check_coverage_delta(before, after) -> CoverageDelta: ...
    def evaluate_gate(unpaired, delta, exemptions, policy) -> GateVerdict: ...
    def register_tech_debt(verdict, sep_log, task_memory) -> None: ...
```

Pairing heuristics per stack (extensible):
- Python: `src/foo/bar.py` → `tests/test_bar.py` OR `tests/foo/test_bar.py` OR `**/bar_test.py`.
- TypeScript/JS: `src/foo/bar.ts` → `**/bar.test.ts` OR `**/bar.spec.ts` OR `__tests__/bar.test.ts`.
- Go: `foo/bar.go` → `foo/bar_test.go`.
- Other stacks: documented as added; `UNKNOWN` triggers operator gate.

`evaluate_gate` returns:
- `BLOCKING` if `unpaired` non-empty AND no exemption applies AND `enforce_level=blocking`.
- `WARNING` if `unpaired` non-empty AND `enforce_level=warning` (shadow mode), OR if `coverage.dropped > coverage_warning_threshold`.
- `PASS` otherwise.

### 6.2 New hook `hooks/test-gate.sh`

PostToolUse hook. Fires on every PostToolUse event but filters early: returns 0 unless the tool was `Agent` and `subagent_type` is `claude-tech-squad:test-automation-engineer`, OR the skill declared an exemption (in which case it fires when the impl-phase agent for that skill completes — detected by checking the last impl-phase agent recorded in the run's checkpoint state). Body:

```bash
#!/usr/bin/env bash
set -euo pipefail
SKILL="${CLAUDE_SKILL_NAME:-}"
RUN_ID="${CLAUDE_RUN_ID:-}"
[[ -z "$SKILL" || -z "$RUN_ID" ]] && exit 0

# Only enforce for in-scope skills
python3 "$(dirname "$0")/../bin/squad-cli" test-gate evaluate \
    --skill "$SKILL" --run-id "$RUN_ID"
case $? in
    0) exit 0 ;;        # PASS or WARNING — continue
    2) exit 2 ;;        # BLOCKING — halt pipeline
    *) echo "test-gate: internal error" >&2; exit 1 ;;
esac
```

`hooks/settings-template.json` gains a PostToolUse hook entry that triggers this script. `hooks/README.md` updated.

### 6.3 New CLI subcommand

`squad-cli` gains `test-gate` subcommand:
- `squad-cli test-gate evaluate --skill <name> --run-id <id>` — runs full evaluation, writes verdict to SEP log, exits with code per Section 6.2.
- `squad-cli test-gate explain --run-id <id>` — prints last verdict (debugging aid).

### 6.4 Integration with retry/fallback

- `failure_handling.max_retries: 2` applies normally to `test-automation-engineer`.
- `fallback_matrix` entry: `test-automation-engineer: qa-tester`.
- BLOCKING after retries+fallback uses existing human gate machinery (no new flow).

### 6.5 SEP log additions

Every run in scope adds:

```yaml
test_gate:
  verdict: pass | warning | blocking
  enforce_level: warning | blocking
  unpaired_files:
    - path: src/foo/bar.py
      reason: no_paired_test_found
  coverage_before: 0.82
  coverage_after: 0.81
  coverage_delta: -0.01
  exemptions_applied: []
  tech_debt_registered: false
  gate_duration_ms: 412
```

`task_memory.py` gains `tech_debt_no_test: list[path]` updated when a WARNING/BLOCKING is accepted by the operator.

## 7. Pillar C — Bootstrap

### 7.1 Preflight detection

In `squad-cli/preflight.py`, new step `check_test_infra()` invoked when current skill is in scope:

1. Detect stack via `stack_detect.py`.
2. Detect test infrastructure via `test_gate.detect_test_infra`.
3. Check `task_memory.get("test_infra_bootstrapped")`.

Decision matrix:

| Infra status | Bootstrapped before? | Behavior |
|---|---|---|
| `PRESENT_AND_CONFIGURED` | any | proceed normally; gate active |
| `ABSENT` or `PARTIAL` | no (1st contact) | **human gate with proposal** |
| `ABSENT` or `PARTIAL` | yes | **incremental automatic** |
| `UNKNOWN` | any | prompt operator (default N) |

### 7.2 First-contact human gate

Skill pauses and shows operator:

```
Repository without test infrastructure detected.
Stack: Python 3.11 + Django 5.0
Bootstrap plan proposed:
  - Framework: pytest + pytest-django + coverage.py
  - Structure: tests/unit/, tests/integration/
  - CI: add pytest step in .github/workflows/ci.yml
  - Initial characterization: 3 hotspots (apps/orders/models.py:Order, ...)
Estimate: ~12min, ~80k tokens

Options:
  [1] Approve — run /test-bootstrap before feature
  [2] Reject — proceed with feature, mark tech_debt: no_tests
  [3] Abort
```

- Option 1: invoke `/claude-tech-squad:test-bootstrap`, then resume original skill via existing checkpoint mechanism.
- Option 2: `task_memory.set("test_infra_bootstrapped", false)` AND `task_memory.set("debt_acknowledged", true)`. Gate runs in WARNING mode for current run; subsequent runs get incremental automatic flow.
- Option 3: pipeline aborts cleanly, no SEP log marks.

### 7.3 New skill `/claude-tech-squad:test-bootstrap`

Standalone skill (not chained from others). Pipeline:

1. **Preflight** — confirm absence, identify hotspots via `git log --pretty=format: --name-only --since="90 days ago" | sort | uniq -c | sort -rn | head -10`.
2. **Agent: `test-planner`** — define framework, structure, coverage policy.
3. **Agent: `test-automation-engineer`** — install framework, create directory structure, write characterization tests for hotspots.
4. **Agent: `ci-cd`** — add test step to existing pipeline (detect `.github/workflows/`, `.gitlab-ci.yml`, etc.).
5. **Human gate** — operator reviews diff before commit.
6. **Persistence** — `task_memory.set("test_infra_bootstrapped", true)`.

Skill is opt-in only; not auto-invoked except from option 1 of the first-contact gate. Class C PR.

### 7.4 Subsequent incremental flow

When `task_memory.test_infra_bootstrapped == false` AND `debt_acknowledged == true`, `test-automation-engineer` receives extra context:

> This repo has acknowledged test debt. Write tests for files this feature touches even if standard test directory does not exist; create minimal structure following the detected framework's convention.

Pillar B gate remains BLOCKING for diff files (not for repo-wide coverage).

## 8. Edge cases

| Case | Behavior |
|---|---|
| Stack `UNKNOWN` | Operator decides; default N |
| Diff only docs/configs | Gate releases via `non_code_extensions` |
| Diff only tests | Gate releases (no test-of-test required) |
| Auto-generated files | Released via `auto_generated_paths` |
| `test-automation-engineer` exhausts retries+fallback | Human gate: skip+debt, write manual, abort |
| Operator insists on skip | Always allowed **with proposal + registration + auto-followup task** |
| Polyglot monorepo | Multi-stack detection; gate per file path |
| `hotfix --skip-tests` | Proposal shown, skip registered as `tech_debt: hotfix_without_test:<file>`, follow-up task auto-created with 7-day deadline, scheduled remote agent reopens case if not addressed |

## 9. Observability

- SEP log gains `test_gate` block (Section 6.5).
- `dashboard` skill adds "Test Gate" column showing %PASS / %WARNING / %BLOCKING-skipped.
- `factory-retrospective` adds metric to detect skip patterns (e.g., "X% of skips concentrated in hotfix → review exemption protocol").
- New section in `dashboard.html` template: "Tech Debt: No Tests" listing files marked across last 50 runs.

## 10. Rollout

Three sequential PRs:

### PR-A — Pillar A (Class B)

Files: `scripts/validate.sh`, `runtime-policy.yaml`, 5 SKILL.md (chain updates), `docs/SKILL-CONTRACT.md`.

Validation: validate.sh + smoke-test.sh + dogfood.sh.

State after merge: chain is structurally mandatory; runtime gate not yet active.

### PR-B — Pillar B (Class C)

Files: new `squad-cli/test_gate.py`, new `hooks/test-gate.sh`, updates to `squad-cli/cli.py`, `hooks/settings-template.json`, `hooks/README.md`, `runtime-policy.yaml` (already has block from PR-A; flip `enforce_level` to `warning`).

Validation: validate.sh + smoke-test.sh + dogfood.sh + 1 real golden run per scenario in `fixtures/dogfooding/` showing gate firing in shadow mode.

After 1 release in `enforce_level: warning` (shadow mode) with no false positives in golden runs, follow-up minimal PR flips to `enforce_level: blocking`.

### PR-C — Pillar C (Class C)

Files: `squad-cli/preflight.py` (new step), `squad-cli/test_gate.py` (extension), `squad-cli/task_memory.py` (new keys), new `skills/test-bootstrap/SKILL.md`, `runtime-policy.yaml` (`bootstrap_policy` block).

New fixture: `fixtures/dogfooding/no-test-infra/` simulating repo without tests.

Validation: full Class C suite + golden run in `no-test-infra` exercising both first-contact human gate and incremental flow.

## 11. Open questions / risks

- **Coverage tool availability** — `check_coverage_delta` requires running coverage tooling. For stacks without configured coverage, that signal is absent and `coverage_delta` is skipped (not an error). Documented behavior.
- **Hook reliability** — PostToolUse hook firing depends on Claude Code harness honoring it. Existing `pre-tool-guard.sh` is precedent; same mechanism reused.
- **Token cost** — adding 2 agents in every implementation run increases cost ~20-30%. Mitigation: cost-guardrails already in policy will surface this; if it becomes a problem, opt-in `--no-tdd` flag (skip pre-impl `tdd-specialist`, keep post-impl gate) can be added in a follow-up PR.
- **Polyglot pairing heuristics** — initial implementation covers Python, TypeScript/JS, Go. Other stacks (Ruby, Java, Rust, etc.) added incrementally; in the meantime they trigger `UNKNOWN` and operator gate.

## 12. Acceptance criteria

- `bash scripts/validate.sh` fails on any of the 5 SKILL.md missing required test agents in correct order.
- `bash scripts/validate.sh` fails on `runtime-policy.yaml` missing `mandatory_test_gate`.
- A run of `/claude-tech-squad:implement` on a fixture that produces a new `.py` file without a paired test results in `test_gate.verdict = blocking` after PR-B flip; before flip, `verdict = warning`.
- A run of any in-scope skill on a fixture without test infrastructure pauses at preflight with the bootstrap proposal.
- A `hotfix --skip-tests` run registers `tech_debt: hotfix_without_test:<file>` in SEP log, in `task_memory`, and creates a scheduled follow-up agent.
- All exemption paths visible in SEP log; none silent.
