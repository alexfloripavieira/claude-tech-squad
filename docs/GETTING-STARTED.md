# Getting Started

This guide explains:

- what `claude-tech-squad` is for
- when to use it instead of `claude-config`
- how to install it globally or locally in Claude Code
- which commands to run
- example prompts for real delivery work
- how to interpret visible squad execution

## What `claude-tech-squad` Is

`claude-tech-squad` is the execution layer.

It is not a general config pack. It is the specialist team you run inside a real repository when you need coordinated product and engineering delivery.

Use it for:

- discovery and scope clarification
- architecture, TDD-first implementation planning, and implementation coordination
- multi-specialist delivery
- test, review, documentation, Jira/Confluence, and release follow-through

Testing split:

- Test Planner defines what must be covered
- TDD Specialist defines how development should proceed through failing tests and small cycles
- QA validates the implemented behavior against acceptance criteria and regressions

Design split:

- Architect defines the overall system shape
- Tech Lead decides sequencing and ownership
- Design Principles Specialist applies SOLID, Clean Architecture, Ports and Adapters, and Hexagonal-style guardrails pragmatically

If you need baseline commands, skills, rules, and templates, use `claude-config`.

## Install In Claude Code

### Add the Marketplace

Run once per machine or Claude environment:

```bash
claude plugin marketplace add alexfloripavieira/claude-tech-squad
```

Interactive equivalent inside Claude Code:

```text
/plugin marketplace add alexfloripavieira/claude-tech-squad
```

## Installation Scopes

### Global User Install

Use this when you want the squad available in any repository on your machine.

```bash
claude plugin install -s user claude-tech-squad@alexfloripavieira-plugins
```

Interactive equivalent:

```text
/plugin install --scope user claude-tech-squad@alexfloripavieira-plugins
```

### Project Install

Use this when you want the plugin associated with the current repository.

```bash
cd /path/to/your-project
claude plugin install -s project claude-tech-squad@alexfloripavieira-plugins
```

Interactive equivalent:

```text
/plugin install --scope project claude-tech-squad@alexfloripavieira-plugins
```

### Local Install

Use this for temporary or isolated local use in the current Claude context.

```bash
cd /path/to/your-project
claude plugin install -s local claude-tech-squad@alexfloripavieira-plugins
```

Interactive equivalent:

```text
/plugin install --scope local claude-tech-squad@alexfloripavieira-plugins
```

## Commands To Run

### `/claude-tech-squad:discovery`

Use when the problem or feature still needs shaping.

Example:

```text
/claude-tech-squad:discovery
Design a customer support workspace with ticket routing, audit history, and role-based administration.
```

### `/claude-tech-squad:implement`

Use after discovery when the blueprint is agreed and you want the squad to coordinate implementation.

Example:

```text
/claude-tech-squad:implement
Use the approved discovery package and implement the next delivery slice with TDD cycles where applicable.
```

### `/claude-tech-squad:squad`

Use when you want the full path from idea to release in one workflow.

For code changes, this command is TDD-first by default.

Example:

```text
/claude-tech-squad:squad
Add SSO login, audit events, admin controls, automated coverage, documentation, and release artifacts.
```

## What Visible Agent Execution Looks Like

The plugin is written to expose orchestration in the Claude output, not just in the internal workflow.

You should expect lines like:

```text
[Phase Start] Discovery
[Agent Start] PM | claude-tech-squad:pm | First-pass product analysis
[Agent Done] PM | Status: completed | Output: scope options and open questions
[Agent Batch Start] Specialist Design Bench | Agents: Backend Architect, Frontend Architect
```

And the final result should include an `Agent Execution Log` summarizing which agents ran, their status, and their outputs.

Depending on the Claude UI, you may or may not see each subagent rendered as an independent visual process. The progress lines above are the authoritative execution trace.

For a full interpretation guide, including healthy patterns, blocked patterns, and what to do when the trace looks wrong, see [EXECUTION-TRACE.md](EXECUTION-TRACE.md).
For scenario-based usage, see [OPERATIONAL-PLAYBOOK.md](OPERATIONAL-PLAYBOOK.md).

## Prompt Patterns That Work Well

Good inputs usually include:

- the business outcome
- the main user or operator
- the constraints
- any repo-specific context that matters

Examples:

```text
/claude-tech-squad:discovery
Create an internal billing admin surface for support operators. It needs invoice search, refunds, and access control. Keep rollout incremental.
```

```text
/claude-tech-squad:squad
Build a webhook reliability improvement package with idempotency, retries, dead-letter visibility, TDD-friendly failing tests, stronger ports-and-adapters boundaries, docs, and release notes.
```

## How It Relates To `claude-config`

Recommended setup:

1. install `claude-config` as your baseline
2. install `claude-tech-squad` as your execution plugin
3. use the plugin for complex delivery
4. use `claude-config` commands and skills for narrower support tasks

Rule of thumb:

- `/claude-tech-squad:implement` can be driven by the approved package
- `/claude-tech-squad:squad` should assume tests-first execution for code changes unless it explicitly declares an exception
