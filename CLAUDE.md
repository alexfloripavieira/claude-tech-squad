# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repository is

This is the source repository for the `claude-tech-squad` Claude Code plugin — a full software delivery squad of 61 specialist agents and 20 skills that replicate big tech engineering pipelines. The repository ships a marketplace manifest, the plugin itself, a validation ladder, and a dogfooding pack with golden run support.

There is no application server, no database, and no build step. The artifacts are Markdown files (agents, skills), a YAML policy file, and JSON manifests.

---

## Validation commands

Run these before every PR. The PR template requires all four to pass.

```bash
bash scripts/validate.sh                    # structural: files, versions, agent/skill contracts
bash scripts/smoke-test.sh                  # full ladder: validate + dogfood + release bundle
bash scripts/dogfood.sh                     # fixture integrity check
bash scripts/dogfood-report.sh --schema-only  # golden run schema validation
```

To see the fixture prompts without running them:

```bash
bash scripts/dogfood.sh --print-prompts
```

To scaffold a golden run for a scenario:

```bash
bash scripts/start-golden-run.sh <scenario-id> <operator>
# scenario-id: layered-monolith | hexagonal-billing | hotfix-checkout
```

To run the full golden run report (requires real captured runs in `ai-docs/dogfood-runs/`):

```bash
bash scripts/dogfood-report.sh
```

---

## What validate.sh enforces

`validate.sh` is the authoritative contract checker. It will fail if any of these are violated:

**Version consistency** — `marketplace.json`, `plugins/claude-tech-squad/.claude-plugin/plugin.json`, and `docs/MANUAL.md` must all carry the same version string. Editing one without updating the others breaks validation.

**Agent contract** — every `.md` in `plugins/claude-tech-squad/agents/` must have:
- `name:` and `description:` frontmatter
- `## Result Contract` section
- `## Documentation Standard — Context7 First, Repository Fallback` section

**Skill contract** — the three main skills (`discovery`, `implement`, `squad`) must have:
- `### Preflight Gate`
- `## Agent Result Contract (ARC)`
- `## Runtime Resilience Contract`
- `### Checkpoint / Resume Rules`

**No self-chaining** — only `incident-manager.md` may expose the `Agent` tool or reference `subagent_type`. Any other agent file with those will fail validation.

**Namespace enforcement** — all `subagent_type` values in skills must use the `claude-tech-squad:` prefix.

**Runtime policy keys** — `runtime-policy.yaml` must contain: `version:`, `retry_budgets:`, `severity_policy:`, `fallback_matrix:`, `checkpoint_resume:`, `reliability_metrics:`.

---

## Architecture

```
.
├── .claude-plugin/marketplace.json          # marketplace registration
├── plugins/claude-tech-squad/
│   ├── .claude-plugin/plugin.json           # plugin metadata and version
│   ├── runtime-policy.yaml                  # retry budgets, fallback matrix, severity, checkpoints
│   ├── agents/                              # 61 specialist agent files (one .md per agent)
│   └── skills/                              # 20 skill directories (each with SKILL.md)
│       └── <skill-name>/SKILL.md
├── fixtures/dogfooding/
│   ├── scenarios.json                       # dogfood scenario manifest (must have exactly 3)
│   ├── layered-monolith/                    # simulates a layered repo for discovery
│   ├── hexagonal-billing/                   # simulates a hexagonal repo for discovery
│   └── hotfix-checkout/                     # simulates a broken prod for hotfix
├── ai-docs/
│   ├── .squad-log/                          # SEP logs from real runs (gitignored, .gitkeep tracked)
│   └── dogfood-runs/                        # captured golden runs (gitignored, .gitkeep tracked)
├── templates/                               # RFC, service readiness review, golden run scorecard
├── scripts/                                 # validate, smoke-test, dogfood, release scripts
└── docs/                                    # operator and contributor documentation
```

### How skills orchestrate agents

A skill (`skills/<name>/SKILL.md`) defines a pipeline: preflight → agent chain → gates → checkpoints → SEP log. It calls agents using the `Agent` tool with `subagent_type: "claude-tech-squad:<agent-slug>"`. The `runtime-policy.yaml` supplies retry limits, fallback agents, and checkpoint names — skills do not hardcode these values.

### How the runtime policy is loaded

Every skill reads `runtime-policy.yaml` at preflight. The policy provides:
- `failure_handling` — max retries (2) and fallback attempts (1) before a user gate
- `retry_budgets` — cycle caps per phase (review: 3, QA: 2, conformance: 2, UAT: 2)
- `fallback_matrix` — which agent to invoke when the primary fails
- `severity_policy` — what is BLOCKING (stops pipeline) vs WARNING (logged, continues) vs INFO
- `checkpoint_resume` — which checkpoints each skill defines and the resume rule

### SEP log

Every skill writes a Squad Execution Protocol log to `ai-docs/.squad-log/<skill>-<timestamp>.json` before ending. This file is the data source for `/factory-retrospective`. Real run artifacts are gitignored; only `.gitkeep` files are tracked.

---

## Change classes

Every PR must declare its change class in the PR template. The class determines the required validation:

| Class | What changed | Required validation |
|---|---|---|
| A | Prompt or doc only | `validate.sh` + `smoke-test.sh` |
| B | Workflow contract (retry, fallback, checkpoint, gate) | + `dogfood.sh` + updated golden run scorecards |
| C | New agents, routing changes, quality bench changes | + all Class B + at least one real golden run per affected scenario |
| D | Release workflow, incident, security/privacy gates | + all Class C + real golden runs + operator doc update |

---

## Files that must NOT be edited manually

The release pipeline generates these automatically on merge to `main`. Editing them by hand causes version drift that will fail `validate.sh`:

- `CHANGELOG.md`
- `.claude-plugin/marketplace.json`
- `plugins/claude-tech-squad/.claude-plugin/plugin.json`
- `docs/MANUAL.md`

All other files — agents, skills, scripts, docs, fixtures, templates — are edited normally.

---

## Adding a new agent

1. Create `plugins/claude-tech-squad/agents/<slug>.md` with required frontmatter (`name:`, `description:`).
2. Include `## Result Contract`, `## Documentation Standard — Context7 First, Repository Fallback`, and (for execution agents) `## Absolute Prohibitions`.
3. Add the agent slug to the `REQUIRED_AGENTS` array in `scripts/validate.sh`.
4. Register it in the roster in `README.md`.
5. Run `bash scripts/validate.sh` to confirm the contract is satisfied.

See `docs/AGENT-CONTRACT.md` for the full required structure.

## Adding a new skill

1. Create `plugins/claude-tech-squad/skills/<slug>/SKILL.md` with required frontmatter.
2. Include the Global Safety Contract, Operator Visibility Contract, preflight block, agent chain, gate definitions, checkpoint block, and SEP log instruction.
3. For orchestrator skills (similar to `discovery`, `implement`, `squad`), also add `### Preflight Gate`, `## Agent Result Contract (ARC)`, `## Runtime Resilience Contract`, `### Checkpoint / Resume Rules`.
4. Add the skill slug to `REQUIRED_SKILLS` in `scripts/validate.sh` if it should be required.
5. Add an asserção in `scripts/smoke-test.sh` for the new skill.
6. Run `bash scripts/smoke-test.sh` to confirm.

See `docs/SKILL-CONTRACT.md` for the full required structure.
