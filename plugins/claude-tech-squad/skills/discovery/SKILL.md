---
name: discovery
description: Run discovery and blueprint for any software project with a full specialist squad. Produces product definition, prioritization, business analysis, architecture, specialist design notes, test and TDD delivery guidance, quality baselines, and delivery artifacts guidance.
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

## Execution

### Step 1 — Repository Recon
Read the following files to understand the project:
- README.md, CLAUDE.md, package.json, pyproject.toml, requirements.txt
- List the main directories and identify the tech stack
- Note any existing architecture patterns, conventions, or constraints

### Step 2 — Start the Discovery Chain
The agents will chain autonomously from PM through to the final blueprint gate.

Invoke PM using the Agent tool with `subagent_type: "claude-tech-squad:pm"`:

```
## Discovery Start — Repository Context

### Stack
{{detected_stack}}

### Project structure
{{key_directories_and_files}}

### CLAUDE.md summary
{{claude_md_summary}}

### Task/Feature requested
{{user_request}}

---
Start the discovery chain. Analyze the problem from a product perspective. Define user stories and acceptance criteria. Then chain to Business Analyst → PO → Planner → Architect → Tech Lead → Specialists → Design Principles → Test Planner → TDD Specialist.

The chain will present gates to the user at: (1) after PO — scope validation, (2) after Planner — technical tradeoffs, (3) after Tech Lead — architecture direction, (4) after TDD Specialist — final blueprint confirmation.
```

### Step 3 — Await Completion
The chain runs autonomously and presents gates to you at key decision points. Respond to each gate to keep the chain moving. The discovery is complete when TDD Specialist presents the Final Blueprint and you confirm.

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

### 8. Design Principles Guardrails
[Design Principles Specialist output]

### 9. Quality, Governance, and Operations Baselines
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

### 10. Test Plan
[Test Planner output]

### 11. TDD Delivery Plan
[TDD Specialist output]

### 12. Stack & Conventions Observed
- Stack: [...]
- Repo conventions: [...]
- CI / deploy clues: [...]
- Design assets / specs: [...]

### 13. Delivery Workstreams
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
