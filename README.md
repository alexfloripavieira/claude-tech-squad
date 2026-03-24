# claude-tech-squad

Installable Claude Code plugin for a complete software delivery squad.

This repository is the execution layer. It provides the specialist team and workflows that run inside a real repository.

## Use This Repository For

- discovery, scope shaping, and release slicing
- architecture, TDD-first implementation planning, and execution coordination
- coordinated delivery across backend, frontend, data, platform, QA, security, docs, and release
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
- 59 specialist agents for software delivery
- 10 skills covering discovery, implementation, security, data, and more

## Commands

```bash
/claude-tech-squad:discovery   # shape the problem and produce a blueprint
/claude-tech-squad:implement   # build from an approved blueprint
/claude-tech-squad:squad       # end-to-end: discovery + implementation + release
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
```

## Specialist Roster (59 agents)

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
- Prompt Engineer
- RAG Engineer
- LLM Eval Specialist
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
- Security Reviewer
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

- Security Reviewer audits existing code for vulnerabilities
- Security Engineer implements security features (OAuth2, MFA, WAF, SAST/DAST)

Documentation split:

- Docs Writer produces internal developer and operator documentation
- Tech Writer produces external user guides, public API references, and customer changelogs
- Developer Relations owns external developer community, SDKs, and technical content

## Install Modes

Global for your user:

```bash
claude plugin marketplace add alexfloripavieira/claude-tech-squad
claude plugin install -s user claude-tech-squad@alexfloripavieira-plugins
```

Only for the current project:

```bash
claude plugin install -s project claude-tech-squad@alexfloripavieira-plugins
```

## Validation and Release

- Validation workflow: [validate.yml](.github/workflows/validate.yml)
- Validation script: [validate.sh](scripts/validate.sh)
- Release process: [RELEASING.md](docs/RELEASING.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
