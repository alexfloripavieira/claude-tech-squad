# claude-tech-squad

Installable Claude Code plugin for a complete software delivery squad.

This repository is the execution layer. It provides the specialist team and workflows that run inside a real repository.

## Use This Repository For

- discovery, scope shaping, and release slicing
- architecture and implementation planning
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

## What This Repository Contains

- one Claude Code marketplace manifest
- one installable plugin: `claude-tech-squad`
- a complete specialist roster for software delivery

## Commands

- `/claude-tech-squad:discovery`
- `/claude-tech-squad:implement`
- `/claude-tech-squad:squad`

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
- Test Planner
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
