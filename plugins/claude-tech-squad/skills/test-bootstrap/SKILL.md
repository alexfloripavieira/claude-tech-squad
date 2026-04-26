---
name: test-bootstrap
description: Opt-in standalone skill that bootstraps test infrastructure in a repository that lacks it. Detects stack, proposes a framework + structure + CI step, and writes characterization tests for hotspots. Trigger only via /claude-tech-squad:test-bootstrap or from the first-contact human gate of an in-scope skill.
---

# /claude-tech-squad:test-bootstrap

## Global Safety Contract

Do not push, merge, or delete files without explicit operator approval. Every step must be visible. Failures escalate to a human gate; silent skips are forbidden.

## Operator Visibility Contract

Every phase emits one of: `[Phase Start]`, `[Phase Done]`, `[Teammate Spawned]`, `[Gate]`, `[Checkpoint Saved]`. Operator can interrupt at any gate.

## Preflight Gate

- Confirm repo lacks test infrastructure (`test_gate.detect_test_infra` returns `ABSENT` or `PARTIAL`).
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

Inherits `failure_handling` and `fallback_matrix` from `runtime-policy.yaml`. If `test-automation-engineer` exhausts retries, fallback to `qa-tester`.

### Checkpoint / Resume Rules

Checkpoints: `bootstrap.framework_chosen`, `bootstrap.tests_written`, `bootstrap.ci_added`. On resume, re-read each checkpoint and skip already-completed steps.

## Progressive Disclosure — Context Digest Protocol

Each agent receives only the slice it needs: stack fingerprint, hotspot list, and the proposal accepted by the operator.

## Visual Reporting Contract

Render teammate cards for `test-planner`, `test-automation-engineer`, `ci-cd`. Pipeline board shows: detect → propose → install → write tests → CI step → review.

## Pipeline

1. Spawn `test-planner`:

```
Agent(team_name="bootstrap-team", name="test-planner", subagent_type="claude-tech-squad:test-planner",
  prompt="Define framework, directory structure, and coverage policy for this stack. Inputs: stack fingerprint, hotspot list. Output: bootstrap proposal.")
```

2. Spawn `test-automation-engineer`:

```
Agent(team_name="bootstrap-team", name="test-automation-engineer", subagent_type="claude-tech-squad:test-automation-engineer",
  prompt="Install the chosen framework, scaffold the agreed directory structure, and write characterization tests for the listed hotspots. Run the test command; confirm green.")
```

3. Spawn `ci-cd`:

```
Agent(team_name="bootstrap-team", name="ci-cd", subagent_type="claude-tech-squad:ci-cd",
  prompt="Add a test step to the existing CI configuration (.github/workflows/, .gitlab-ci.yml, or equivalent). Do NOT modify deployment steps.")
```

4. **Human gate** — operator reviews diff before commit.
5. Persist `task_memory.set("test_infra_bootstrapped", true)` and write SEP log.
