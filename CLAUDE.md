# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is the source repository for the `claude-tech-squad` Claude Code plugin — a marketplace-installable squad of 61 specialist agents and 20 skills for software delivery. It is not a software project being built; it is the plugin itself.

## Validation

```bash
bash scripts/validate.sh                      # JSON validity, version consistency, agent/skill contracts
bash scripts/smoke-test.sh                    # lightweight structural smoke test
bash scripts/dogfood.sh                       # validate local dogfooding pack
bash scripts/dogfood-report.sh --schema-only  # validate golden-run contract schema
```

All four must pass before any PR is merged. For Class C/D changes (orchestration or release-critical), also run real golden runs and validate with `bash scripts/dogfood-report.sh` (no flag).

## Release

Releases are fully automated via GitHub Actions on push to `main`. The pipeline:
- derives the semver bump from conventional commit subjects
- updates `CHANGELOG.md`, `.claude-plugin/marketplace.json`, `plugins/claude-tech-squad/.claude-plugin/plugin.json`, and `docs/MANUAL.md`
- commits the generated metadata back to `main` with subject `chore: prepare release vX.Y.Z`
- creates the git tag and GitHub Release

**Do not hand-edit** `CHANGELOG.md`, `plugin.json`, `marketplace.json`, or `MANUAL.md` for routine releases — automation owns them.

PR titles and squash-merge subjects must follow conventional commits (`feat:`, `fix:`, `chore:`, `type!:`) because the semver bump is derived from them.

Emergency fallback: `bash scripts/release.sh`

## Repository Structure

```
.claude-plugin/marketplace.json              # marketplace registry (owned by automation)
plugins/claude-tech-squad/
  .claude-plugin/plugin.json                 # plugin manifest (owned by automation)
  agents/*.md                                # 61 specialist agent definitions
  skills/*/SKILL.md                          # 20 skill/workflow definitions
  runtime-policy.yaml                        # retry budgets, severity policy, fallback matrix, checkpoint rules
scripts/                                     # validate, smoke-test, dogfood, release automation
fixtures/dogfooding/                         # three dogfood scenarios: layered-monolith, hexagonal-billing, hotfix-checkout
fixtures/dogfooding/scenarios.json           # scenario manifest consumed by dogfood.sh
ai-docs/.squad-log/                          # runtime SEP logs (gitignored)
ai-docs/dogfood-runs/                        # golden-run captures (gitignored)
templates/                                   # rfc-template, service-readiness-review, golden-run-scorecard
docs/                                        # operator documentation
```

## Agent and Skill Contracts

Every agent `.md` file must have:
- `name:` and `description:` frontmatter
- `## Result Contract` section
- `## Documentation Standard — Context7 First, Repository Fallback` section

The core skills (`discovery`, `implement`, `squad`) additionally require:
- `## Agent Result Contract (ARC)`
- `### Preflight Gate`
- `## Runtime Resilience Contract`
- `### Checkpoint / Resume Rules`

`scripts/validate.sh` enforces all of these structurally.

## Architectural Constraints (enforced by validate.sh)

- **No agent self-chaining**: agents must not include `subagent_type` in their definition. Only `incident-manager` is exempt (it orchestrates fan-out during active incidents).
- **No Agent tool in frontmatter tools list**: only `incident-manager` may expose the `Agent` tool.
- **All `subagent_type` references must stay in the `claude-tech-squad:` namespace** — no cross-plugin or bare agent references.
- **Version triplet must be consistent**: `marketplace.json` version == `plugin.json` version == `docs/MANUAL.md` version.

## Change Classes

| Class | Scope | Golden runs required |
|---|---|---|
| A | Prompt or doc only | No |
| B | Workflow contract change | No (schema validation sufficient) |
| C | Orchestration or specialist model change | Yes, when behavior changed materially |
| D | Release-critical change | Yes |

## Golden Runs

```bash
bash scripts/start-golden-run.sh <scenario-id> <operator>  # scaffold capture
# execute scenario in Claude, paste trace and output into generated files
bash scripts/dogfood-report.sh                             # validate
```

Scenario IDs are defined in `fixtures/dogfooding/scenarios.json`.

## runtime-policy.yaml

Central policy consumed by skills at runtime. Contains:
- `retry_budgets`: max cycles for review, QA, conformance, quality-fix, UAT
- `severity_policy`: blocking vs warning vs info issue classification
- `fallback_matrix`: per-skill agent fallback chains (e.g. `pm → po`, `reviewer → code-quality`)
- `checkpoint_resume`: checkpoint names and resume rules for `discovery`, `implement`, `squad`
- `reliability_metrics`: fields tracked in SEP logs

Changes here affect all three core skills simultaneously.
