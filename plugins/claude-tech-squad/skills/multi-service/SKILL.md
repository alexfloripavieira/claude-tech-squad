---
name: multi-service
description: Coordinates feature delivery across multiple repositories and services. Maps inter-service dependencies, negotiates API contracts, sequences deployments safely, and validates cross-service integration. Trigger with "feature em multiplos servicos", "multi-service", "mudanca cross-service", "coordenar servicos", "feature distribuida", "multi-repo feature".
user-invocable: true
---

# /multi-service — Cross-Service Feature Coordination

Coordinates the delivery of a feature that spans multiple independent services or repositories. Prevents the classic distributed systems failure mode: teams deploy independently, contracts break, production goes down.

**Core principle:** No service deploys until all contracts are agreed, all integration tests pass, and a safe rollback sequence exists for every service involved.

**Escalate to `/squad` if:** the feature is contained to a single repository. This skill is only for features that genuinely require coordinated changes across 2+ independent services.

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Deploy any service to production before all contract tests pass across all involved services
- Merge a breaking API change to a shared contract without a versioning or backward-compatibility strategy
- Deploy services in an order that would leave the system in an inconsistent state (even briefly)
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL without a verified rollback script and explicit user confirmation
- Delete cloud resources in production
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Deploy to production before staging has been successfully deployed and verified for ALL involved services
- Apply migrations to production without confirming a recent backup exists

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

## When to Use

- A feature requires changes in 2+ independent services or repositories
- An API contract change affects multiple consumers
- A database schema change is shared across services
- A new service is being introduced that other services will depend on
- When the user says: "feature em multiplos servicos", "multi-service", "mudanca cross-service", "coordenar servicos", "feature distribuida", "multi-repo feature"

## Execution

## Teammate Failure Protocol

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role.

**For every teammate spawned — without exception:**

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - Emit: `[Teammate Retry] <name> | Reason: silent failure — re-spawning`
   - Re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails:
   - Emit: `[Gate] Teammate Failure | <name> failed twice`
   - Surface to the user:

```
Teammate <name> failed to return a valid output (attempt 1 and 2).

Options:
- [R] Retry once more with the same prompt
- [S] Skip and continue — downstream quality WILL be degraded (log the risk)
- [X] Abort the run
```

4. **Sequential teammates** (output feeds the next agent): [S] degrades ALL downstream teammates that depend on this output — warn the user explicitly before accepting skip.
5. **Parallel batch teammates**: [S] on one agent does not block the batch, but the missing output must be logged as a risk in the final report.
6. **Do NOT advance to the next step** until every teammate in the current step has returned valid output, been explicitly skipped, or the run has been aborted.

### Step 1 — Service intake gate

Ask the user (if not already provided):

```
Para coordenar o delivery multi-service, preciso de:

1. Quais serviços estão envolvidos? (nomes + repos)
2. Qual é a feature ou mudança sendo entregue?
3. Quais serviços produzem contratos (APIs, eventos, schemas)?
4. Quais serviços consomem esses contratos?
5. Qual é o ambiente alvo? (staging / produção)
6. Existe um service mesh, API gateway, ou message broker central?
```

Do NOT proceed until services list and feature description are provided. This is a blocking gate.

### Step 2 — Map service dependency graph

For each service repository provided, read:
```bash
# Detect service type and tech stack
ls {{service_path}}/package.json {{service_path}}/pyproject.toml {{service_path}}/pom.xml {{service_path}}/go.mod 2>/dev/null | head -5

# Find API contract files
find {{service_path}} -name "openapi.yaml" -o -name "openapi.json" -o -name "swagger.yaml" \
  -o -name "*.proto" -o -name "asyncapi.yaml" -o -name "schema.graphql" 2>/dev/null | head -10

# Find event/message definitions
find {{service_path}} -name "*event*" -o -name "*message*" -o -name "*schema*" 2>/dev/null \
  | grep -E "\.(json|yaml|avro|proto)$" | grep -v node_modules | head -10
```

Build dependency graph:
```
Service A (producer) ──[REST API v2]──► Service B (consumer)
Service A (producer) ──[Kafka topic]──► Service C (consumer)
Service B (producer) ──[gRPC]──────────► Service D (consumer)
```

Identify:
- **Producers**: services that expose contracts (APIs, events, schemas)
- **Consumers**: services that depend on those contracts
- **Shared resources**: databases, caches, message brokers used by multiple services
- **Critical path**: the chain of dependencies that must be deployed in order

### Step 3 — Spawn integration-engineer for contract analysis

Use TeamCreate to create a team named "multi-service-team". Then spawn each agent using the Agent tool with `team_name="multi-service-team"` and a descriptive `name` for each agent.

```
Agent(
  subagent_type = "claude-tech-squad:integration-engineer",
  team_name = "multi-service-team",
  name = "integration-engineer",
  prompt = """
## Cross-Service Contract Analysis

### Services Involved
{{services_list_with_repos}}

### Feature Description
{{feature_description}}

### Existing Contracts Found
{{contract_files_content}}

### Dependency Graph
{{dependency_graph}}

---
You are the Integration Engineer. Analyze the contracts between these services for this feature.

1. **Contract changes required** — for each service pair:
   - What contract changes does this feature require?
   - Is the change backward-compatible or breaking?
   - If breaking: what is the versioning strategy? (v2 endpoint, header negotiation, parallel run, consumer-driven contract migration)

2. **Contract testing strategy**:
   - Which pairs need Pact / contract tests?
   - What is the minimal set of contract tests to validate this feature across services?
   - Are existing contract tests sufficient, or do new ones need to be written?

3. **Shared resource conflicts**:
   - Do any services share a database, cache, or topic that this feature touches?
   - What isolation strategy prevents one service's change from breaking another?

4. **Deployment ordering**:
   - What is the safe deployment sequence? (producers before consumers, or parallel if backward-compatible)
   - What is the rollback sequence if any service fails?

5. **Risk assessment**: HIGH / MEDIUM / LOW — with specific reasoning

Safety: Never recommend deploying a breaking change without a migration strategy.
Do NOT chain to other agents.
"""
)
```

Emit: `[Teammate Spawned] integration-engineer | pane: integration-engineer`

### Step 4 — Spawn architect for cross-service design

```
Agent(
  subagent_type = "claude-tech-squad:architect",
  team_name = "multi-service-team",
  name = "architect",
  prompt = """
## Cross-Service Architecture Review

### Services and Dependency Graph
{{dependency_graph}}

### Feature Requirements
{{feature_description}}

### Contract Analysis
{{integration_engineer_output}}

---
You are the Architect. Design the cross-service implementation strategy.

1. **Data consistency strategy**: how does this feature maintain consistency across service boundaries?
   - Synchronous (2PC, Saga) vs. asynchronous (eventual consistency, outbox pattern)
   - Where does the source of truth live?

2. **API evolution strategy**: if contracts change, which pattern applies?
   - Expand-and-contract (parallel fields)
   - Versioned endpoints (v1/v2)
   - Consumer-driven contract migration with feature flags
   - Strangler fig pattern

3. **Failure mode design**: what happens when one service in the chain is unavailable?
   - Circuit breakers between which pairs?
   - Fallback behaviors?
   - Retry policies with backoff?

4. **Observability requirements**: what tracing and monitoring is needed to detect cross-service failures?
   - Distributed trace IDs that span all services
   - Correlation IDs in events/messages
   - Which metrics alert on cross-service degradation?

5. **Deployment strategy recommendation**: rolling / blue-green / canary — per service

Return: architecture decisions with rationale. Do NOT chain.
"""
)
```

Emit: `[Teammate Spawned] architect | pane: architect`

### Step 5 — Gate: Contract and Architecture Alignment

Present to user:

```
Cross-Service Analysis Complete

Services involved: {{N}}
Contract changes: {{list}}
Breaking changes detected: {{yes/no — list if yes}}
Deployment order: {{sequence}}
Risk level: {{HIGH/MEDIUM/LOW}}

Architecture recommendation: {{summary}}

Issues requiring decision:
{{list_of_decisions_needed}}

Proceed with this approach? [Y/N/modify]
```

**This is a blocking gate.** Do NOT proceed until user confirms. Breaking changes require explicit acknowledgment.

### Step 6 — Spawn techlead for delivery sequencing

```
Agent(
  subagent_type = "claude-tech-squad:techlead",
  team_name = "multi-service-team",
  name = "techlead",
  prompt = """
## Multi-Service Delivery Plan

### Services
{{services_list}}

### Approved Architecture
{{architect_output}}

### Contract Changes
{{integration_engineer_output}}

---
You are the Tech Lead. Produce the delivery sequencing plan for this multi-service feature.

1. **Per-service work breakdown**: for each service, what code changes are needed?
   - API changes (producer side)
   - Consumer adaptations
   - Schema migrations
   - Test additions

2. **Development sequencing**: which teams/repos should start first?
   - Can development be parallel with contract stubs/mocks?
   - Which service needs to be code-complete first to unblock others?

3. **Integration test plan**: what cross-service tests must pass before any production deploy?
   - Contract tests (Pact or equivalent)
   - End-to-end smoke tests in staging
   - Which tests are blocking for production?

4. **Deployment runbook** — step-by-step ordered list:
   - Pre-deploy: {{checks before starting}}
   - Step 1: deploy {{service}} to staging
   - Step 2: run contract tests
   - Step 3: deploy {{next service}}
   - ...
   - Production deploy sequence (must mirror staging sequence)
   - Rollback sequence (reverse order with data rollback steps if needed)

5. **Parallel work opportunities**: what can be developed simultaneously with contract mocks?

Do NOT chain.
"""
)
```

Emit: `[Teammate Spawned] techlead | pane: techlead`

### Step 7 — Spawn SRE for blast radius and rollback assessment

```
Agent(
  subagent_type = "claude-tech-squad:sre",
  team_name = "multi-service-team",
  name = "sre",
  prompt = """
## Multi-Service Blast Radius Assessment

### Services and Dependencies
{{dependency_graph}}

### Deployment Plan
{{techlead_output}}

### Feature Scope
{{feature_description}}

---
You are the SRE. Assess reliability and rollback readiness for this multi-service deployment.

1. **Blast radius per service**: if this deploy fails mid-sequence, what is the impact on users?
   - Which services would be degraded vs. fully down?
   - Is there a "safe stopping point" in the deployment sequence?

2. **Rollback feasibility**: can each service be independently rolled back?
   - What is the data state after a partial rollback?
   - Are there database migrations that prevent clean rollback?
   - What is the maximum tolerable rollback time?

3. **Canary recommendation**: should any service use a canary deploy? (phased traffic shift)
   - Which services carry the most risk?
   - Recommended canary percentage and duration

4. **Monitoring checklist** — what to watch during and after each service deploy:
   - Error rates per service
   - Latency on cross-service calls
   - Message queue depth (if event-driven)
   - Database connection counts

5. **GO / NO-GO** per service: is each service ready for production?

Do NOT chain.
"""
)
```

Emit: `[Teammate Spawned] sre | pane: sre`

### Step 7b — Reviewer Gate

After SRE assessment, spawn reviewer to validate the full plan before the delivery package is produced:

```
Agent(
  subagent_type = "claude-tech-squad:reviewer",
  team_name = "multi-service-team",
  name = "reviewer",
  prompt = """
## Multi-Service Plan Review

### Contract Changes
{{integration_engineer_output}}

### Architecture
{{architect_output}}

### Deployment Sequencing
{{techlead_output}}

### SRE Assessment
{{sre_output}}

---
Review this multi-service delivery plan for:
1. Cross-service contracts — are they syntactically correct and backwards-compatible?
2. Deployment sequence — is the ordering safe? Any circular dependencies?
3. Rollback strategy — is each service independently rollback-able?
4. Integration test plan — is it complete enough to detect contract breaks?
5. API versioning approach — is it sound?

Return: APPROVED or CHANGES REQUESTED with specific issues.
Do NOT chain.
"""
)
```

If CHANGES REQUESTED: surface issues to the relevant specialist (integration-engineer or architect) for resolution. Re-run reviewer after fix. Max 2 review cycles.

Emit: `[Gate] Multi-Service Reviewer APPROVED | Advancing to delivery package`

### Step 8 — Produce delivery package

Generate the full multi-service delivery package:

```markdown
# Multi-Service Delivery Plan — {{feature_name}} — {{date}}

## Services Involved
| Service | Repo | Role | Changes |
|---------|------|------|---------|
| {{service}} | {{repo}} | producer/consumer | {{summary}} |

## Dependency Graph
```
{{ascii_dependency_graph}}
```

## Contract Changes
| Service Pair | Contract | Change Type | Strategy |
|---|---|---|---|
| A → B | REST /api/v2/orders | Breaking | Parallel v1+v2, sunset v1 in 30d |

## Deployment Sequence

### Staging
1. [ ] Deploy {{service_A}} to staging
2. [ ] Run contract tests: A→B, A→C
3. [ ] Deploy {{service_B}} to staging
4. [ ] Run integration smoke tests
5. [ ] Deploy {{service_C}} to staging
6. [ ] Run full end-to-end suite
7. [ ] SRE sign-off: staging verified

### Production
1. [ ] Deploy {{service_A}} to production (canary 10%)
2. [ ] Monitor: error rate < 0.1%, latency p95 < {{threshold}} for 15 min
3. [ ] Promote canary to 100%
4. [ ] Deploy {{service_B}} to production
5. [ ] Deploy {{service_C}} to production
6. [ ] Post-deploy monitoring: 30 min

### Rollback Sequence (reverse order)
1. [ ] Rollback {{service_C}}
2. [ ] Rollback {{service_B}}
3. [ ] Rollback {{service_A}} — note: migration {{X}} may need manual reversal

## Risk Assessment
- Overall risk: {{HIGH/MEDIUM/LOW}}
- Highest-risk service: {{service}} — reason: {{reason}}
- Canary recommended: {{yes/no}}

## Monitoring During Deploy
{{sre_monitoring_checklist}}
```

### Step 9 — Final gate

Present delivery package to user:

```
Multi-Service Delivery Package ready.

Services: {{N}}
Contract changes: {{N}} (breaking: {{N}})
Deployment steps: {{N}}
Risk: {{HIGH/MEDIUM/LOW}}
SRE: {{GO/NO-GO}}

Proceed? [Y] to save and finalize / [N] to revise
```

**This is a blocking gate.**

### Step 10 — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-multi-service-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: multi-service
timestamp: {{ISO8601}}
status: completed
services_count: N
breaking_changes: N
deployment_steps: N
risk_level: HIGH | MEDIUM | LOW
sre_result: GO | NO-GO
---

## Services
{{list}}

## Key Decisions
{{architecture_decisions}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 11 — Save plan and report to user

Write plan to `ai-docs/multi-service-{{feature_slug}}-{{date}}.md`.

Tell the user:
- Number of services coordinated
- Breaking contract changes (if any) and their migration strategies
- Deployment sequence (staging → production)
- Highest-risk service and mitigation
- Path to saved delivery plan
- Suggest: run `/squad` per service for implementation detail, then return here for coordinated deploy
