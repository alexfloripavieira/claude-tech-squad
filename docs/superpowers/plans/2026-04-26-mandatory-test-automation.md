# Mandatory Test Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make test gating mechanically enforced across all 5 implementation skills, block runs that produce production code without paired tests, and detect/bootstrap repos lacking test infrastructure — never silently.

**Architecture:** Three pillars. Pillar A is structural enforcement in `validate.sh` + `runtime-policy.yaml`. Pillar B is a runtime gate via PostToolUse hook + new `test_gate.py` module in `squad-cli`. Pillar C is preflight detection + opt-in `/test-bootstrap` skill. Each pillar ships as one PR; PR-B depends on PR-A, PR-C depends on PR-B.

**Tech Stack:** Bash (validate.sh, hooks), Python 3.11 (squad_cli, click, pyyaml), Markdown (SKILL.md), YAML (runtime-policy).

**Spec reference:** `docs/superpowers/specs/2026-04-26-mandatory-test-automation-design.md`

---

## File Structure

**Created:**
- `plugins/claude-tech-squad/bin/squad_cli/test_gate.py` — gate logic (stack pairing, coverage delta, verdict)
- `plugins/claude-tech-squad/bin/squad_cli/test_gate_policy.py` — pure-data policy loader (split from test_gate to keep gate testable)
- `plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py` — pytest unit tests
- `plugins/claude-tech-squad/bin/squad_cli/tests/test_preflight_test_infra.py` — pytest tests for preflight infra check
- `plugins/claude-tech-squad/hooks/test-gate.sh` — PostToolUse hook
- `plugins/claude-tech-squad/skills/test-bootstrap/SKILL.md` — opt-in standalone skill
- `fixtures/dogfooding/no-test-infra/` — dogfood fixture (Python repo missing tests/)
- `docs/superpowers/plans/2026-04-26-mandatory-test-automation.md` — this plan

**Modified:**
- `plugins/claude-tech-squad/runtime-policy.yaml` — add `mandatory_test_gate` block, extend `fallback_matrix`
- `scripts/validate.sh` — add `validate_test_gate_contract`, register required runtime-policy key
- `plugins/claude-tech-squad/skills/squad/SKILL.md` — declare Test Gate, ensure post-impl `test-automation-engineer`
- `plugins/claude-tech-squad/skills/implement/SKILL.md` — same as squad
- `plugins/claude-tech-squad/skills/refactor/SKILL.md` — declare Test Gate (already has test-automation-engineer pre-impl; add post-impl validation pass)
- `plugins/claude-tech-squad/skills/bug-fix/SKILL.md` — declare Test Gate, add post-impl `test-automation-engineer`
- `plugins/claude-tech-squad/skills/hotfix/SKILL.md` — declare Test Gate Exemption Protocol with `--skip-tests` flag
- `plugins/claude-tech-squad/bin/squad_cli/cli.py` — register `test-gate` subcommand
- `plugins/claude-tech-squad/bin/squad_cli/preflight.py` — add `check_test_infra` step
- `plugins/claude-tech-squad/bin/squad_cli/task_memory.py` — add bootstrap state keys
- `plugins/claude-tech-squad/hooks/settings-template.json` — add PostToolUse entry
- `plugins/claude-tech-squad/hooks/README.md` — document the new hook
- `docs/SKILL-CONTRACT.md` — add Test Gate Contract paragraph
- `fixtures/dogfooding/scenarios.json` — add no-test-infra scenario
- `scripts/smoke-test.sh` — add assertions for new pieces

---

# PHASE A — Pillar A: Enforcement (PR-A, Class B)

End state: chain is structurally mandatory in validate.sh; runtime gate not yet active. PR mergeable on its own.

### Task A1: Add `mandatory_test_gate` to `runtime-policy.yaml`

**Files:**
- Modify: `plugins/claude-tech-squad/runtime-policy.yaml`

- [ ] **Step 1: Read end of file to find a good insertion point**

Run: `tail -20 plugins/claude-tech-squad/runtime-policy.yaml`

- [ ] **Step 2: Append the new block before `context_management:`**

Insert this block immediately before the `context_management:` line:

```yaml
mandatory_test_gate:
  enabled: true
  enforce_level: warning  # warning (shadow) | blocking — flipped after PR-B shadow release
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

- [ ] **Step 3: Validate YAML parses**

Run: `python3 -c "import yaml; yaml.safe_load(open('plugins/claude-tech-squad/runtime-policy.yaml'))"`
Expected: no output, exit 0.

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-tech-squad/runtime-policy.yaml
git commit -m "feat: add mandatory_test_gate policy block"
```

---

### Task A2: Add `test-automation-engineer` to `fallback_matrix`

**Files:**
- Modify: `plugins/claude-tech-squad/runtime-policy.yaml`

- [ ] **Step 1: Find current fallback_matrix entry for test-automation-engineer**

Run: `grep -A1 "test-automation-engineer:" plugins/claude-tech-squad/runtime-policy.yaml | head -10`

- [ ] **Step 2: Confirm fallback exists; if missing, add**

If grep returns nothing, append under the `fallback_matrix:` block:

```yaml
  test-automation-engineer:
    fallback: qa-tester
    reason: "test-automation-engineer exhausted retries; qa-tester provides last-resort coverage"
```

If it already exists, skip. Note in commit message which case applied.

- [ ] **Step 3: Validate YAML still parses**

Run: `python3 -c "import yaml; yaml.safe_load(open('plugins/claude-tech-squad/runtime-policy.yaml'))"`

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-tech-squad/runtime-policy.yaml
git commit -m "feat: ensure test-automation-engineer fallback in matrix"
```

---

### Task A3: Add `validate_test_gate_contract` to `validate.sh`

**Files:**
- Modify: `scripts/validate.sh`

- [ ] **Step 1: Read tail of validate.sh to find where to add new checks**

Run: `grep -n "^validate_\|^main\|^# ===" scripts/validate.sh | tail -20`

- [ ] **Step 2: Add the function definition near other `validate_*` functions**

Insert this function:

```bash
validate_test_gate_contract() {
    section "Validating mandatory_test_gate contract"

    local mandatory_skills=("squad" "implement" "refactor" "bug-fix" "hotfix")
    local skills_root="plugins/claude-tech-squad/skills"
    local dev_agents='backend-dev|frontend-dev|django-backend|react-developer|vue-developer|mobile-dev|python-developer|typescript-developer|javascript-developer|shell-developer'

    for skill in "${mandatory_skills[@]}"; do
        local skill_md="${skills_root}/${skill}/SKILL.md"
        [[ -f "$skill_md" ]] || { fail "missing $skill_md"; continue; }

        # Required agents present
        grep -q 'subagent_type: "claude-tech-squad:tdd-specialist"' "$skill_md" \
            || grep -q 'subagent_type="claude-tech-squad:tdd-specialist"' "$skill_md" \
            || fail "$skill: missing tdd-specialist invocation"
        grep -q 'subagent_type: "claude-tech-squad:test-automation-engineer"' "$skill_md" \
            || grep -q 'subagent_type="claude-tech-squad:test-automation-engineer"' "$skill_md" \
            || fail "$skill: missing test-automation-engineer invocation"

        # Test Gate section present
        if [[ "$skill" == "hotfix" ]]; then
            grep -q '^### Test Gate Exemption Protocol' "$skill_md" \
                || fail "$skill: missing '### Test Gate Exemption Protocol' section"
        else
            grep -q '^### Test Gate (Mandatory)' "$skill_md" \
                || fail "$skill: missing '### Test Gate (Mandatory)' section"
        fi

        # Order: tdd-specialist before any dev agent before test-automation-engineer
        local tdd_line dev_line tae_line
        tdd_line=$(grep -nE 'claude-tech-squad:tdd-specialist' "$skill_md" | head -1 | cut -d: -f1)
        dev_line=$(grep -nE "claude-tech-squad:(${dev_agents})" "$skill_md" | head -1 | cut -d: -f1)
        tae_line=$(grep -nE 'claude-tech-squad:test-automation-engineer' "$skill_md" | tail -1 | cut -d: -f1)
        if [[ -n "$tdd_line" && -n "$dev_line" && -n "$tae_line" ]]; then
            if (( tdd_line >= dev_line )) || (( dev_line >= tae_line )); then
                fail "$skill: order violation (tdd=${tdd_line} dev=${dev_line} tae=${tae_line}); expected tdd < dev < tae"
            fi
        fi
    done

    # Required runtime-policy key
    grep -q '^mandatory_test_gate:' plugins/claude-tech-squad/runtime-policy.yaml \
        || fail "runtime-policy.yaml missing 'mandatory_test_gate' top-level key"
}
```

Where `section` and `fail` are existing helpers in validate.sh — confirm by grepping `grep -n "^section\|^fail" scripts/validate.sh`.

- [ ] **Step 3: Wire the function into main**

Find the line that calls other `validate_*` functions in sequence (often inside `main()` or at script bottom) and add `validate_test_gate_contract` there. Use grep `grep -n "validate_runtime_policy\|validate_skills" scripts/validate.sh` to find the right spot.

- [ ] **Step 4: Run validate.sh and observe expected failures**

Run: `bash scripts/validate.sh 2>&1 | tail -40`
Expected: failures for missing `### Test Gate (Mandatory)` sections in 4 skills + missing exemption section in `hotfix` (the next 5 tasks fix these).

- [ ] **Step 5: Commit**

```bash
git add scripts/validate.sh
git commit -m "feat: add validate_test_gate_contract enforcement"
```

---

### Task A4: Add Test Gate section to `squad/SKILL.md`

**Files:**
- Modify: `plugins/claude-tech-squad/skills/squad/SKILL.md`

- [ ] **Step 1: Find a good anchor — section before the agent chain spawning impl**

Run: `grep -n "^## \|^### " plugins/claude-tech-squad/skills/squad/SKILL.md | head -30`

- [ ] **Step 2: Insert the Test Gate section near the top of the implementation phase**

Add this block immediately before the impl-phase spawn block:

```markdown
### Test Gate (Mandatory)

This skill is in `mandatory_test_gate.skills_in_scope` (see `runtime-policy.yaml#mandatory_test_gate`).

Contract:
- `tdd-specialist` MUST be spawned before any dev agent.
- `test-automation-engineer` MUST be spawned after dev agents and before reviewer agents.
- After `test-automation-engineer` completes, the PostToolUse hook `hooks/test-gate.sh` evaluates the gate. A `BLOCKING` verdict halts the pipeline; the operator decides skip+debt, write manual, or abort.
- No exemption is available for this skill. Any pipeline producing a new or modified production file without a paired test will block.
```

- [ ] **Step 3: Confirm chain order matches contract**

Run: `grep -nE "claude-tech-squad:(tdd-specialist|backend-dev|frontend-dev|test-automation-engineer)" plugins/claude-tech-squad/skills/squad/SKILL.md | head -10`
Verify: tdd-specialist line < dev-* line < test-automation-engineer line.

If `test-automation-engineer` is not yet present in chain, add a spawn block right after the dev/impl phase and before the reviewer phase (mirror existing spawn syntax in the file).

- [ ] **Step 4: Run validate.sh and verify squad passes**

Run: `bash scripts/validate.sh 2>&1 | grep -E "squad|test_gate" | head -20`
Expected: squad-related test_gate checks pass; other 4 skills still failing.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/skills/squad/SKILL.md
git commit -m "feat: declare Test Gate contract in /squad"
```

---

### Task A5: Add Test Gate section to `implement/SKILL.md`

**Files:**
- Modify: `plugins/claude-tech-squad/skills/implement/SKILL.md`

- [ ] **Step 1: Locate impl-phase anchor**

Run: `grep -nE "claude-tech-squad:(tdd-specialist|backend-dev|test-automation-engineer)" plugins/claude-tech-squad/skills/implement/SKILL.md`

- [ ] **Step 2: Insert Test Gate section**

Same block as Task A4 Step 2, inserted before the impl-phase spawn block.

- [ ] **Step 3: Add `test-automation-engineer` post-impl spawn if missing**

If grep in Step 1 shows no `test-automation-engineer` in the implement skill, add a spawn block after dev agents and before reviewer:

```markdown
After dev agents complete and before spawning reviewer:

\`\`\`
Agent(team_name=<team>, name="test-automation-engineer",
      subagent_type="claude-tech-squad:test-automation-engineer",
      prompt="Validate test coverage for files modified in this implementation phase. Add edge-case tests for any new branches. Pair every new/modified production file with a test. Report unpaired files in your Result Contract.")
\`\`\`
```

- [ ] **Step 4: Validate**

Run: `bash scripts/validate.sh 2>&1 | grep -E "implement|test_gate" | head`
Expected: implement test_gate checks pass.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/skills/implement/SKILL.md
git commit -m "feat: declare Test Gate contract in /implement"
```

---

### Task A6: Add Test Gate section to `refactor/SKILL.md`

**Files:**
- Modify: `plugins/claude-tech-squad/skills/refactor/SKILL.md`

- [ ] **Step 1: Inspect current chain**

Run: `grep -nE "claude-tech-squad:(tdd-specialist|test-automation-engineer)" plugins/claude-tech-squad/skills/refactor/SKILL.md`

The skill currently has `test-automation-engineer` writing characterization tests pre-impl. We need also a post-impl validation pass AND a `tdd-specialist` invocation (or document equivalence in the Test Gate section).

- [ ] **Step 2: Insert Test Gate section adapted for refactor**

```markdown
### Test Gate (Mandatory)

This skill is in `mandatory_test_gate.skills_in_scope` (see `runtime-policy.yaml#mandatory_test_gate`).

Refactor adapts the contract:
- `tdd-specialist` MUST be spawned to confirm characterization tests lock all behavior the refactor will touch — this acts as the pre-impl test contract.
- `test-automation-engineer` writes the characterization tests, runs them green on unmodified code, then re-runs after the refactor completes (post-impl validation pass).
- After the post-impl pass, `hooks/test-gate.sh` evaluates the gate. A `BLOCKING` verdict (e.g., refactor introduced a new untested branch) halts the pipeline.
- No exemption.
```

- [ ] **Step 3: Add `tdd-specialist` invocation if absent**

If grep shows no `tdd-specialist`, add a spawn block right before the existing `test-automation-engineer` characterization block:

```markdown
Before characterization tests are written:

\`\`\`
Agent(team_name=<team>, name="tdd-specialist",
      subagent_type="claude-tech-squad:tdd-specialist",
      prompt="Define the behavioral contract this refactor MUST preserve. List the characterization tests that must exist before any refactor step. Hand contract to test-automation-engineer.")
\`\`\`
```

- [ ] **Step 4: Add post-impl `test-automation-engineer` validation pass**

After all refactor steps, add:

```markdown
After the final refactor step:

\`\`\`
Agent(team_name=<team>, name="test-automation-validate",
      subagent_type="claude-tech-squad:test-automation-engineer",
      prompt="Re-run characterization tests against the refactored code. Add tests for any newly introduced branches. Report unpaired files.")
\`\`\`
```

- [ ] **Step 5: Validate**

Run: `bash scripts/validate.sh 2>&1 | grep -E "refactor|test_gate" | head`

- [ ] **Step 6: Commit**

```bash
git add plugins/claude-tech-squad/skills/refactor/SKILL.md
git commit -m "feat: declare Test Gate contract in /refactor"
```

---

### Task A7: Add Test Gate section to `bug-fix/SKILL.md`

**Files:**
- Modify: `plugins/claude-tech-squad/skills/bug-fix/SKILL.md`

- [ ] **Step 1: Inspect chain**

Run: `grep -nE "claude-tech-squad:(tdd-specialist|test-automation-engineer)" plugins/claude-tech-squad/skills/bug-fix/SKILL.md`

bug-fix already has `tdd-specialist` (writes failing test reproducing the bug). Need to add `test-automation-engineer` post-impl for edge cases.

- [ ] **Step 2: Insert Test Gate section**

Same block as Task A4 Step 2, adapted:

```markdown
### Test Gate (Mandatory)

This skill is in `mandatory_test_gate.skills_in_scope` (see `runtime-policy.yaml#mandatory_test_gate`).

Contract:
- `tdd-specialist` MUST write a failing test reproducing the bug before the dev agent fixes it (pre-existing pattern).
- `test-automation-engineer` MUST run after the fix to add regression and edge-case tests for the touched code paths.
- After `test-automation-engineer` completes, `hooks/test-gate.sh` evaluates the gate. A `BLOCKING` verdict halts the pipeline.
- No exemption.
```

- [ ] **Step 3: Add `test-automation-engineer` post-impl spawn**

After the dev agent fixes the bug and before reviewer:

```markdown
\`\`\`
Agent(team_name=<team>, name="test-automation-engineer",
      subagent_type="claude-tech-squad:test-automation-engineer",
      prompt="The bug is now fixed. Add regression tests covering the fix and edge cases adjacent to the touched code paths. Pair every modified production file with a test. Report unpaired files.")
\`\`\`
```

- [ ] **Step 4: Validate**

Run: `bash scripts/validate.sh 2>&1 | grep -E "bug-fix|test_gate" | head`

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/skills/bug-fix/SKILL.md
git commit -m "feat: declare Test Gate contract in /bug-fix"
```

---

### Task A8: Add Test Gate Exemption Protocol to `hotfix/SKILL.md`

**Files:**
- Modify: `plugins/claude-tech-squad/skills/hotfix/SKILL.md`

- [ ] **Step 1: Inspect chain**

Run: `grep -nE "claude-tech-squad:(tdd-specialist|test-automation-engineer)" plugins/claude-tech-squad/skills/hotfix/SKILL.md`

- [ ] **Step 2: Insert Exemption Protocol section**

```markdown
### Test Gate Exemption Protocol

This skill is in `mandatory_test_gate.skills_in_scope` and is the only skill with an exemption (`runtime-policy.yaml#mandatory_test_gate.exemption_protocols.hotfix`).

Default behavior:
- `tdd-specialist` MUST be spawned to propose a rapid test reproducing the production break, even in emergencies.
- `test-automation-engineer` MUST be spawned after the patch unless the operator invokes the exemption.

Exemption (`--skip-tests` flag):
- Operator must approve a visible proposal showing what test would be written and why skipping is justified now.
- Skip is registered in SEP log as `tech_debt: hotfix_without_test:<file>` and persisted to `task_memory`.
- An automatic follow-up task is created with a `auto_followup_days: 7` deadline.
- A scheduled remote agent is registered (via `/schedule`) to reopen the case if not addressed within the deadline.
- Silent skip is forbidden — `hooks/test-gate.sh` blocks the pipeline if the exemption was not declared in the run state.
```

- [ ] **Step 3: Ensure both `tdd-specialist` and `test-automation-engineer` are referenced in the chain**

If absent, add minimal spawn blocks (similar to Task A4/A7) gated by an inline check `unless --skip-tests is set`.

- [ ] **Step 4: Validate**

Run: `bash scripts/validate.sh 2>&1 | grep -E "hotfix|test_gate" | head`

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/skills/hotfix/SKILL.md
git commit -m "feat: declare Test Gate exemption protocol in /hotfix"
```

---

### Task A9: Update SKILL-CONTRACT.md and run full validation

**Files:**
- Modify: `docs/SKILL-CONTRACT.md`

- [ ] **Step 1: Read existing contract sections**

Run: `grep -n "^## \|^### " docs/SKILL-CONTRACT.md`

- [ ] **Step 2: Append "Test Gate Contract" section**

```markdown
## Test Gate Contract

For any skill listed in `runtime-policy.yaml#mandatory_test_gate.skills_in_scope`, the SKILL.md MUST include:

1. An invocation of `subagent_type: "claude-tech-squad:tdd-specialist"` before any dev agent (`backend-dev`, `frontend-dev`, `django-backend`, `react-developer`, `vue-developer`, `mobile-dev`, `python-developer`, `typescript-developer`, `javascript-developer`, `shell-developer`).
2. An invocation of `subagent_type: "claude-tech-squad:test-automation-engineer"` after dev agents and before reviewer agents.
3. A `### Test Gate (Mandatory)` section referencing `runtime-policy.yaml#mandatory_test_gate`. The only exception is skills that declare an exemption — they use `### Test Gate Exemption Protocol` instead, documenting the proposal/registration/followup flow.

`scripts/validate.sh` enforces these rules mechanically via `validate_test_gate_contract`. Skills outside the `skills_in_scope` list are unaffected.
```

- [ ] **Step 3: Run full validation suite**

Run: `bash scripts/validate.sh && bash scripts/smoke-test.sh`
Expected: both pass.

- [ ] **Step 4: Commit and tag the PR-A endpoint**

```bash
git add docs/SKILL-CONTRACT.md
git commit -m "docs: document Test Gate contract for skills in scope"
git tag --no-sign mandatory-test-automation-pr-a
```

PR-A complete. Open a PR with title `feat: enforce mandatory test agents in 5 implementation skills (Pillar A)`.

---

# PHASE B — Pillar B: Runtime Gate (PR-B, Class C)

End state: hook + squad-cli `test-gate evaluate` flag drift in shadow mode (warning, not blocking). After 1 release with clean dogfood, follow-up minimal PR flips `enforce_level` to `blocking`.

### Task B1: Set up pytest harness for `squad-cli`

**Files:**
- Create: `plugins/claude-tech-squad/bin/squad_cli/tests/__init__.py`
- Create: `plugins/claude-tech-squad/bin/squad_cli/tests/conftest.py`
- Create: `plugins/claude-tech-squad/bin/squad_cli/tests/test_smoke.py`
- Modify: `squad-cli/venv` (add pytest)

- [ ] **Step 1: Install pytest in the venv**

Run: `cd squad-cli && source venv/bin/activate && pip install pytest && deactivate`
Expected: pytest installed.

- [ ] **Step 2: Create empty `__init__.py`**

Write to `plugins/claude-tech-squad/bin/squad_cli/tests/__init__.py`:

```python
```

- [ ] **Step 3: Create minimal `conftest.py`**

Write to `plugins/claude-tech-squad/bin/squad_cli/tests/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

- [ ] **Step 4: Create smoke test verifying imports work**

Write to `plugins/claude-tech-squad/bin/squad_cli/tests/test_smoke.py`:

```python
def test_import_cli():
    from squad_cli import cli
    assert hasattr(cli, "main")
```

- [ ] **Step 5: Run pytest and confirm green**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/ -v`
Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/claude-tech-squad/bin/squad_cli/tests/
git commit -m "test: add pytest harness for squad_cli"
```

---

### Task B2: Write failing test for `test_gate.check_paired_tests` (Python)

**Files:**
- Create: `plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py`

- [ ] **Step 1: Write the failing test**

Write to `plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py`:

```python
import pytest
from pathlib import Path

from squad_cli.test_gate import check_paired_tests, StackFingerprint


def make_stack(language="python"):
    return StackFingerprint(language=language, framework=None, test_framework="pytest", test_dirs=["tests"])


def test_python_unpaired_when_no_test_file(tmp_path: Path):
    (tmp_path / "src" / "foo").mkdir(parents=True)
    (tmp_path / "src" / "foo" / "bar.py").write_text("def x(): ...\n")
    diff = ["src/foo/bar.py"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert len(result) == 1
    assert result[0].path == "src/foo/bar.py"


def test_python_paired_when_test_exists(tmp_path: Path):
    (tmp_path / "src" / "foo").mkdir(parents=True)
    (tmp_path / "src" / "foo" / "bar.py").write_text("def x(): ...\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_bar.py").write_text("def test_x(): ...\n")
    diff = ["src/foo/bar.py"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert result == []


def test_non_code_extension_ignored(tmp_path: Path):
    diff = ["README.md", "config.yaml"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert result == []


def test_test_file_itself_ignored(tmp_path: Path):
    diff = ["tests/test_bar.py"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert result == []
```

- [ ] **Step 2: Run and confirm it fails (module does not exist)**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_test_gate.py -v`
Expected: ImportError or ModuleNotFoundError on `squad_cli.test_gate`.

---

### Task B3: Implement `test_gate.py` with stack pairing heuristics

**Files:**
- Create: `plugins/claude-tech-squad/bin/squad_cli/test_gate.py`

- [ ] **Step 1: Write minimal implementation**

Write to `plugins/claude-tech-squad/bin/squad_cli/test_gate.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class TestInfraStatus(str, Enum):
    PRESENT_AND_CONFIGURED = "present"
    PARTIAL = "partial"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class GateVerdict(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCKING = "blocking"


@dataclass
class StackFingerprint:
    language: str
    framework: str | None = None
    test_framework: str | None = None
    test_dirs: list[str] = field(default_factory=list)


@dataclass
class UnpairedFile:
    path: str
    reason: str = "no_paired_test_found"


NON_CODE_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".lock"}


def _is_test_file(path: str, language: str) -> bool:
    name = Path(path).name
    if language == "python":
        return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in path
    if language in {"typescript", "javascript"}:
        return ".test." in name or ".spec." in name or "__tests__" in path
    if language == "go":
        return name.endswith("_test.go")
    return False


def _is_non_code(path: str) -> bool:
    return Path(path).suffix in NON_CODE_EXTENSIONS


def _candidate_test_paths(prod_path: str, language: str) -> list[str]:
    p = Path(prod_path)
    stem = p.stem
    parent = p.parent
    if language == "python":
        return [
            f"tests/test_{stem}.py",
            f"tests/{parent.name}/test_{stem}.py",
            f"{parent}/test_{stem}.py",
            f"{parent}/{stem}_test.py",
        ]
    if language in {"typescript", "javascript"}:
        ext = p.suffix
        return [
            f"{parent}/{stem}.test{ext}",
            f"{parent}/{stem}.spec{ext}",
            f"{parent}/__tests__/{stem}.test{ext}",
        ]
    if language == "go":
        return [f"{parent}/{stem}_test.go"]
    return []


def check_paired_tests(
    diff_files: Iterable[str],
    stack: StackFingerprint,
    repo_root: Path,
) -> list[UnpairedFile]:
    unpaired: list[UnpairedFile] = []
    for f in diff_files:
        if _is_non_code(f) or _is_test_file(f, stack.language):
            continue
        candidates = _candidate_test_paths(f, stack.language)
        if not any((repo_root / c).exists() for c in candidates):
            unpaired.append(UnpairedFile(path=f))
    return unpaired
```

- [ ] **Step 2: Run tests and confirm they pass**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_test_gate.py -v`
Expected: 4 passed.

- [ ] **Step 3: Commit**

```bash
git add plugins/claude-tech-squad/bin/squad_cli/test_gate.py plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py
git commit -m "feat: add test_gate.check_paired_tests with python/ts/go heuristics"
```

---

### Task B4: Add `evaluate_gate` and verdict logic

**Files:**
- Modify: `plugins/claude-tech-squad/bin/squad_cli/test_gate.py`
- Modify: `plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py`

- [ ] **Step 1: Append failing tests for `evaluate_gate`**

Append to `tests/test_test_gate.py`:

```python
from squad_cli.test_gate import evaluate_gate, GatePolicy


def make_policy(level="blocking", coverage_threshold=0.02):
    return GatePolicy(enforce_level=level, coverage_warning_threshold=coverage_threshold)


def test_pass_when_no_unpaired_no_drop():
    verdict = evaluate_gate(unpaired=[], coverage_delta=0.0, policy=make_policy())
    assert verdict == GateVerdict.PASS


def test_blocking_when_unpaired_and_blocking_level():
    verdict = evaluate_gate(
        unpaired=[UnpairedFile(path="src/x.py")], coverage_delta=0.0, policy=make_policy("blocking")
    )
    assert verdict == GateVerdict.BLOCKING


def test_warning_when_unpaired_in_shadow_mode():
    verdict = evaluate_gate(
        unpaired=[UnpairedFile(path="src/x.py")], coverage_delta=0.0, policy=make_policy("warning")
    )
    assert verdict == GateVerdict.WARNING


def test_warning_on_coverage_drop_above_threshold():
    verdict = evaluate_gate(unpaired=[], coverage_delta=-0.05, policy=make_policy())
    assert verdict == GateVerdict.WARNING


def test_pass_on_small_coverage_drop():
    verdict = evaluate_gate(unpaired=[], coverage_delta=-0.01, policy=make_policy())
    assert verdict == GateVerdict.PASS
```

- [ ] **Step 2: Run; expect ImportError on `evaluate_gate`, `GatePolicy`**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_test_gate.py -v`

- [ ] **Step 3: Implement in `test_gate.py`**

Append to `test_gate.py`:

```python
@dataclass
class GatePolicy:
    enforce_level: str = "blocking"
    coverage_warning_threshold: float = 0.02


def evaluate_gate(
    unpaired: list[UnpairedFile],
    coverage_delta: float,
    policy: GatePolicy,
) -> GateVerdict:
    if unpaired:
        if policy.enforce_level == "blocking":
            return GateVerdict.BLOCKING
        return GateVerdict.WARNING
    if coverage_delta < 0 and abs(coverage_delta) > policy.coverage_warning_threshold:
        return GateVerdict.WARNING
    return GateVerdict.PASS
```

- [ ] **Step 4: Run and confirm all green**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/ -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/bin/squad_cli/test_gate.py plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py
git commit -m "feat: add evaluate_gate verdict logic"
```

---

### Task B5: Wire `test-gate evaluate` CLI subcommand

**Files:**
- Modify: `plugins/claude-tech-squad/bin/squad_cli/cli.py`

- [ ] **Step 1: Read existing CLI structure**

Run: `grep -n "@click\|def main\|def [a-z_]*(" plugins/claude-tech-squad/bin/squad_cli/cli.py | head -30`

- [ ] **Step 2: Add subcommand**

Append a new click command group `test_gate` with `evaluate` subcommand. Pattern (adapt to actual click setup detected in Step 1):

```python
import subprocess
from pathlib import Path
import yaml

from squad_cli.test_gate import (
    StackFingerprint,
    GatePolicy,
    GateVerdict,
    check_paired_tests,
    evaluate_gate,
)

@main.group("test-gate")
def test_gate_group():
    """Mandatory test gate operations."""

@test_gate_group.command("evaluate")
@click.option("--skill", required=True)
@click.option("--run-id", required=True)
@click.option("--repo-root", default=".", type=click.Path(exists=True))
def evaluate(skill: str, run_id: str, repo_root: str):
    repo = Path(repo_root).resolve()
    diff = subprocess.check_output(
        ["git", "-C", str(repo), "diff", "--name-only", "HEAD"], text=True
    ).strip().splitlines()
    policy_yaml = yaml.safe_load(
        (repo / "plugins/claude-tech-squad/runtime-policy.yaml").read_text()
    )
    mtg = policy_yaml.get("mandatory_test_gate", {})
    if skill not in mtg.get("skills_in_scope", []):
        click.echo(f"test-gate: {skill} not in scope; skip")
        raise SystemExit(0)
    # Detect stack via existing helper if available; fallback to python
    try:
        from squad_cli.stack_detect import detect_stack
        stack = detect_stack(repo)
    except Exception:
        stack = StackFingerprint(language="python")
    unpaired = check_paired_tests(diff, stack, repo)
    policy = GatePolicy(
        enforce_level=mtg.get("enforce_level", "warning"),
        coverage_warning_threshold=mtg.get("coverage_warning_threshold", 0.02),
    )
    verdict = evaluate_gate(unpaired, 0.0, policy)
    click.echo(f"test-gate verdict={verdict.value} unpaired={[u.path for u in unpaired]}")
    if verdict == GateVerdict.BLOCKING:
        raise SystemExit(2)
    raise SystemExit(0)
```

- [ ] **Step 3: Smoke-test the subcommand on this very repo**

Run: `plugins/claude-tech-squad/bin/squad-cli test-gate evaluate --skill implement --run-id smoke-1 --repo-root .`
Expected: exits 0 (warning mode; current diff state may produce verdict=warning or pass).

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-tech-squad/bin/squad_cli/cli.py
git commit -m "feat: add 'test-gate evaluate' CLI subcommand"
```

---

### Task B6: Create `hooks/test-gate.sh`

**Files:**
- Create: `plugins/claude-tech-squad/hooks/test-gate.sh`

- [ ] **Step 1: Write the hook**

Write to `plugins/claude-tech-squad/hooks/test-gate.sh`:

```bash
#!/usr/bin/env bash
# PostToolUse hook for the mandatory test gate.
# Fires after Agent calls; filters early so it only acts when relevant.

set -euo pipefail

# Only act for Agent tool calls
[[ "${CLAUDE_TOOL_NAME:-}" == "Agent" ]] || exit 0

SUBAGENT="${CLAUDE_TOOL_INPUT_subagent_type:-}"
SKILL="${CLAUDE_SKILL_NAME:-}"
RUN_ID="${CLAUDE_RUN_ID:-unknown}"

# Only act when the just-completed agent is test-automation-engineer
[[ "$SUBAGENT" == "claude-tech-squad:test-automation-engineer" ]] || exit 0

# Only act for in-scope skills (defensive — runtime-policy is the source of truth)
case "$SKILL" in
    squad|implement|refactor|bug-fix|hotfix) ;;
    *) exit 0 ;;
esac

REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
SQUAD_CLI="${REPO_ROOT}/plugins/claude-tech-squad/bin/squad-cli"

if [[ ! -x "$SQUAD_CLI" ]]; then
    echo "test-gate: squad-cli not found at $SQUAD_CLI" >&2
    exit 0  # Fail open if tooling missing
fi

"$SQUAD_CLI" test-gate evaluate --skill "$SKILL" --run-id "$RUN_ID" --repo-root "$REPO_ROOT"
RC=$?
case $RC in
    0) exit 0 ;;
    2) echo "test-gate: BLOCKING — production file without paired test" >&2; exit 2 ;;
    *) echo "test-gate: internal error rc=$RC" >&2; exit 1 ;;
esac
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x plugins/claude-tech-squad/hooks/test-gate.sh`

- [ ] **Step 3: Smoke-test by sourcing env vars and running**

Run:
```bash
CLAUDE_TOOL_NAME=Agent \
  CLAUDE_TOOL_INPUT_subagent_type=claude-tech-squad:test-automation-engineer \
  CLAUDE_SKILL_NAME=implement \
  CLAUDE_RUN_ID=smoke-1 \
  CLAUDE_PROJECT_ROOT="$(pwd)" \
  plugins/claude-tech-squad/hooks/test-gate.sh
```
Expected: prints `test-gate verdict=...`; exits 0 in warning mode.

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-tech-squad/hooks/test-gate.sh
git commit -m "feat: add PostToolUse hooks/test-gate.sh"
```

---

### Task B7: Register hook in `settings-template.json` and document

**Files:**
- Modify: `plugins/claude-tech-squad/hooks/settings-template.json`
- Modify: `plugins/claude-tech-squad/hooks/README.md`

- [ ] **Step 1: Read existing template**

Run: `cat plugins/claude-tech-squad/hooks/settings-template.json`

- [ ] **Step 2: Add PostToolUse entry**

Add (or extend if PostToolUse already present) the `hooks.PostToolUse` array with an entry that runs `hooks/test-gate.sh` when the tool is `Agent`. Exact JSON shape depends on the existing template; mirror the pattern of `pre-tool-guard.sh`.

- [ ] **Step 3: Update README**

Append to `plugins/claude-tech-squad/hooks/README.md`:

```markdown
### test-gate.sh (PostToolUse)

Fires after every `Agent` tool call. Acts only when:
- the tool was `Agent`,
- the `subagent_type` is `claude-tech-squad:test-automation-engineer`,
- the active skill is in `mandatory_test_gate.skills_in_scope`.

Calls `squad-cli test-gate evaluate` and propagates the verdict via exit code:
- `0` — PASS or WARNING (continue)
- `2` — BLOCKING (halt pipeline)

See `runtime-policy.yaml#mandatory_test_gate` and `docs/superpowers/specs/2026-04-26-mandatory-test-automation-design.md`.
```

- [ ] **Step 4: Validate JSON parses**

Run: `python3 -c "import json; json.load(open('plugins/claude-tech-squad/hooks/settings-template.json'))"`

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/hooks/settings-template.json plugins/claude-tech-squad/hooks/README.md
git commit -m "feat: register test-gate.sh in settings template + docs"
```

---

### Task B8: Add SEP log fields and run full validation

**Files:**
- Modify: `plugins/claude-tech-squad/runtime-policy.yaml` (extend `observability.sep_log_schema`)

- [ ] **Step 1: Find sep_log_schema**

Run: `grep -n "sep_log_schema" plugins/claude-tech-squad/runtime-policy.yaml`

- [ ] **Step 2: Add `test_gate` block to required schema**

Under `observability.sep_log_schema`, add fields documenting that runs in scope SHOULD include a `test_gate` block with: `verdict`, `enforce_level`, `unpaired_files`, `coverage_before`, `coverage_after`, `coverage_delta`, `exemptions_applied`, `tech_debt_registered`, `gate_duration_ms`.

- [ ] **Step 3: Update smoke-test.sh assertions**

Add to `scripts/smoke-test.sh` an assertion that `hooks/test-gate.sh` exists and is executable, and that `squad-cli test-gate --help` returns 0.

```bash
[[ -x plugins/claude-tech-squad/hooks/test-gate.sh ]] \
    || { echo "FAIL: hooks/test-gate.sh not executable"; exit 1; }
plugins/claude-tech-squad/bin/squad-cli test-gate --help >/dev/null \
    || { echo "FAIL: test-gate subcommand missing"; exit 1; }
```

- [ ] **Step 4: Run full validation**

Run: `bash scripts/validate.sh && bash scripts/smoke-test.sh && bash scripts/dogfood.sh`
Expected: all pass.

- [ ] **Step 5: Commit and tag PR-B endpoint**

```bash
git add plugins/claude-tech-squad/runtime-policy.yaml scripts/smoke-test.sh
git commit -m "feat: add test_gate SEP log schema + smoke assertions"
git tag --no-sign mandatory-test-automation-pr-b
```

PR-B complete. Open PR with title `feat: runtime test gate hook + squad-cli evaluate (Pillar B, shadow mode)`.

---

# PHASE C — Pillar C: Bootstrap (PR-C, Class C)

End state: preflight detects repos without test infra; first contact triggers human gate with proposal; subsequent runs operate in incremental-automatic mode.

### Task C1: Add `detect_test_infra` to `test_gate.py`

**Files:**
- Modify: `plugins/claude-tech-squad/bin/squad_cli/test_gate.py`
- Modify: `plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/test_test_gate.py`:

```python
from squad_cli.test_gate import detect_test_infra


def test_infra_present_python_pytest(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x(): ...\n")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    status = detect_test_infra(tmp_path, make_stack())
    assert status == TestInfraStatus.PRESENT_AND_CONFIGURED


def test_infra_absent_python(tmp_path: Path):
    (tmp_path / "src").mkdir()
    status = detect_test_infra(tmp_path, make_stack())
    assert status == TestInfraStatus.ABSENT


def test_infra_partial_when_dir_only(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    status = detect_test_infra(tmp_path, make_stack())
    assert status == TestInfraStatus.PARTIAL
```

- [ ] **Step 2: Run; expect import or attribute error**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_test_gate.py::test_infra_present_python_pytest -v`

- [ ] **Step 3: Implement `detect_test_infra`**

Append to `test_gate.py`:

```python
def detect_test_infra(repo_root: Path, stack: StackFingerprint) -> TestInfraStatus:
    if stack.language == "python":
        has_dir = (repo_root / "tests").is_dir() or any(
            (repo_root / d).is_dir() for d in stack.test_dirs
        )
        has_runner = any(
            (repo_root / cfg).exists()
            for cfg in ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini")
        )
        if has_dir and has_runner:
            test_files = list((repo_root / "tests").rglob("test_*.py")) if has_dir else []
            return (
                TestInfraStatus.PRESENT_AND_CONFIGURED
                if test_files
                else TestInfraStatus.PARTIAL
            )
        if has_dir or has_runner:
            return TestInfraStatus.PARTIAL
        return TestInfraStatus.ABSENT
    if stack.language in {"typescript", "javascript"}:
        pkg = repo_root / "package.json"
        if pkg.exists() and "jest" in pkg.read_text() or "vitest" in pkg.read_text() if pkg.exists() else False:
            return TestInfraStatus.PRESENT_AND_CONFIGURED
        return TestInfraStatus.ABSENT
    return TestInfraStatus.UNKNOWN
```

- [ ] **Step 4: Run all tests green**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/ -v`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/bin/squad_cli/test_gate.py plugins/claude-tech-squad/bin/squad_cli/tests/test_test_gate.py
git commit -m "feat: detect_test_infra for python/ts/js"
```

---

### Task C2: Extend `task_memory.py` with bootstrap state keys

**Files:**
- Modify: `plugins/claude-tech-squad/bin/squad_cli/task_memory.py`
- Create: `plugins/claude-tech-squad/bin/squad_cli/tests/test_task_memory.py`

- [ ] **Step 1: Read current task_memory.py**

Run: `cat plugins/claude-tech-squad/bin/squad_cli/task_memory.py`

- [ ] **Step 2: Write failing test**

Write to `tests/test_task_memory.py`:

```python
from squad_cli.task_memory import TaskMemory


def test_bootstrap_keys_default_to_none(tmp_path):
    tm = TaskMemory(repo_root=tmp_path)
    assert tm.get("test_infra_bootstrapped") is None
    assert tm.get("debt_acknowledged") is None


def test_set_and_get_bootstrap_state(tmp_path):
    tm = TaskMemory(repo_root=tmp_path)
    tm.set("test_infra_bootstrapped", True)
    assert tm.get("test_infra_bootstrapped") is True


def test_persistence_across_instances(tmp_path):
    TaskMemory(repo_root=tmp_path).set("test_infra_bootstrapped", True)
    assert TaskMemory(repo_root=tmp_path).get("test_infra_bootstrapped") is True
```

- [ ] **Step 3: Run and confirm failure**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_task_memory.py -v`
Expected: failure if `TaskMemory` API does not yet exist.

- [ ] **Step 4: Implement minimal `TaskMemory` class**

Add to `task_memory.py` (or adapt existing class):

```python
import json
from pathlib import Path


class TaskMemory:
    def __init__(self, repo_root: Path):
        self.path = Path(repo_root) / "ai-docs" / ".squad-log" / "task-memory.json"

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2))

    def get(self, key: str, default=None):
        return self._read().get(key, default)

    def set(self, key: str, value) -> None:
        data = self._read()
        data[key] = value
        self._write(data)
```

- [ ] **Step 5: Run tests green**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_task_memory.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/claude-tech-squad/bin/squad_cli/task_memory.py plugins/claude-tech-squad/bin/squad_cli/tests/test_task_memory.py
git commit -m "feat: TaskMemory persistence with test_infra_bootstrapped key"
```

---

### Task C3: Add `check_test_infra` step to `preflight.py`

**Files:**
- Modify: `plugins/claude-tech-squad/bin/squad_cli/preflight.py`
- Create: `plugins/claude-tech-squad/bin/squad_cli/tests/test_preflight_test_infra.py`

- [ ] **Step 1: Read preflight structure**

Run: `grep -n "^def \|^class " plugins/claude-tech-squad/bin/squad_cli/preflight.py`

- [ ] **Step 2: Write failing test**

Write to `tests/test_preflight_test_infra.py`:

```python
from pathlib import Path
from squad_cli.preflight import check_test_infra
from squad_cli.test_gate import StackFingerprint, TestInfraStatus


def make_stack():
    return StackFingerprint(language="python", test_framework="pytest", test_dirs=["tests"])


def test_returns_proceed_when_infra_present(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x(): ...\n")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    decision = check_test_infra(tmp_path, make_stack(), bootstrapped=False, debt_acknowledged=False)
    assert decision.action == "proceed"


def test_returns_human_gate_on_first_contact(tmp_path: Path):
    decision = check_test_infra(tmp_path, make_stack(), bootstrapped=False, debt_acknowledged=False)
    assert decision.action == "human_gate"
    assert decision.proposal is not None


def test_returns_incremental_when_already_acknowledged(tmp_path: Path):
    decision = check_test_infra(tmp_path, make_stack(), bootstrapped=False, debt_acknowledged=True)
    assert decision.action == "incremental_automatic"


def test_returns_unknown_stack_gate(tmp_path: Path):
    decision = check_test_infra(
        tmp_path, StackFingerprint(language="ruby"), bootstrapped=False, debt_acknowledged=False
    )
    assert decision.action == "human_gate_unknown"
```

- [ ] **Step 3: Run and confirm failures**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_preflight_test_infra.py -v`

- [ ] **Step 4: Implement `check_test_infra`**

Append to `preflight.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from squad_cli.test_gate import detect_test_infra, StackFingerprint, TestInfraStatus


@dataclass
class TestInfraDecision:
    action: str  # proceed | human_gate | incremental_automatic | human_gate_unknown
    proposal: dict | None = None


def check_test_infra(
    repo_root: Path,
    stack: StackFingerprint,
    bootstrapped: bool,
    debt_acknowledged: bool,
) -> TestInfraDecision:
    status = detect_test_infra(repo_root, stack)
    if status == TestInfraStatus.UNKNOWN:
        return TestInfraDecision(action="human_gate_unknown")
    if status == TestInfraStatus.PRESENT_AND_CONFIGURED:
        return TestInfraDecision(action="proceed")
    # ABSENT or PARTIAL
    if not bootstrapped and not debt_acknowledged:
        return TestInfraDecision(
            action="human_gate",
            proposal={
                "stack": stack.language,
                "framework_recommended": stack.test_framework or "pytest",
                "structure": ["tests/unit/", "tests/integration/"],
                "ci_step_required": True,
            },
        )
    return TestInfraDecision(action="incremental_automatic")
```

- [ ] **Step 5: Tests green**

Run: `cd plugins/claude-tech-squad/bin && ../../../squad-cli/venv/bin/pytest squad_cli/tests/test_preflight_test_infra.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/claude-tech-squad/bin/squad_cli/preflight.py plugins/claude-tech-squad/bin/squad_cli/tests/test_preflight_test_infra.py
git commit -m "feat: preflight check_test_infra with decision matrix"
```

---

### Task C4: Create `/test-bootstrap` skill

**Files:**
- Create: `plugins/claude-tech-squad/skills/test-bootstrap/SKILL.md`

- [ ] **Step 1: Use an existing skill as template**

Run: `cp plugins/claude-tech-squad/skills/onboarding/SKILL.md /tmp/template.md && head -40 /tmp/template.md`

- [ ] **Step 2: Author SKILL.md**

Write to `plugins/claude-tech-squad/skills/test-bootstrap/SKILL.md`:

```markdown
---
name: test-bootstrap
description: Opt-in standalone skill that bootstraps test infrastructure in a repository that lacks it. Detects stack, proposes a framework + structure + CI step, and writes characterization tests for hotspots. Trigger only via /claude-tech-squad:test-bootstrap or from the first-contact human gate of an in-scope skill.
---

# /claude-tech-squad:test-bootstrap

## Preflight Gate
- Confirm repo lacks test infrastructure (`test_gate.detect_test_infra` returns ABSENT or PARTIAL).
- Confirm operator approved the proposal (interactive).
- Identify hotspots: top-10 files modified in last 90 days via
  `git log --since="90 days ago" --pretty=format: --name-only | sort | uniq -c | sort -rn | head -10`.

## Agent Result Contract (ARC)
result_contract:
  - framework_installed: string
  - structure_created: list[string]
  - characterization_tests: list[string]
  - ci_step_added: bool
verification_checklist:
  - [ ] framework dependency installed and importable
  - [ ] tests/ directory committed
  - [ ] at least 3 characterization tests pass against current code
  - [ ] CI pipeline runs the new test command

## Runtime Resilience Contract
Inherits failure_handling and fallback_matrix from runtime-policy.yaml. If `test-automation-engineer` exhausts retries, fallback to `qa-tester`.

### Checkpoint / Resume Rules
Checkpoints: `bootstrap.framework_chosen`, `bootstrap.tests_written`, `bootstrap.ci_added`. On resume, re-read each checkpoint and skip already-completed steps.

## Progressive Disclosure — Context Digest Protocol
Each agent receives only the slice it needs: stack fingerprint, hotspot list, and the proposal accepted by the operator.

## Visual Reporting Contract
Render teammate cards for `test-planner`, `test-automation-engineer`, `ci-cd`. Pipeline board shows: detect → propose → install → write tests → CI step → review.

## Pipeline

1. Spawn `test-planner` (`subagent_type: "claude-tech-squad:test-planner"`) to define framework, structure, coverage policy.
2. Spawn `test-automation-engineer` (`subagent_type: "claude-tech-squad:test-automation-engineer"`) to install framework, scaffold structure, write characterization tests for hotspots.
3. Spawn `ci-cd` (`subagent_type: "claude-tech-squad:ci-cd"`) to add the test step to existing CI configs.
4. Human gate — operator reviews diff before commit.
5. Persist `task_memory.set("test_infra_bootstrapped", true)` and write SEP log.
```

- [ ] **Step 3: Add to required-skills list if applicable**

Run: `grep -n "REQUIRED_SKILLS\|test-bootstrap" scripts/validate.sh`. If REQUIRED_SKILLS is opt-in, do not add — this skill is operator-triggered, not part of the mandatory skill set.

- [ ] **Step 4: Run validate.sh**

Run: `bash scripts/validate.sh`
Expected: pass (skill not in mandatory list, but its SKILL.md has the contract elements).

- [ ] **Step 5: Commit**

```bash
git add plugins/claude-tech-squad/skills/test-bootstrap/SKILL.md
git commit -m "feat: add /test-bootstrap opt-in skill"
```

---

### Task C5: Add `no-test-infra` dogfood fixture

**Files:**
- Create: `fixtures/dogfooding/no-test-infra/README.md`
- Create: `fixtures/dogfooding/no-test-infra/src/orders/models.py`
- Create: `fixtures/dogfooding/no-test-infra/src/orders/__init__.py`
- Modify: `fixtures/dogfooding/scenarios.json`

- [ ] **Step 1: Inspect existing fixture**

Run: `cat fixtures/dogfooding/scenarios.json && ls fixtures/dogfooding/layered-monolith`

- [ ] **Step 2: Build minimal Python package without tests**

Write `fixtures/dogfooding/no-test-infra/README.md`:

```markdown
# no-test-infra fixture

Simulates a Python project with production code and no test infrastructure.
Used by dogfood golden runs for `/test-bootstrap` and the first-contact gate.
```

Write `fixtures/dogfooding/no-test-infra/src/orders/__init__.py`:

```python
```

Write `fixtures/dogfooding/no-test-infra/src/orders/models.py`:

```python
class Order:
    def __init__(self, total: float):
        self.total = total

    def is_eligible_for_discount(self) -> bool:
        return self.total > 100.0
```

- [ ] **Step 3: Register the scenario**

Edit `fixtures/dogfooding/scenarios.json`. Add a new entry following the existing schema. Confirm count constraint — CLAUDE.md says "exactly 4". Update the validation if it was hard-coded to 4. Run:

```bash
grep -n "scenarios.json" scripts/validate.sh scripts/dogfood.sh
```

If the count `== 4` is hard-coded, change to `>= 4` and add the fixture.

- [ ] **Step 4: Update dogfood scenario assertions**

Add an assertion path `fixtures/dogfooding/no-test-infra/src/orders/models.py` to `scripts/dogfood.sh` integrity check.

- [ ] **Step 5: Run dogfood.sh**

Run: `bash scripts/dogfood.sh`
Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add fixtures/dogfooding/no-test-infra/ fixtures/dogfooding/scenarios.json scripts/validate.sh scripts/dogfood.sh
git commit -m "feat: add no-test-infra dogfood fixture"
```

---

### Task C6: Add `bootstrap_policy` enforcement in validate.sh + final validation

**Files:**
- Modify: `scripts/validate.sh`
- Modify: `scripts/smoke-test.sh`

- [ ] **Step 1: Extend `validate_test_gate_contract` to also verify bootstrap_policy keys**

In the function added in Task A3, add at the bottom:

```bash
local policy_yaml="plugins/claude-tech-squad/runtime-policy.yaml"
for key in first_contact subsequent unknown_stack; do
    grep -q "  ${key}:" "$policy_yaml" \
        || fail "runtime-policy.yaml mandatory_test_gate.bootstrap_policy missing '${key}'"
done
```

- [ ] **Step 2: Smoke-test assertion that test-bootstrap skill exists**

Append to `scripts/smoke-test.sh`:

```bash
[[ -f plugins/claude-tech-squad/skills/test-bootstrap/SKILL.md ]] \
    || { echo "FAIL: /test-bootstrap skill missing"; exit 1; }
```

- [ ] **Step 3: Run full validation suite**

Run: `bash scripts/validate.sh && bash scripts/smoke-test.sh && bash scripts/dogfood.sh`
Expected: all pass.

- [ ] **Step 4: Commit and tag PR-C endpoint**

```bash
git add scripts/validate.sh scripts/smoke-test.sh
git commit -m "feat: enforce bootstrap_policy keys + smoke-test test-bootstrap presence"
git tag --no-sign mandatory-test-automation-pr-c
```

PR-C complete. Open PR with title `feat: bootstrap detection + /test-bootstrap skill (Pillar C)`.

---

# After PR-B is merged and shadow release passes

### Task D1 (follow-up minimal PR): Flip `enforce_level` to `blocking`

**Files:**
- Modify: `plugins/claude-tech-squad/runtime-policy.yaml`

- [ ] **Step 1: Confirm at least 1 release in shadow mode produced no false positives**

Run: review `ai-docs/.squad-log/` for `test_gate.verdict` entries; confirm no `BLOCKING` would have fired on legitimate work.

- [ ] **Step 2: Edit policy**

Change `enforce_level: warning` to `enforce_level: blocking` in `runtime-policy.yaml`.

- [ ] **Step 3: Run validation**

Run: `bash scripts/validate.sh && bash scripts/smoke-test.sh`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add plugins/claude-tech-squad/runtime-policy.yaml
git commit -m "feat: flip mandatory_test_gate to blocking enforcement"
```

---

## Self-Review Notes

- **Spec coverage:** Sections 5–10 of the spec are each implemented by specific tasks (5→A1–A9, 6→B1–B8, 7→C1–C5, 8→edge cases live in test_gate.py heuristics + hotfix exemption A8, 9→B7/B8 SEP log fields, 10→PR sequencing maps to Phases A/B/C).
- **Placeholder scan:** No "TBD"/"TODO". One intentional ambiguity flagged inline: settings-template.json shape (Task B7 Step 2) depends on existing format — engineer must mirror `pre-tool-guard.sh` pattern they observe in the file.
- **Type consistency:** `StackFingerprint`, `GatePolicy`, `GateVerdict`, `UnpairedFile`, `TestInfraDecision`, `TaskMemory` are defined where first used; later tasks reference them by exact name.
- **Known follow-ups:** D1 is the post-shadow flip and lives outside the three-PR sequence by design.
