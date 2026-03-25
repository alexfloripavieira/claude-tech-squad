# claude-tech-squad

Installable Claude Code plugin for a complete software delivery squad.

![claude-tech-squad demo](docs/assets/demo.gif)

This repository is the execution layer. It provides the specialist team and workflows that run inside a real repository.

## Use This Repository For

- discovery, scope shaping, and release slicing
- architecture, TDD-first implementation planning, and execution coordination
- coordinated delivery across backend, frontend, data, platform, QA, security, docs, and release
- LLM/AI features: evals as CI gate, prompt review, RAG quality, prompt injection security
- Jira and Confluence handoff support

## Use `claude-config` For

- machine-level and user-level baseline setup
- reusable global commands, skills, rules, and templates
- portable defaults shared across repositories

Short version:

- `claude-config` installs the environment
- `claude-tech-squad` runs the squad

See [USAGE-BOUNDARIES.md](docs/USAGE-BOUNDARIES.md).
See [GETTING-STARTED.md](docs/GETTING-STARTED.md) for installation, teammate mode setup, commands, and prompt examples.
See [EXECUTION-TRACE.md](docs/EXECUTION-TRACE.md) for how to interpret visible agent execution.
See [OPERATIONAL-PLAYBOOK.md](docs/OPERATIONAL-PLAYBOOK.md) for common execution scenarios.

## What This Repository Contains

- one Claude Code marketplace manifest
- one installable plugin: `claude-tech-squad`
- 60 specialist agents for software delivery
- 20 skills covering discovery, implementation, LLM evals, security, distributed systems, and more

## Commands

```bash
# Core delivery
/claude-tech-squad:discovery   # shape the problem and produce a blueprint
/claude-tech-squad:implement   # build from an approved blueprint
/claude-tech-squad:squad       # end-to-end: discovery + implementation + release

# Emergency & incidents
/claude-tech-squad:hotfix              # emergency production fix
/claude-tech-squad:incident-postmortem # blameless post-mortem

# Quality & security
/claude-tech-squad:pr-review      # full specialist bench review on any PR
/claude-tech-squad:security-audit # static analysis + secrets scan + CVE check
/claude-tech-squad:refactor       # test-guarded incremental refactoring

# LLM / AI specific
/claude-tech-squad:llm-eval      # run eval suite as CI gate — detect regressions before deploy
/claude-tech-squad:prompt-review # review prompt changes: regression, injection, token cost

# Release & planning
/claude-tech-squad:release          # cut a release with rollback plan and CI gate
/claude-tech-squad:migration-plan   # safe database migration planning with backup gate
/claude-tech-squad:dependency-check # CVEs, supply chain, outdated packages
/claude-tech-squad:cloud-debug      # investigate production incidents

# Distributed systems & infrastructure
/claude-tech-squad:multi-service # coordinate changes across multiple services with contract testing
/claude-tech-squad:iac-review    # review IaC changes before apply: blast radius, security, cost

# Project setup
/claude-tech-squad:onboarding         # bootstrap any new repo for squad usage
/claude-tech-squad:factory-retrospective # analyze executions and improve the process
```

## Teammate Mode (tmux panes)

By default, agents run inline as subagents. To make each specialist open in its own tmux pane, enable teammate mode.

**Requires:**
1. Starting Claude Code inside a tmux session
2. Two environment variables configured in `~/.claude/settings.json`

Configuration:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "CLAUDE_CODE_TEAMMATE_MODE": "tmux"
  }
}
```

Starting Claude Code inside tmux:

```bash
tmux new-session -s squad
claude
```

With teammate mode active, each `/discovery`, `/implement`, and `/squad` call creates a team and spawns every specialist in a separate pane. Without tmux mode, the same workflows run correctly as inline subagents.

## Visible Orchestration

The workflows expose squad execution in the Claude output.

You should see:

- `[Team Created] discovery` or `[Team Created] squad`
- `[Teammate Spawned] pm | pane: pm`
- `[Gate] Scope Validation | Waiting for user input`
- `[Batch Spawned] specialist-bench | Teammates: backend-arch, frontend-arch, api-designer`
- `[Teammate Done] reviewer | Status: APPROVED`
- `[AI Detected] LLM/AI features found — activating AI specialist bench`
- a final `Agent Execution Log` in the result

See [EXECUTION-TRACE.md](docs/EXECUTION-TRACE.md) for interpretation guidance.

## Install

```bash
claude plugin marketplace add alexfloripavieira/claude-tech-squad
claude plugin install -s user claude-tech-squad@alexfloripavieira-plugins
```

## Usage

```bash
/claude-tech-squad:discovery describe the feature or initiative
/claude-tech-squad:implement
/claude-tech-squad:squad describe the full delivery request

# For LLM/AI projects
/claude-tech-squad:llm-eval      # after any prompt or RAG pipeline change
/claude-tech-squad:prompt-review # before merging any prompt file change
```

## Specialist Roster (60 agents)

### Discovery & Planning
- PM
- Business Analyst
- PO
- Planner
- Architect
- Tech Lead

### Architecture Specialists
- Backend Architect
- Frontend Architect
- API Designer
- Data Architect
- UX Designer
- AI Engineer
- Agent Architect
- Integration Engineer
- DevOps
- CI/CD
- DBA
- Platform Dev
- Cloud Architect

### LLM / AI Specialists
- AI Engineer *(model pinning, context budget, output validation, agent loop safety)*
- Prompt Engineer *(design, token optimization, caching, versioning, injection defense)*
- RAG Engineer *(full pipeline + RAGAS quality gates + knowledge base poisoning prevention)*
- LLM Eval Specialist *(RAGAS, DeepEval, PromptFoo, hallucination detection, LLM-as-judge)*
- LLM Safety Reviewer *(prompt injection direct + indirect, jailbreak, tool call auth, PII leakage)*
- Agent Architect *(multi-agent orchestration, MCP, tool use design, loops with termination)*
- Conversational Designer
- ML Engineer

### Implementation
- Backend Dev
- Frontend Dev
- Mobile Dev
- Data Engineer
- TDD Specialist

### Search
- Search Engineer

### Quality & Review
- Reviewer
- QA
- Test Planner
- Test Automation Engineer
- Integration QA

### Specialist Reviewers
- Security Reviewer *(includes LLM threat surface checks)*
- Security Engineer
- Privacy Reviewer
- Compliance Reviewer
- Accessibility Reviewer
- Performance Engineer
- Chaos Engineer
- Design Principles Specialist
- Code Quality

### Observability & Monitoring
- Observability Engineer
- Monitoring Specialist
- Analytics Engineer

### Design
- Design System Engineer

### Documentation & Developer Experience
- Docs Writer
- Tech Writer
- DevEx Engineer
- Jira and Confluence Specialist
- Developer Relations

### Operations & Release
- Release
- SRE
- Cost Optimizer
- Incident Manager

### Business & Growth
- Solutions Architect
- Growth Engineer

Testing split:

- Test Planner defines the coverage contract
- TDD Specialist defines red-green-refactor delivery cycles
- QA validates acceptance criteria and regressions after cycles pass

Security split:

- Security Reviewer audits existing code for vulnerabilities (includes LLM-specific checks)
- Security Engineer implements security features (OAuth2, MFA, WAF, SAST/DAST)
- LLM Safety Reviewer covers AI-specific attack surface (prompt injection, jailbreak, tool abuse)

Documentation split:

- Docs Writer produces internal developer and operator documentation
- Tech Writer produces external user guides, public API references, and customer changelogs
- Developer Relations owns external developer community, SDKs, and technical content

## LLM / AI Project Workflow

When `/squad` detects LLM/AI code in the repository (OpenAI, Anthropic, LangChain, LlamaIndex, pgvector, etc.), it automatically activates the full AI specialist bench:

```
/squad "feature with AI"
    │
    ├─ [AI Detected] → activates AI specialist bench
    │
    PHASE 1 — Discovery
    ├─ + ai-engineer     (model design, context budget, eval strategy)
    ├─ + rag-engineer    (retrieval pipeline, if RAG detected)
    ├─ + prompt-engineer (prompt architecture, injection defense)
    ├─ + llm-eval-specialist (golden dataset, regression thresholds)
    └─ + llm-safety-reviewer (threat model: injection, jailbreak, tool auth)
    │
    PHASE 2 — Quality Bench
    ├─ + llm-safety-reviewer (injection surface + tool authorization review)
    └─ + llm-eval gate (runs evals before UAT — blocks if regression detected)
```

For LLM-specific workflows outside of full squad runs:

```bash
# After any prompt change
/claude-tech-squad:prompt-review

# Before any release touching AI features
/claude-tech-squad:llm-eval

# Security audit of LLM attack surface
/claude-tech-squad:security-audit  # includes llm-safety-reviewer
```

## Safety Guardrails

Every skill carries a **Global Safety Contract** (v5.8.0+). Every agent with execution authority carries an **Absolute Prohibitions** block. These are hard-coded constraints that cannot be overridden by incident urgency, deadlines, or business pressure.

Forbidden without explicit written user confirmation (across all agents):

- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` — any destructive SQL
- `tsuru app-remove`, `heroku apps:destroy`, or any cloud resource deletion in production
- Merging to `main`, `master`, or `develop` without an approved pull request
- `git push --force` to any protected branch
- `git commit --no-verify` — skipping pre-commit hooks
- Removing secrets or environment variables from production
- Deploying to production without staging verified first
- Creating a release tag when CI is failing
- Applying migrations without a confirmed backup
- Deploying to production without a documented and tested rollback plan
- Disabling authentication, authorization, monitoring, or SLO alerting
- Running chaos experiments in production without maintenance window, on-call, and abort procedure
- Publishing to App Store or Play Store production track without a staged rollout

Additional safety for LLM features:

- Prompt injection vulnerabilities are blocking — no merge until fixed
- Tool calls with destructive actions require an explicit human-in-the-loop gate
- PII must not be passed to LLMs or eval services without masking
- Model version must be pinned — never use floating model aliases in production
- Auto-updating prompts without eval regression testing is prohibited

## Validation and Release

- Validation workflow: [validate.yml](.github/workflows/validate.yml)
- Validation script: [validate.sh](scripts/validate.sh)
- Release process: [RELEASING.md](docs/RELEASING.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
