---
name: squad
description: Run the full technology squad workflow end-to-end with the full specialist bench: discovery, blueprint, implementation, quality, documentation, Jira/Confluence, reliability, and release preparation.
---

# /squad — Full Technology Squad

Run the complete workflow with the full technology squad. This command is best when the user wants end-to-end delivery, but discovery and blueprint remain interactive for the decisions that require user input.

## Core Principle

Do not assume the stack, the conventions, or the product domain. Discover them from the repository and validate technical decisions against current documentation.

---

## Phase 1: Discovery

Follow the exact `/discovery` process:

1. Repository recon
2. PM first pass
3. Business analysis
4. PO prioritization
5. User answers product and domain questions
6. Planner feasibility
7. User resolves feasibility tradeoffs

Do not proceed until requirements are confirmed.

---

## Phase 2: Blueprint

Follow the exact `/discovery` blueprint process:

1. Overall Architect
2. Tech Lead execution plan
3. User resolves overall design questions
4. Relevant specialist design agents
5. User resolves specialist design questions if any
6. Test Planner
7. Quality, governance, and operations baselines
8. User confirms the final blueprint

Do not proceed until the user explicitly confirms the blueprint.

---

## Phase 3: Build

Follow the exact `/implement` build process:

1. Run Tech Lead coordination
2. Run relevant implementation agents:
   - `claude-tech-squad:backend-dev`
   - `claude-tech-squad:frontend-dev`
   - `claude-tech-squad:platform-dev`
   - `claude-tech-squad:integration-engineer`
   - `claude-tech-squad:ai-engineer`
   - `claude-tech-squad:devops`
   - `claude-tech-squad:ci-cd`
   - `claude-tech-squad:dba`
3. Run `claude-tech-squad:reviewer`
4. Run continuous quality agents
5. Loop on build issues until approved or blocked

---

## Phase 4: Quality

Follow the exact `/implement` quality process:

1. Full QA and integration validation
2. Specialist quality reviews
3. Documentation and Jira/Confluence updates
4. PM UAT
5. Loop on critical issues until approved or blocked

---

## Phase 5: Release

### Step 5.1: Release Plan

Use the Agent tool with `subagent_type: "claude-tech-squad:release"`.

Prompt:
```
You are the Release agent.

Review the implemented change set and prepare a release plan.

Use the architecture package, QA reports, specialist reviews, docs update plan, Jira / Confluence pack, and UAT result as inputs.

MANDATORY:
- Validate CI/CD and deployment tooling against current docs when relevant
- Inventory env vars, migrations, breaking changes, and rollback steps
- Produce a concrete release plan
```

### Step 5.2: Reliability Sign-Off

Use the Agent tool with `subagent_type: "claude-tech-squad:sre"`.

Prompt:
```
You are the SRE agent.

Review the release plan, observability findings, performance review, and operational changes.

Produce reliability guardrails, rollout advice, and rollback concerns.
```

---

## Final Output

```
## Squad Complete

### Product
- User story: [...]
- Acceptance criteria: [...]
- Release slice: [...]

### Architecture
- Overall design: [...]
- Tech lead plan: completed
- Specialist notes: [summary]
- Quality baselines: completed
- Test plan: completed

### Delivery
- Workstreams executed: [...]
- Review: APPROVED / CHANGES REQUESTED
- Continuous quality: PASS / FAIL
- Full QA: PASS / FAIL
- Specialist reviews: [summary]
- Docs: updated / plan produced
- Jira / Confluence: updated / pack produced
- UAT: APPROVED / REJECTED

### Release
- Release plan: completed
- SRE sign-off: completed
- Breaking changes: [...]
- Rollback plan: defined

### Stack Validation
- Docs checked via context7 for: [...]
```
