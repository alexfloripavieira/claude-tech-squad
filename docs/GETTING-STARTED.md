# Getting Started

This guide explains:

- what `claude-tech-squad` is for
- how to install it
- how to enable teammate mode (each specialist in its own tmux pane)
- which commands to run and when
- example prompts for real delivery work
- how to interpret visible squad execution

## What `claude-tech-squad` Is

`claude-tech-squad` is the execution layer.

It is not a general config pack. It is the specialist team you run inside a real repository when you need coordinated product and engineering delivery.

Use it for:

- discovery and scope clarification
- architecture, TDD-first implementation planning, and implementation coordination
- multi-specialist delivery across 59 specialist agents
- test, review, documentation, Jira/Confluence, and release follow-through

If you need baseline commands, skills, rules, and templates, use `claude-config`.

## Install In Claude Code

### Step 1 — Add the Marketplace

Run once per machine:

```bash
claude plugin marketplace add alexfloripavieira/claude-tech-squad
```

Or inside Claude Code:

```text
/plugin marketplace add alexfloripavieira/claude-tech-squad
```

### Step 2 — Install the Plugin

**Global (available in any repository):**

```bash
claude plugin install -s user claude-tech-squad@alexfloripavieira-plugins
```

**Project only:**

```bash
claude plugin install -s project claude-tech-squad@alexfloripavieira-plugins
```

**Local (current Claude context only):**

```bash
claude plugin install -s local claude-tech-squad@alexfloripavieira-plugins
```

---

## Teammate Mode — Each Specialist in Its Own Pane

By default, agents run as inline subagents — one after another inside the same Claude session. With teammate mode enabled, each specialist spawns as an independent Claude Code instance in a separate tmux pane.

### Requirements

1. Claude Code must be started **inside a tmux session**
2. Two environment variables must be set in `~/.claude/settings.json`

### Step 1 — Configure settings.json

Open `~/.claude/settings.json` and add:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "CLAUDE_CODE_TEAMMATE_MODE": "tmux"
  }
}
```

If the file already has an `"env"` section, add only the two keys inside it.

### Step 2 — Start Claude Code inside tmux

Every time you want teammate panes, open a terminal and run:

```bash
# Create a new tmux session named "squad"
tmux new-session -s squad

# Then start Claude Code inside it
claude
```

Or attach to an existing session:

```bash
tmux attach -t squad
claude
```

### Step 3 — Run any squad command

Once inside tmux with the env vars set, any `/discovery`, `/implement`, or `/squad` command will:

1. Create a team via `TeamCreate`
2. Spawn each specialist as a teammate in its own tmux pane
3. Show gates for user decisions at key points

### What to expect

When teammate mode is active you will see output like:

```text
[Team Created] discovery
[Teammate Spawned] pm | pane: pm
[Teammate Spawned] ba | pane: ba
[Gate] Scope Validation | Waiting for user input
[Batch Spawned] specialist-bench | Teammates: backend-arch, frontend-arch, api-designer
[Teammate Done] reviewer | Status: APPROVED
```

Each pane shows the specialist working independently. The orchestrator (your main pane) coordinates the flow and presents gates for your input.

### Without tmux

If you run the commands without tmux mode, the workflows still work correctly — agents run inline as subagents. You get the same outputs and gates, but no separate panes.

### SEP logs in teammate mode

When running in teammate mode, each specialist runs in its own Claude Code instance. The **Squad Execution Protocol (SEP)** ensures observability regardless of mode: every skill writes a structured log to `ai-docs/.squad-log/` before the pane exits. This means `/factory-retrospective` always has a persistent trace of what ran, even when there is no shared conversation history to inspect. See MANUAL.md section 13 for the full SEP reference.

---

## Commands

### `/claude-tech-squad:hotfix`

Use quando produção está quebrada e você precisa de um patch agora. Mais rápido que `/bug-fix` — intake → root cause → patch mínimo → branch `hotfix/` → PR → deploy checklist.

```text
/claude-tech-squad:hotfix
```

### `/claude-tech-squad:pr-review`

Use para revisar qualquer pull request com bench especializado. Detecta os revisores relevantes pelos arquivos alterados, roda em paralelo, consolida findings, e abre threads no GitHub.

```text
/claude-tech-squad:pr-review
https://github.com/org/repo/pull/42
```

### `/claude-tech-squad:discovery`

Use when the problem or feature still needs shaping. Produces a complete Discovery & Blueprint Document.

Chain: PM → Business Analyst → PO → Planner → Architect → TechLead → Specialists → Quality Baselines → Design Principles → Test Planner → TDD Specialist

Gates at: PO (scope), Planner (tradeoffs), TechLead (architecture direction), TDD Specialist (blueprint confirmation)

```text
/claude-tech-squad:discovery
Design a customer support workspace with ticket routing, audit history, and role-based administration.
```

```text
/claude-tech-squad:discovery
Build a RAG-powered travel agent chatbot that learns from interactions and handles flight and hotel search.
```

### `/claude-tech-squad:implement`

Use after discovery when the blueprint is agreed. Requires a Discovery & Blueprint Document in the conversation.

Chain: TDD Specialist (failing tests) → Implementation batch → Reviewer → QA → Quality bench → Docs Writer → Jira/Confluence → PM UAT

```text
/claude-tech-squad:implement
Use the approved discovery package and implement the next delivery slice with TDD cycles.
```

### `/claude-tech-squad:squad`

Use when you want the full path from idea to release in one workflow.

Phases: Discovery (with gates) → Implementation (TDD-first) → Release (Release + SRE sign-off)

For code changes, this command is TDD-first by default.

```text
/claude-tech-squad:squad
Add SSO login, audit events, admin controls, automated coverage, documentation, and release artifacts.
```

```text
/claude-tech-squad:squad
Build a webhook reliability improvement package with idempotency, retries, dead-letter visibility, and release notes.
```

---

## Prompt Patterns That Work Well

Good inputs usually include:

- the business outcome
- the main user or persona
- the constraints (performance, compliance, incremental rollout)
- any repo-specific context that matters

More examples:

```text
/claude-tech-squad:discovery
Create an internal billing admin surface for support operators. Invoice search, refunds, and access control. Keep rollout incremental.
```

```text
/claude-tech-squad:squad
Implement vector search for the knowledge base. Use pgvector with hybrid BM25 + semantic retrieval. TDD required. Cover RAG quality metrics.
```

```text
/claude-tech-squad:discovery
Add real-time monitoring dashboards in Grafana for token cost per user and RAG retrieval quality. Integrate with existing Prometheus stack.
```

---

## How It Relates To `claude-config`

Recommended setup:

1. Install `claude-config` as your baseline
2. Install `claude-tech-squad` as your execution plugin
3. Use the plugin for complex delivery
4. Use `claude-config` commands and skills for narrower support tasks

Rule of thumb:

- `/claude-tech-squad:implement` runs from the approved blueprint package
- `/claude-tech-squad:squad` assumes TDD-first for code changes unless it declares an exception

---

## Specialist Roster Quick Reference

| Category | Agents |
|---|---|
| Discovery | pm, business-analyst, po, planner, architect, techlead |
| Architecture | backend-architect, frontend-architect, api-designer, data-architect, ux-designer, ai-engineer, agent-architect, integration-engineer, devops, ci-cd, dba, platform-dev, cloud-architect |
| LLM / AI | prompt-engineer, rag-engineer, llm-eval-specialist, conversational-designer, ml-engineer |
| Implementation | backend-dev, frontend-dev, mobile-dev, data-engineer, tdd-specialist |
| Search | search-engineer |
| Quality | reviewer, qa, test-planner, test-automation-engineer, integration-qa |
| Specialist Review | security-reviewer, security-engineer, privacy-reviewer, compliance-reviewer, accessibility-reviewer, performance-engineer, chaos-engineer, design-principles-specialist, code-quality |
| Observability | observability-engineer, monitoring-specialist, analytics-engineer |
| Design | design-system-engineer |
| Business & Growth | solutions-architect, growth-engineer |
| Docs / DX | docs-writer, tech-writer, devex-engineer, developer-relations, jira-confluence-specialist |
| Operations | release, sre, cost-optimizer, incident-manager |

Total: 59 specialists.
