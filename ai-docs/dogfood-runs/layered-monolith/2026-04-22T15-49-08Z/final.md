# Discovery & Blueprint — Audit-Log Filters (Layered Monolith)

## 0. Agent Execution Log

- Team: discovery (inline/virtual)
- prd-author | completed | PRD synthesized inline
- pm | completed | acceptance criteria for 3 filters + pagination
- ba | completed | business rules documented
- po | completed | scope cut: filter trio in, export/FTS out
- planner | completed | selected option A (extend layered module)
- architect | completed | preserve layered pattern, FilterSpec in service
- techlead | completed | single workstream; minimal bench
- specialist-bench | completed | backend-architect only (1/1)
- quality-baseline | completed | security + performance + observability (3/3, privacy/compliance skipped — not applicable)
- design-principles | completed | enforce api→service→repo direction
- test-planner | completed | unit + integration
- tdd-specialist | completed | RGR cycles per filter

## 1. Product Definition (PM)

**Problem:** operators cannot narrow audit logs to investigate incidents — every query returns the full table.

**User stories:**
- As an operator, I filter by actor to find everything one user did.
- As an operator, I filter by action type to isolate one class of events.
- As an operator, I filter by date range to scope an investigation window.

**Acceptance criteria:**
1. `GET /audit-logs` accepts `actor`, `action`, `from`, `to`, `page`, `pageSize`.
2. String filters are case-insensitive and trimmed.
3. Date-range is a closed interval validated as ISO-8601.
4. Results are ordered by `created_at DESC` with stable pagination.
5. Page size capped at 100; default 25.

## 2. Business Analysis (BA)

- Audit logs are append-only; filters MUST NOT mutate.
- Actor id is already exposed to operators; no new PII.
- Action values come from a known vocabulary (LOGIN, LOGOUT, UPDATE, etc.) — filter comparison is uppercased.
- Unknown actions return empty set, not 400.

## 3. Prioritization (PO)

**IN scope (this release):**
- Filter by actor, action, date-range
- Pagination with stable ordering

**OUT of scope:**
- Full-text search on payload
- CSV/JSON export
- Retention / archival policy
- Cross-tenant search

Single deployment; no migration required for the filter parameters themselves.

## 4. Technical Requirements (Planner)

**Option A — Extend current layered module (SELECTED)**
- Add filter params to `listAuditLogs`, widen `FilterSpec`, push predicates into `buildAuditLogQuery`.
- Rationale: 3 fields + pagination is well under the threshold where a query-builder earns its keep; YAGNI.

**Option B — Introduce generic query-builder abstraction (REJECTED)**
- Adds a layer, more tests, more surface area; no known second consumer.

**Risks:** table scan if no index; caps and indexing addressed in quality phase.

## 5. Architecture (Architect)

Preserve layered pattern — no Ports & Adapters.

```
controller (api/auditLogController.ts)
   │   validates + parses query params -> FilterSpec
   ▼
service (service/auditLogService.ts)
   │   normalizeAuditFilters(FilterSpec) -> NormalizedFilterSpec
   │   applies business rules (uppercase action, trim strings, validate dates)
   ▼
repository (repo/auditLogRepository.ts)
   │   buildAuditLogQuery(NormalizedFilterSpec) -> { where, orderBy, limit, offset }
```

**FilterSpec shape:**
```ts
type FilterSpec = {
  actor?: string;
  action?: string;
  from?: string; // ISO-8601
  to?: string;   // ISO-8601
  page?: number;
  pageSize?: number;
};
```

Dependency direction: api → service → repo only. Repo does not import service or api.

## 6. Tech Lead Execution Plan

**Workstreams:** backend (only).

**Sequence:**
1. Extend `normalizeAuditFilters` to cover action upper-casing, date validation, pagination clamping.
2. Extend `buildAuditLogQuery` to emit predicates for each field and pagination.
3. Wire new query params in `listAuditLogs` controller.
4. Add composite index migration (guarded — only if repo owner confirms DB layer).

**Specialists required:** backend-architect.
**Specialists explicitly NOT required:** hexagonal-architect, frontend-architect, api-designer, data-architect, ux-designer, ai-engineer, integration-engineer, devops, ci-cd, dba, privacy-reviewer, compliance-reviewer.

## 7. Specialist Notes

### Backend (backend-architect)

- Keep FilterSpec type colocated in `service/auditLogService.ts` (single source of truth for normalization rules).
- Controller `listAuditLogs` should reject unknown query params (fail-fast) rather than silently forward.
- Repo `buildAuditLogQuery` returns a plain object — no ORM coupling — so it remains testable as pure function.
- Pagination: normalize `page>=1`, `pageSize in [1,100]` at the service layer, not the controller.

## 8. Design Principles Guardrails

- SRP: normalization stays in service; query translation stays in repo.
- DIP: service depends on `FilterSpec` type, not on DB types.
- Testability: every layer is a pure function given the current fixture — preserve that.
- Simplicity: no interfaces/abstract classes unless a second implementation appears.

## 9. Quality, Governance, Operations Baselines

### Security
- No auth change, no new PII. Validate types on input (string length, ISO-8601). Not auth-touching — security-reviewer gate SOFT.

### Performance
- Composite index `(actor, action, created_at)` recommended when the table exceeds 100k rows.
- Hard cap `pageSize <= 100` in service.

### Observability
- Structured log per filter request: `{ filters, result_count, duration_ms }`, actor id redacted at log sink if policy requires.
- Counter metric: `audit_log_filter_requests_total{action,has_actor,has_range}`.

### Privacy / Compliance
- Not applicable — no new personal data processed or persisted.

## 10. Test Plan

- **Unit (node:test):** `normalizeAuditFilters` — trim, upper-case action, clamp pagination, reject invalid date.
- **Unit:** `buildAuditLogQuery` — emits correct `where`/`orderBy`/`limit`/`offset` for each combination.
- **Integration:** `listAuditLogs` controller — valid request → normalized filters → query shape; invalid date → 400.
- **No e2e** — pure in-process layered monolith.

## 11. TDD Delivery Plan

Red-green-refactor cycles, in order:

1. RGR: `normalizeAuditFilters` trims strings (already green — baseline).
2. RGR: `normalizeAuditFilters` upper-cases `action`.
3. RGR: `normalizeAuditFilters` validates ISO-8601 `from`/`to`.
4. RGR: `normalizeAuditFilters` clamps `pageSize` to [1,100].
5. RGR: `buildAuditLogQuery` emits `where` fragments per filter.
6. RGR: `buildAuditLogQuery` emits `orderBy: [{created_at: 'desc'}]` and `limit/offset`.
7. RGR: `listAuditLogs` controller wires query params through service to repo; rejects unknown params.

## 12. Stack & Conventions Observed

- Stack: Node.js + TypeScript + `node:test` + eslint + tsc.
- Conventions: one module per feature under `src/modules/<feature>/{api,service,repo}`.
- CI: `npm test` / `npm run lint` / `npm run build` per fixture `package.json`.
- No DB migrations tooling in fixture — DB index is a follow-up note, not part of slice.

## 13. Delivery Workstreams

- Backend: all 7 TDD cycles above.
- Frontend: none (no UI in fixture).
- Data: optional composite index (deferred — owner confirmation needed).
- AI: none.
- Integrations: none.
- Platform: none.
- DevOps / CI-CD: none (existing `npm test` pipeline covers).
- Docs / Jira / Confluence: update audit-log module README with new filter params.
- QA / Risk / Reliability: verify pagination stability under concurrent writes (note only; append-only table mitigates most risks).

---

## Next Step

`/implement ai-docs/audit-log-filters/blueprint.md`

## result_contract

```yaml
result_contract:
  status: completed
  scenario_id: layered-monolith
  skill: discovery
  execution_mode: inline
  artifacts:
    - ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z/prompt.txt
    - ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z/trace.md
    - ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z/final.md
    - ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z/metadata.yaml
    - ai-docs/dogfood-runs/layered-monolith/2026-04-22T15-49-08Z/scorecard.md
    - ai-docs/.squad-log/2026-04-22T15-49-08Z-discovery-audit-log-filters.md
  gates:
    gate_1_product_definition: approved
    gate_2_scope_validation: approved
    gate_3_technical_tradeoffs: approved
    gate_4_architecture_direction: approved
    final_blueprint_confirmation: approved
  next_action: "/implement ai-docs/audit-log-filters/blueprint.md"
```
