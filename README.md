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
See [GETTING-STARTED.md](docs/GETTING-STARTED.md) for installation scopes, Claude commands, and prompt examples.
See [EXECUTION-TRACE.md](docs/EXECUTION-TRACE.md) for how to interpret visible agent execution.
See [OPERATIONAL-PLAYBOOK.md](docs/OPERATIONAL-PLAYBOOK.md) for common execution scenarios such as features, audits, refactors, incidents, and release work.

## What This Repository Contains

- one Claude Code marketplace manifest
- one installable plugin: `claude-tech-squad`
- a complete specialist roster for software delivery

## Commands

- `/claude-tech-squad:discovery`
- `/claude-tech-squad:implement`
- `/claude-tech-squad:squad`

## Visible Orchestration

The workflows are designed to make squad execution visible in the Claude output.

You should see:

- phase transitions such as `[Phase Start] Discovery`
- explicit handoffs such as `[Agent Start] PM | claude-tech-squad:pm | ...`
- completion lines such as `[Agent Done] Reviewer | Status: completed | ...`
- batch execution lines for parallel specialist work
- a final `Agent Execution Log` in the result

This gives you proof of orchestration even if the Claude UI does not render each subagent call as a separate visual process.

If you want to know how to read these lines and what counts as healthy or blocked execution, see [EXECUTION-TRACE.md](docs/EXECUTION-TRACE.md).

## Specialist Roster

- PM
- PO
- Business Analyst
- Planner
- Tech Lead
- Architect
- Backend Architect
- Frontend Architect
- Data Architect
- UX Designer
- API Designer
- AI Engineer
- Backend Dev
- Frontend Dev
- Platform Dev
- Integration Engineer
- DevOps
- CI/CD
- DBA
- Design Principles Specialist
- Test Planner
- TDD Specialist
- Test Automation Engineer
- Integration QA
- QA
- Reviewer
- Security Reviewer
- Privacy Reviewer
- Compliance Reviewer
- Accessibility Reviewer
- Performance Engineer
- Observability Engineer
- Analytics Engineer
- Docs Writer
- Jira and Confluence Specialist
- SRE
- Release

Testing split:

- Test Planner defines the coverage contract
- TDD Specialist defines the red-green-refactor delivery cycles
- QA validates acceptance criteria, regressions, and behavior after the cycles pass

Default squad mode:

- when you use `/claude-tech-squad:squad` for code changes, the delivery model is TDD-first by default

Design split:

- Architect defines the overall system shape
- Tech Lead defines delivery sequencing and ownership
- Design Principles Specialist protects structural boundaries, dependency direction, and testability

## Install

```bash
/plugin marketplace add alexfloripavieira/claude-tech-squad
/plugin install claude-tech-squad@alexfloripavieira-plugins
```

## Usage

```bash
/claude-tech-squad:discovery describe the feature or initiative
/claude-tech-squad:implement
/claude-tech-squad:squad describe the full delivery request
```

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
