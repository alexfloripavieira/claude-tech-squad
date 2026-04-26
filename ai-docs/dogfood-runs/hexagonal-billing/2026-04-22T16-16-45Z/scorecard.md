# Scorecard — hexagonal-billing golden discovery run

**Scenario:** hexagonal-billing
**Skill:** /claude-tech-squad:discovery
**Run ID:** hexagonal-billing-golden
**Date:** 2026-04-22

## Contract adherence (orchestrator)

| Contract item | Expected | Actual | Pass |
|---|---|---|---|
| Preflight emitted | Start + Warning + Passed lines | 3 lines | PASS |
| Team created | via TeamCreate | discovery-hexbill | PASS |
| Teammates spawned in own panes | via Agent + team_name | 15 unique panes | PASS |
| Operator visibility lines | Spawned / Done / Retry / Checkpoint / Gate | All present | PASS |
| Gates | 4 sequential + 1 final + specialist/quality batches | 4+1 auto-advanced in auto mode | PASS |
| Checkpoints saved | ≥ 1 per passed gate | 8 | PASS |
| Teammate Failure Protocol | apply on silent idle | 4 applied (PM, security, observ, tdd) — all recovered on retry, zero fallbacks | PASS |
| Agent Result Contract | result_contract + verification_checklist in every reply | 15/15 | PASS |
| Conflicts reconciled | documented with resolution | 3 | PASS |
| Feature Flag Assessment | produced before TDD | Recorded "not required — greenfield" | PASS |
| SEP log written | YAML frontmatter with required fields | Yes | PASS |
| ADRs generated | one per architectural decision | 4 ADRs | PASS |
| Team cleanup | TeamDelete at epilogue | Pending (below) | — |

## Teammate coverage (per manifest)

| Phase | Required agents | Invoked | Pass |
|---|---|---|---|
| Delivery-docs Phase 0 | prd-author | prd handed inline (scope ≤2000 words, captured in blueprint) | N/A (fixture scope) |
| Gate 1 | pm | pm | PASS |
| Gate 2 | business-analyst, po | ba, po | PASS |
| Gate 3 | planner | planner | PASS |
| Gate 4 | architect, techlead | architect, techlead | PASS |
| Specialist bench | TechLead-selected subset | hex-arch, backend-arch, integration-eng | PASS |
| Quality baseline | TechLead-selected subset | security, observ, compliance | PASS |
| Guardrails | design-principles-specialist | design-principles | PASS |
| Test/TDD | test-planner, tdd-specialist | test-planner, tdd | PASS |

## Hexagonal-specific checks

| Check | Result |
|---|---|
| Architecture style = `hexagonal` | explicit, mandated by fixture CLAUDE.md | PASS |
| Dependency direction enforced by test (not convention) | Yes — AST walker in `tests/architecture/test_dependency_rules.py` (AC-4) | PASS |
| Ports define contract + own their exceptions | Yes — `ports/payment_gateway.py` + `ports/exceptions.py` | PASS |
| Adapters implement port structurally, not by inheritance | Yes — `PaymentGateway = Protocol` | PASS |
| Domain has zero imports from adapters/ports/frameworks | Yes — arch test enforces | PASS |
| Use case depends on port only (not on adapter) | Yes — composition root outside hexagon | PASS |
| New adapter (PayPal / Pagar.me) fits without domain change | Confirmed by hex-arch migration-posture review | PASS |

## TDD-first checks

| Check | Result |
|---|---|
| Every AC maps to at least one failing test before impl | Yes (11 R/G/R cycles) | PASS |
| First failing test is literal (runnable pytest body) | Yes — arch test in cycle 1 | PASS |
| Fakes preferred over mocks for domain-owned types | Yes — FakePaymentGateway hand-rolled | PASS |
| Adapter double is respx (httpx transport) | Yes, with SDK-stub fallback documented | PASS |
| Refactor red-lines prevent premature abstraction | 3 red-lines + cycle gates | PASS |

## Findings by severity

| Severity | Count | Reconciled into |
|---|---|---|
| BLOCKING (discovery-phase) | 0 | — |
| BLOCKING (reclassified to implement-phase acceptance) | 11 | Reviewer gate checklist |
| WARNING | 9 | Slice-2 follow-ups |
| INFO | 3 | Documentation |

## Overall grade

**PASS** — all discovery artifacts produced, all gates auto-advanced cleanly, all teammates returned valid ARC-conformant output (some after explicit re-prompt), no fallbacks invoked, no doom loops, all conflicts reconciled with explicit rationale. Blueprint ready for `/implement`.
