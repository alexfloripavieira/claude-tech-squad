# claude-tech-squad

A generic Claude Code plugin for end-to-end software delivery with a full specialist squad.

## Commands

- `/claude-tech-squad:discovery` - Product definition, business analysis, prioritization, feasibility, architecture, specialist design notes, and quality baselines
- `/claude-tech-squad:implement` - Multi-track implementation, review, automated and integration testing, specialist quality reviews, docs, and Jira/Confluence updates
- `/claude-tech-squad:squad` - Full flow from discovery through release, reliability, and delivery artifact preparation

## Squad Roster

### Product & Delivery

- PM
- PO
- Business Analyst
- Planner
- Tech Lead

### Design & Architecture

- Architect
- Backend Architect
- Frontend Architect
- Data Architect
- UX Designer
- API Designer
- AI Engineer

### Implementation

- Backend Dev
- Frontend Dev
- Platform Dev
- Integration Engineer
- DevOps
- CI/CD
- DBA

### Quality & Risk

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

### Operations & Knowledge

- Observability Engineer
- Analytics Engineer
- Docs Writer
- Jira & Confluence Specialist
- SRE
- Release

## Principles

- Documentation-first: validate stack decisions against current docs via context7
- Project-aware: inspect repo conventions before proposing patterns
- Interactive where it matters: ask the user to resolve product, business, and design tradeoffs
- Specialist bench: only invoke the specialists the task actually needs
- Multi-track delivery: split backend, frontend, data, AI, integration, and platform work when needed
- Quality gates: no feature is done until tests, review, security, privacy, docs, and release impacts are addressed

## Install

```bash
/plugin marketplace add alexfloripavieira/claude-tech-squad
/plugin install claude-tech-squad@alexfloripavieira-plugins
```

## Usage

```bash
/claude-tech-squad:discovery build an internal admin dashboard for subscription management
/claude-tech-squad:implement

/claude-tech-squad:squad add SSO login with audit trail and admin controls
```
