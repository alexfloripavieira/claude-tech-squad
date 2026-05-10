# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What this repository is

This is the source repository for the `claude-tech-squad` Claude Code plugin — a full software delivery squad of 81 specialist agents and 29 skills that replicate big tech engineering pipelines. The repository ships a marketplace manifest, the plugin itself, a validation ladder, a dogfooding pack with golden run support, and a live pipeline dashboard.

Built on **Harness Engineering** principles — the infrastructure, constraints, and feedback loops that make AI agents reliable in production. The plugin scores 10/10 across all 5 pillars (Tool Orchestration, Guardrails, Error Recovery, Observability, Human-in-the-Loop) and all 5 practical concepts (Rule Files, Progressive Disclosure, Mechanical Enforcers, Reasoning Sandwich, Entropy Management).

There is no application server, no database, and no build step. The artifacts are Markdown files (agents, skills), a YAML policy file, JSON manifests, and a self-contained HTML dashboard.

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
- `name:`, `description:`, and `tool_allowlist:` frontmatter
- `## Result Contract` section
- `## Self-Verification Protocol` with role-specific checks
- `verification_checklist:` block (mechanically validated by orchestrator)
- `## Pre-Execution Plan` (execution agents) or `## Analysis Plan` (analysis agents)
- `## Documentation Standard — Context7 First, Repository Fallback` section

**Skill contract** — the three main skills (`discovery`, `implement`, `squad`) must have:
- `### Preflight Gate`
- `## Agent Result Contract (ARC)` — requires both `result_contract` and `verification_checklist`
- `## Runtime Resilience Contract`
- `### Checkpoint / Resume Rules`
- `## Progressive Disclosure — Context Digest Protocol`
- `## Visual Reporting Contract` (teammate cards + pipeline board rendered from Result Contract metrics)

**No self-chaining** — only `incident-manager.md` may expose the `Agent` tool or reference `subagent_type`. Any other agent file with those will fail validation.

**Namespace enforcement** — all `subagent_type` values in skills must use the `claude-tech-squad:` prefix.

**Runtime policy keys** — `runtime-policy.yaml` must contain: `version:`, `retry_budgets:`, `severity_policy:`, `fallback_matrix:`, `checkpoint_resume:`, `reliability_metrics:`, `cost_guardrails:`, `doom_loop_detection:`, `auto_advance:`, `entropy_management:`, `agent_teams:`, `tool_allowlists:`, `observability:`.

**Hierarchical worktree flow (hard requirement)** — controlled by `runtime-policy.yaml::agent_worktrees` and four helpers under `plugins/claude-tech-squad/bin/`:

1. **Skill init** — orchestrator runs `init-skill-branch.sh <skill>`, which (in the project's MAIN worktree) verifies the working tree is clean, then `git checkout -b cts/skill/<skill>-<epoch>`. The orchestrator owns the main worktree on this skill branch for the entire run; it does not get a separate worktree of its own. Output: `skill_branch=... base_branch=... base_commit=...`. Operator emits `[Skill Branch Created]`.
2. **Per-agent spawn** — for every `Agent(...)`, orchestrator runs `spawn-agent-worktree.sh <skill> <agent> [id]` to create an isolated worktree under `${CTS_WORKTREE_BASE:-${TMPDIR:-/tmp}/cts-worktrees}` on branch `cts/<skill>/<agent>-<epoch>-<id>`, derived from the orchestrator's HEAD (i.e. the skill branch). The fields `skill_branch`, `worktree_path`, `branch`, `base_commit` are injected into the spawn prompt via `agent_worktrees.spawn_prompt_inject`. The agent does all Read/Edit/Write/Bash inside its worktree and commits there if it wants the work preserved. Operator emits `[Worktree Spawned]`.
3. **Per-agent cleanup** — when an agent returns its `result_contract` (or on teammate-failure / skill-abort), orchestrator runs `cleanup-agent-worktree.sh <path>`. The helper:
   - Computes `commits_ahead` against the skill branch.
   - If > 0: merges the agent branch into the skill branch in the main worktree using `--no-ff` (commit message `merge: agent worktree <agent_branch> into <skill_branch>`).
   - Removes the per-agent worktree (`git worktree remove --force`).
   - Deletes the agent branch unconditionally on successful merge (its commits now live on the skill branch).
   - On merge conflict: leaves the merge in progress, exits 4, emits `[Worktree Cleanup Conflict]`, and the orchestrator opens `[Gate] Worktree Merge Conflict | [R]esolve / [A]bort`. Agent worktree and branch are preserved until the user resolves.
4. **Skill finalize** — `finalize-skill.sh <skill_branch> [base_branch]` asserts the invariant: zero per-agent worktrees survive, zero `cts/<skill>/...` branches survive (only `cts/skill/<skill>-<epoch>` remains), main worktree is clean, and the orchestrator is still on the skill branch. Non-zero exit if any check fails. Emits `[Skill Finalized]`. The helper does NOT push, merge to main, or delete the skill branch — that decision belongs to the user.

**Cross-talk file handoff** — pairs that need to share a file (e.g. `tdd-specialist` ↔ `dev` exchanging the failing test) send `from_branch + commit_sha + file_paths` via `SendMessage`. Receiver fetches with `git fetch . <branch>:<branch> 2>/dev/null || true; git checkout <branch> -- <paths>` inside its own worktree. The sender's branch is always reachable locally because all agent branches live in the same repo.

**SEP log audit** — `worktrees[]` per agent (`agent_branch`, `path`, `commits_ahead`, `merged`, `final_status: merged_and_deleted | deleted_no_commits | preserved_unresolved`) plus a top-level `skill_branch` field.

**Language policy (pt-BR — hard requirement)** — `runtime-policy.yaml::language_policy.default_locale: pt-BR`. All natural-language communication from teammates and from the orchestrator to the user MUST be in Portuguese (pt-BR): SendMessage bodies, `result_contract` narrative fields (`blockers`, `next_action`, evidence narratives), gate prompts, lead-to-user reports, and SEP log narrative sections. **Stays in English:** code, commit messages, PR titles/bodies, file paths, identifier names, structured YAML keys, log tag grammar (`[Preflight Start]` etc.), and shell commands. The orchestrator injects `language_policy.spawn_prompt_preamble` as the first block of every `Agent(...)` spawn prompt and follows `language_policy.lead_to_user_preamble` for its own user-facing output. Every SEP log records `language_policy_applied: pt-BR`.

**Inter-Teammate Cross-Talk Protocol** — every skill listed in `agent_teams.cross_talk_protocol.required_for_skills` must declare `## Inter-Teammate Cross-Talk Protocol` in its SKILL.md, enumerate `Required pairs`, reference `SendMessage`, and define `cross-talk-missing` as a Teammate Failure reason. Teammates communicate **directly with each other**, not only through the lead.

**Mode resolution at preflight** — `bin/detect-team-mode.sh` runs before TeamCreate and prints `mode=<teammate|inline> tmux=<0|1> inside_tmux=<0|1> flag=<0|1> version=<x.y.z>`.
- **teammate mode** (preferred) — fires when tmux binary present, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, Claude Code ≥ 2.1.32. If `inside_tmux=0`, the orchestrator auto-launches a detached session `cts-<skill>-<epoch>` and re-attaches the lead before TeamCreate, making tmux UX independent of the host terminal (plain bash, VS Code terminal, Windows Terminal, Ghostty, etc.).
- **inline mode** (fallback) — fires when any prerequisite is missing. Lead spawns inline `Agent(subagent_type=...)` in the main session. Cross-talk gate is **downgraded to warning-only** (`enforcement_by_mode.inline: warning`); pipeline continues.

Operator visibility: every skill emits `[Team Mode Resolved] mode=<...> | tmux=<...> | inside_tmux=<...> | flag=<...> | version=<...>` and, on auto-launch, `[Tmux Auto-Launch] session=<...> | host_terminal=<...>`.

**Harness Engineering enforcement** — validate.sh runs 39 checks including:
- Self-Verification Protocol in all 81 agents
- `verification_checklist` in all 81 agents
- Role-specific checks in all 81 agents
- Pre-Execution Plan / Analysis Plan in all 81 agents
- Progressive Disclosure in orchestrator skills
- `hooks/pre-tool-guard.sh` exists and is executable
- Token tracking (`tokens_input:`) in all 29 skill SEP log templates

---

## Architecture

```
.
├── .claude-plugin/marketplace.json          # marketplace registration
├── plugins/claude-tech-squad/
│   ├── .claude-plugin/plugin.json           # plugin metadata and version
│   ├── runtime-policy.yaml                  # retry, fallback, severity, checkpoints, cost, doom loop, auto-advance, entropy, tool allowlists, observability
│   ├── agents/                              # 81 specialist agent files (one .md per agent)
│   ├── skills/                              # 29 skill directories (each with SKILL.md)
│   │   └── <skill-name>/SKILL.md
│   ├── hooks/                               # runtime PreToolUse mechanical enforcers
│   │   ├── pre-tool-guard.sh                # blocks destructive operations deterministically
│   │   ├── settings-template.json           # copy to .claude/settings.json to activate hooks
│   │   └── README.md
│   └── scripts/                             # render-teammate-card.sh, render-pipeline-board.sh
├── fixtures/dogfooding/
│   ├── scenarios.json                       # dogfood scenario manifest (must have exactly 4)
│   ├── layered-monolith/                    # simulates a layered repo for discovery
│   ├── hexagonal-billing/                   # simulates a hexagonal repo for discovery
│   ├── hotfix-checkout/                     # simulates a broken prod for hotfix
│   └── llm-rag/                             # simulates a RAG pipeline for AI bench
├── ai-docs/
│   ├── .squad-log/                          # SEP logs from real runs (gitignored, .gitkeep tracked)
│   └── dogfood-runs/                        # captured golden runs (gitignored, .gitkeep tracked)
├── templates/                               # RFC, service readiness review, golden run scorecard
├── scripts/                                 # validate, smoke-test, dogfood, release, build-release-bundle
└── docs/                                    # operator and contributor documentation
```

### How skills orchestrate agents

A skill (`skills/<name>/SKILL.md`) defines a pipeline: preflight → agent chain → gates → checkpoints → SEP log. It calls agents using the `Agent` tool with `subagent_type: "claude-tech-squad:<agent-slug>"`. The `runtime-policy.yaml` supplies retry limits, fallback agents, and checkpoint names — skills do not hardcode these values.

### How the runtime policy is loaded

Every skill reads `runtime-policy.yaml` at preflight. The policy provides:
- `failure_handling` — max retries (2) and fallback attempts (1) before a user gate
- `retry_budgets` — cycle caps per phase (review: 3, QA: 2, conformance: 2, UAT: 2)
- `fallback_matrix` — which agent to invoke when the primary fails (complete coverage: all agents including LLM/AI specialists)
- `severity_policy` — what is BLOCKING (stops pipeline) vs WARNING (logged, continues) vs INFO
- `checkpoint_resume` — which checkpoints each skill defines and the resume rule
- `cost_guardrails` — token budget per skill with circuit breaker (warn at 75%, halt at 100%)
- `doom_loop_detection` — 3 divergence patterns that short-circuit futile retries
- `auto_advance` — gates that can be skipped when all agents return high confidence + zero BLOCKING
- `entropy_management` — auto-trigger `/factory-retrospective` after every 5 runs + orphan detection at preflight
- `tool_allowlists` — per-category tool access (analysis, implementation, documentation, operations, orchestrator)
- `observability.live_dashboard` — schema for the live status JSON file
- `observability.sep_log_schema` — required and teammate fields for SEP logs

### SEP log

Every skill writes a Squad Execution Protocol log to `ai-docs/.squad-log/<skill>-<timestamp>.md` before ending, including `tokens_input`, `tokens_output`, `estimated_cost_usd`, and `total_duration_ms`. This file is the data source for `/factory-retrospective` and `/dashboard`. Real run artifacts are gitignored; only `.gitkeep` files are tracked.

### Dashboard

The `/dashboard` skill aggregates SEP logs from `ai-docs/.squad-log/` into Markdown and HTML snapshots (`ai-docs/dashboard-snapshot.md` and `ai-docs/dashboard.html`). Run via `python3 plugins/claude-tech-squad/bin/squad-cli dashboard` or invoke the skill. There is no live-polling dashboard — observability is post-run via SEP logs and Visual Reporting Contract cards.

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

## Inline execution policy (when skills may run without teammates)

Not every skill invocation requires a full TeamCreate + Agent spawn cycle. The rule:

| Skill | Inline allowed? | Rationale |
|---|---|---|
| `/claude-tech-squad:bug-fix` | **Yes, when scope is 1–2 files** | Cost-optimized for small, well-scoped defects. The skill still writes a SEP log and runs tests. |
| `/claude-tech-squad:hotfix` | **Yes** | Emergency path — speed matters, skill still enforces its own gates. |
| `/claude-tech-squad:mini-squad` | **Mode-aware** | 3 teammates (tdd + dev + reviewer). Auto-uses tmux teammate mode when available, inline fallback when not. Scope guard blocks auth/billing/schema/new-public-endpoint changes — those force escalation to `/implement` or `/squad`. ~20% of `/squad` token cost. |
| `/claude-tech-squad:implement` | **No — MUST spawn teammates** | Progressive disclosure, reviewer/QA/conformance/UAT gates depend on separate teammate contexts. |
| `/claude-tech-squad:squad` | **No — MUST spawn teammates** | Full pipeline; multi-lens review is the entire value. |
| `/claude-tech-squad:discovery` | **No — MUST spawn teammates** | Specialist bench is the point. |
| `/claude-tech-squad:refactor` | **No — MUST spawn teammates** | Characterization tests + reviewer gate. |
| `/claude-tech-squad:security-audit` | Inline | Runs scanners + one reviewer agent; no multi-gate pipeline. |
| `/claude-tech-squad:tech-debt-audit` | **No — MUST spawn teammates** | 5 specialist lenses run in parallel before tech-debt-analyst synthesizes. |
| `/claude-tech-squad:pentest-deep` | **No — MUST spawn teammates** | 4–5 specialist lenses run in parallel before ethical-hacker synthesizes the 16-dimension report. |
| `/claude-tech-squad:factory-retrospective` | Inline | Reads logs, no parallel specialist work. |

When in doubt: if the skill SKILL.md contains `TeamCreate` + multiple `Agent(...)` spawns in its execution block, it MUST use teammates. Inline bypass is forbidden except for the explicit whitelist above. Added 2026-04-18 after the retrospective documented silent inline bypass in `/implement` runs.

## .retro-counter file

`ai-docs/.squad-log/.retro-counter` is a plain-text file holding a single integer — runs-since-last-retrospective. Incremented by SEP-log-writing skills. Read by `runtime-policy.yaml` (`entropy_management.factory_retrospective_auto_trigger`) to auto-suggest `/factory-retrospective` after threshold (default 5). Reset to `0` in Step 9a of `/factory-retrospective`. Gitignored; only `.gitkeep` tracked. If missing or corrupt, treat as `0`.

## squad-cli (Python component)

`squad-cli/` is a standalone Python package that embeds the orchestrator runtime as a CLI tool. Its modules mirror the SKILL.md pipeline phases:

| Module | Role |
|---|---|
| `cli.py` | Entrypoint and command dispatch |
| `preflight.py` | Validates runtime-policy.yaml and fixture state before execution |
| `policy.py` | Loads and surfaces `runtime-policy.yaml` keys |
| `models.py` | Shared data structures (SEP log record, checkpoint state) |
| `sep_log.py` | Writes the SEP log artifact |
| `checkpoint.py` | Checkpoint read/write/resume logic |
| `cost.py` | Token budget tracking and circuit breaker |
| `doom_loop.py` | Doom-loop divergence detection |
| `health.py` | Preflight fixture health checks |
| `stack_detect.py` | Tech-stack fingerprinting for fixture scenarios |
| `dry_run.py` | `--dry-run` execution path |
| `task_memory.py` | Persistent task memory across skill invocations |

The package uses a virtualenv at `squad-cli/venv/`. There is no `setup.py` or `pyproject.toml` exposed at repo root — the egg-info lives at `squad-cli/squad_cli.egg-info/`.

---

## Commit convention and release automation

Commits must follow Conventional Commits — the release pipeline derives the next semver bump from commit subjects since the last tag:

| Prefix | Version bump |
|---|---|
| `feat:` | minor |
| `fix:`, `docs:`, `refactor:`, `chore:` | patch |
| `type!:` or `BREAKING CHANGE` in body | major |

After merge to `main`, GitHub Actions (`publish` workflow) auto-generates `CHANGELOG.md`, bumps the three version files, builds the release bundle, tags the commit, and creates the GitHub Release. No manual step is needed.

If the workflow did not fire, run `./scripts/release.sh` as a fallback. For a full emergency manual release path, see `docs/HOW-TO-CHANGE-AND-PUBLISH.md`.

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

1. Create `plugins/claude-tech-squad/agents/<slug>.md` with required frontmatter (`name:`, `description:`, `tool_allowlist:`).
2. Include `## Result Contract`, `## Self-Verification Protocol` (with role-specific checks), `verification_checklist:` block, `## Documentation Standard — Context7 First, Repository Fallback`.
3. Include `## Pre-Execution Plan` (for execution agents) or `## Analysis Plan` (for analysis agents).
4. Include (for execution agents) `## Absolute Prohibitions`.
5. Add the agent slug to the `REQUIRED_AGENTS` array in `scripts/validate.sh`.
6. Register it in the roster in `README.md`.
7. Run `bash scripts/validate.sh` to confirm all contracts are satisfied.

See `docs/AGENT-CONTRACT.md` for the full required structure including the Reasoning Sandwich protocol.

## Adding a new skill

1. Create `plugins/claude-tech-squad/skills/<slug>/SKILL.md` with required frontmatter.
2. Include the Global Safety Contract, Operator Visibility Contract, preflight block, agent chain, gate definitions, checkpoint block, and SEP log instruction.
3. For orchestrator skills (similar to `discovery`, `implement`, `squad`), also add `### Preflight Gate`, `## Agent Result Contract (ARC)`, `## Runtime Resilience Contract`, `### Checkpoint / Resume Rules`.
4. Add the skill slug to `REQUIRED_SKILLS` in `scripts/validate.sh` if it should be required.
5. Add an assertion in `scripts/smoke-test.sh` for the new skill.
6. Run `bash scripts/smoke-test.sh` to confirm.

See `docs/SKILL-CONTRACT.md` for the full required structure.
