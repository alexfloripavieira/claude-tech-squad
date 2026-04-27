# claude-tech-squad

Generic Claude Code plugin for end-to-end software delivery with a complete specialist squad.

## Use This Plugin When

- the task crosses product, engineering, QA, docs, and release boundaries
- you want one orchestrated workflow rather than hand-assembling agents
- you need specialists selected according to the actual repository and feature
- you want TDD cycle planning separated cleanly from QA acceptance validation
- you want explicit structural guidance for SOLID, Clean Architecture, Ports and Adapters, and Hexagonal-style boundaries
- you want `/squad` to run code delivery in TDD-first mode by default

## Do Not Use This Plugin For

- machine bootstrap or global defaults
- storing reusable templates and generic rules
- product-specific artifacts outside the repository being worked on

For those, use `claude-config`.
For install scopes and prompt examples, see [GETTING-STARTED.md](../../docs/GETTING-STARTED.md).
For visible execution interpretation, see [EXECUTION-TRACE.md](../../docs/EXECUTION-TRACE.md).

## Commands

- `/claude-tech-squad:discovery`
- `/claude-tech-squad:implement`
- `/claude-tech-squad:squad`
- `/claude-tech-squad:hotfix`
- `/claude-tech-squad:bug-fix`
- `/claude-tech-squad:pr-review`
- `/claude-tech-squad:refactor`
- `/claude-tech-squad:security-audit`
- `/claude-tech-squad:llm-eval`
- `/claude-tech-squad:prompt-review`
- `/claude-tech-squad:release`
- `/claude-tech-squad:migration-plan`
- `/claude-tech-squad:dependency-check`
- `/claude-tech-squad:cloud-debug`
- `/claude-tech-squad:iac-review`
- `/claude-tech-squad:multi-service`
- `/claude-tech-squad:onboarding`
- `/claude-tech-squad:incident-postmortem`
- `/claude-tech-squad:pre-commit-lint`
- `/claude-tech-squad:factory-retrospective`
- `/claude-tech-squad:cost-estimate`
- `/claude-tech-squad:from-ticket`
- `/claude-tech-squad:dashboard`
- `/claude-tech-squad:rollover`
- `/claude-tech-squad:resume-from-rollover`

### Agent profile management (since v5.63.0)

- `/claude-tech-squad:setup` — detect repo stack and pick a curated profile
- `/claude-tech-squad:profiles` — list available profiles with agent counts
- `/claude-tech-squad:list-agents` — show active vs. disabled agents
- `/claude-tech-squad:enable <agent>` — re-enable a single agent on top of profile
- `/claude-tech-squad:disable <agent>` — silence a single agent for this repo
- `/claude-tech-squad:reset` — restore the default 'full' profile (all 81 agents active)

## Profile-based agent selection

The plugin ships 81 specialist agents covering many stacks (Django, React, Vue, mobile, data, AI/RAG, etc.). Loading all of them into every project's system prompt costs roughly 17k tokens.

**With profiles**, each project picks only the agents that match its stack:

| Profile | Agents | Description |
|---|---|---|
| `django-react-ai` | ~38 | Django + React with LLM/RAG (e.g. A1) |
| `django-react` | ~32 | Plain Django + React SaaS |
| `vue-typescript` | ~28 | Vue 3 + TS frontend with API backend |
| `react-typescript` | ~28 | React + TS frontend with API backend |
| `python-backend` | ~28 | FastAPI/Flask Python services |
| `mobile-fullstack` | ~28 | React Native or Flutter + backend |
| `data-platform` | ~26 | dbt/Airflow/Spark data engineering |
| `minimal` | 14 | Discovery + implementation + review only |
| `full` | 81 | All agents (default — backward-compatible) |

**Per-repo config** lives at `.claude-tech-squad.yml` in the project root and is committed to git so the whole team uses the same agent set:

```yaml
profile: django-react-ai
overrides:
  enable:
    - llm-safety-reviewer    # added on top of profile
  disable:
    - jira-confluence-specialist
```

**How it works:**
1. Run `/claude-tech-squad:setup` once per repo. It detects your stack (Django, React, etc.) and proposes a profile.
2. Confirm — the plugin writes `.claude-tech-squad.yml` and physically moves non-profile agents to `agents/.disabled/` inside the plugin cache.
3. The `SessionStart` hook reapplies the profile every time Claude Code starts, so plugin auto-updates won't undo your config.
4. Backward-compatible: if `.claude-tech-squad.yml` is absent, all 81 agents stay active (same as before).

## squad-cli — Embedded Orchestrator

The plugin includes `squad-cli`, a Python tool that handles deterministic orchestration logic outside the LLM. This reduces token overhead by 80-85% on mechanical tasks like stack detection, health checks, cost tracking, and SEP log generation.

**No installation required** — squad-cli ships inside the plugin at `bin/squad-cli`. It auto-installs its two dependencies (PyYAML, Click) on first run if missing. Requires Python 3.10+.

### What squad-cli does

| Command | What it replaces | Tokens saved |
|---|---|---|
| `preflight` | LLM reading YAML, grepping for AI imports, parsing package.json, resolving routing tables | ~5K/run |
| `health` | LLM evaluating 6 health check signals after each teammate | ~2K/teammate |
| `doom-check` | LLM comparing diffs to detect retry loops | ~2K/retry |
| `checkpoint` | LLM reading/writing state from Markdown files | ~3K/resume |
| `cost` | LLM estimating token counts and costs | ~2K/run |
| `sep-log` | LLM generating 60+ line YAML frontmatter SEP logs | ~5K/run |
| `dry-run` | Not possible before — shows execution plan without spending tokens | N/A |
| `onboarding-plan` | LLM selecting onboarding profile and CLAUDE.md template | ~3K/repo |
| `dashboard` | LLM aggregating SEP logs into health reports | ~5K/report |
| `ticket-plan` | LLM normalizing tickets and selecting skill routes | ~4K/ticket |
| `sdk-smoke` | Manual SDK verification | N/A |

`ticket-plan` supports Jira, Linear, GitHub Issue, JQL/pasted text, captured JSON, batch JSON, and optional planning SEP logs:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan PROJ-123
python3 plugins/claude-tech-squad/bin/squad-cli ticket-plan --ticket-json tickets.json --write-sep-log
```

The Python SDK exposes the same deterministic contracts for scripts and future UI/API layers. It does not launch agents or call external ticket APIs by itself.

### Supported stacks

squad-cli detects the project stack automatically and routes to the correct specialist agents:

Django, React, Vue, TypeScript, JavaScript, Python, Go, Rust, Java, Ruby, PHP, .NET, Elixir

Detection works in monorepos — scans up to 3 levels of subdirectories for signal files.

### Fallback

Every skill retains full manual fallback instructions. If Python3 is unavailable or squad-cli fails, the LLM executes the same logic from prompt instructions (at higher token cost).

## Principles

- repository-aware first
- specialist bench, not specialist noise
- validate decisions against current docs and real stack evidence
- use TDD cycle planning when the delivery strategy benefits from red-green-refactor execution
- apply design principles pragmatically, not dogmatically
- finish through review, docs, and release impact, not just implementation

## Visible Execution

The plugin workflows emit explicit progress lines for phase changes, agent handoffs, retries, and batch execution.

Expect output such as:

- `[Phase Start] Build`
- `[Teammate Spawned] Backend Dev | pane: backend-dev`
- `[Health Check] reviewer | signals: ok`
- `[Teammate Done] Backend Dev | Status: completed | Output: endpoints and tests updated`

Final outputs also include an `Agent Execution Log`.

Use [EXECUTION-TRACE.md](../../docs/EXECUTION-TRACE.md) to interpret these lines during real runs.
