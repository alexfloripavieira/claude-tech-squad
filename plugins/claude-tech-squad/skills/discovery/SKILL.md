---
name: discovery
description: Run discovery and blueprint for any software project with a full specialist squad. Produces product definition, prioritization, business analysis, architecture, specialist design notes, quality baselines, and delivery artifacts guidance.
---

# /discovery — Discovery & Blueprint

Run the planning phases before implementation. This command is generic and adapts to the current repository instead of assuming a specific framework, stack, or product domain.

## Core Principle

All technical decisions must be grounded in the repository's real stack, conventions, and current documentation via context7.

## Operator Visibility Contract

This workflow must make agent activity visible in the terminal output.

For every agent handoff, emit these plain-text progress lines:

- `[Phase Start] <phase-name>`
- `[Agent Start] <role> | <subagent_type> | <objective>`
- `[Agent Done] <role> | Status: completed | Output: <one-line summary>`
- `[Agent Blocked] <role> | Waiting on: <missing input or user decision>`

When multiple specialists run in parallel, emit:

- `[Agent Batch Start] <phase-name> | Agents: <comma-separated roles>`
- one `Agent Start` / `Agent Done` line per agent
- `[Agent Batch Done] <phase-name> | Outcome: <one-line summary>`

Do not silently switch phases or invoke agents without printing the handoff line first.
If the UI suppresses tool-level detail, these visibility lines are still mandatory in the assistant output.

## Step 0: Repository Recon

Before invoking any agent:

1. Identify the real stack from dependency, build, and deployment files.
2. Read local instructions and conventions if present:
   - `CLAUDE.md`
   - `AGENTS.md`
   - `README*`
   - `CONTRIBUTING*`
   - architecture docs, ADRs, runbooks, API specs, migration docs
3. Search for visual design assets and planning artifacts if relevant:
   - `.pen` files
   - PRDs, tickets, RFCs, backlog docs
4. Identify test, CI/CD, and runtime clues:
   - workflow files
   - Docker / compose / infra files
   - build scripts
   - observability and analytics config

Record these findings and pass them to the agents.

---

## Phase 1: Product, Business, and Feasibility

### Step 1.1: PM — First Pass

Use the Agent tool with `subagent_type: "claude-tech-squad:pm"`.

Prompt:
```
You are the PM agent. Follow the PM instructions exactly.

User request: {{input}}

Repository context:
- Stack files found: [list]
- Conventions/docs found: [list]
- Existing specs/tickets/designs found: [list]

Do NOT finalize immediately.
Start with a first-pass analysis, challenge scope, propose alternatives, and ask the user the questions that materially affect what should be built.
```

### Step 1.2: Business Analyst — Domain Clarification

Use the Agent tool with `subagent_type: "claude-tech-squad:business-analyst"`.

Prompt:
```
You are the Business Analyst agent.

Initial PM output:
[Insert PM output]

Repository context:
[Insert relevant recon findings]

Clarify business rules, actor flows, domain constraints, operational edge cases, and dependencies that materially affect implementation.
```

### Step 1.3: PO — Scope and Release Slice

Use the Agent tool with `subagent_type: "claude-tech-squad:po"`.

Prompt:
```
You are the PO agent.

Initial PM output:
[Insert PM output]

Business analysis:
[Insert Business Analyst output]

Propose the MVP slice, defer candidates, and release increments the user should approve.
```

### Interaction Gate

1. Present PM, Business Analyst, and PO outputs to the user.
2. Ask the user to answer the product and domain questions.
3. Re-run PM, Business Analyst, or PO if needed until the product definition and release slice are confirmed.

### Step 1.4: Planner — Technical Discovery

Use the Agent tool with `subagent_type: "claude-tech-squad:planner"`.

Prompt:
```
You are the Planner agent. Follow the Planner instructions exactly.

Confirmed product package:
- PM output: [Insert PM output]
- Business Analyst output: [Insert Business Analyst output]
- PO output: [Insert PO output]

User answers so far:
[Insert relevant user answers]

MANDATORY:
1. Read the real dependency, build, test, and deployment files.
2. Check project conventions already present in the repo.
3. Use resolve-library-id then query-docs via context7 for each relevant framework or library.
4. Produce feasibility, risks, workstreams, and user tradeoffs.
```

### Interaction Gate

1. Present the Planner findings to the user.
2. Ask the user to answer the Planner questions and confirm tradeoffs.
3. Re-run Planner if answers materially change scope.

---

## Phase 2: Blueprint

### Step 2.1: Architect — Overall Design

Use the Agent tool with `subagent_type: "claude-tech-squad:architect"`.

Prompt:
```
You are the Architect agent. Follow the Architect instructions exactly.

Confirmed product package:
- PM output: [Insert PM output]
- Business Analyst output: [Insert Business Analyst output]
- PO output: [Insert PO output]

Confirmed Planner output:
[Insert Planner output]

User decisions so far:
[Insert relevant user decisions]

MANDATORY:
- Validate design assumptions against current docs with context7
- Design the whole system shape first
- Define workstream boundaries and implementation order
- Ask the user the key design questions before finalizing
```

### Step 2.2: Tech Lead — Execution Direction

Use the Agent tool with `subagent_type: "claude-tech-squad:techlead"`.

Prompt:
```
You are the Tech Lead agent.

Confirmed product package:
[Insert PM, Business Analyst, and PO outputs]

Confirmed Planner output:
[Insert Planner output]

Architect output:
[Insert Architect output]

Reconcile the design into a realistic execution plan, define workstream ownership, and identify unresolved technical decisions.
```

### Interaction Gate

1. Present the Architect and Tech Lead outputs to the user.
2. Ask the user to answer the design questions and confirm the overall direction.
3. Re-run Architect or Tech Lead if needed.

### Step 2.3: Specialist Design Bench

Invoke only the specialist agents relevant to the task:

- `claude-tech-squad:backend-architect`
- `claude-tech-squad:frontend-architect`
- `claude-tech-squad:data-architect`
- `claude-tech-squad:ux-designer`
- `claude-tech-squad:api-designer`
- `claude-tech-squad:ai-engineer`
- `claude-tech-squad:integration-engineer`
- `claude-tech-squad:devops`
- `claude-tech-squad:ci-cd`
- `claude-tech-squad:dba`

Use the Architect and Tech Lead outputs to decide which ones are needed. Skip unused slices.

Prompt template:
```
You are the [specialist] agent. Follow your agent definition exactly.

Confirmed product package:
[Insert PM, Business Analyst, and PO outputs]

Confirmed Planner output:
[Insert Planner output]

Confirmed architecture package:
- Overall architecture: [Insert Architect output]
- Tech lead execution plan: [Insert Tech Lead output]

Focus only on your slice. Validate framework usage via context7. Ask only the questions that remain open for your area.
```

### Interaction Gate

If specialist design agents raise blocking questions, present them to the user and resolve them before continuing.

### Step 2.4: Test Planner

Use the Agent tool with `subagent_type: "claude-tech-squad:test-planner"`.

Prompt:
```
You are the Test Planner agent. Follow the Test Planner instructions exactly.

Confirmed PM output:
[Insert PM output]

Confirmed architecture package:
- Planner output: [Insert Planner output]
- Architect output: [Insert Architect output]
- Tech Lead output: [Insert Tech Lead output]
- Specialist notes: [Insert relevant specialist notes]

Read the real test setup in the repo and validate testing APIs via context7.
Produce the full test plan.
```

### Step 2.5: Quality, Governance, and Operations Baselines

Run the relevant specialists for baseline review:

- `claude-tech-squad:security-reviewer`
- `claude-tech-squad:privacy-reviewer`
- `claude-tech-squad:compliance-reviewer`
- `claude-tech-squad:accessibility-reviewer`
- `claude-tech-squad:performance-engineer`
- `claude-tech-squad:observability-engineer`
- `claude-tech-squad:analytics-engineer`
- `claude-tech-squad:jira-confluence-specialist`

Use concise prompts tied to the confirmed blueprint and ask each specialist for the minimum baseline needed before implementation starts.

### Final Blueprint Gate

Present the complete blueprint to the user and ask:

"Discovery complete. Are you happy with this plan, or do you want to adjust requirements, architecture, delivery boundaries, or release slicing before implementation?"

Do not enter build mode until the user explicitly confirms.

---

## Output: Discovery & Blueprint Document

```
## Discovery & Blueprint Document

### 0. Agent Execution Log
- Phase: [...]
- Role: [...] | Subagent: [...] | Status: [...] | Output: [...]
- Role: [...] | Subagent: [...] | Status: [...] | Output: [...]

### 1. Product Definition
[Final PM output]

### 2. Business Analysis
[Business Analyst output]

### 3. Product Prioritization
[PO output]

### 4. Technical Requirements
[Planner output]

### 5. Overall Architecture
[Architect output]

### 6. Tech Lead Execution Plan
[Tech Lead output]

### 7. Specialist Notes
#### Backend
[If present]

#### Frontend
[If present]

#### Data
[If present]

#### UX
[If present]

#### API
[If present]

#### AI
[If present]

#### Integration
[If present]

#### DevOps
[If present]

#### CI/CD
[If present]

#### DBA
[If present]

### 8. Quality, Governance, and Operations Baselines
#### Security
[If present]

#### Privacy
[If present]

#### Compliance
[If present]

#### Accessibility
[If present]

#### Performance
[If present]

#### Observability
[If present]

#### Analytics
[If present]

#### Jira / Confluence
[If present]

### 9. Test Plan
[Test Planner output]

### 10. Stack & Conventions Observed
- Stack: [...]
- Repo conventions: [...]
- CI / deploy clues: [...]
- Design assets / specs: [...]

### 11. Delivery Workstreams
- Backend: [...]
- Frontend: [...]
- Data: [...]
- AI: [...]
- Integrations: [...]
- Platform: [...]
- DevOps / CI-CD: [...]
- Docs / Jira / Confluence: [...]
- QA / Risk / Reliability: [...]
```
