# Final — hexagonal-billing golden discovery run

**Status:** completed
**Blueprint:** [ai-docs/hexagonal-billing/blueprint.md](../../hexagonal-billing/blueprint.md)
**Architecture style:** hexagonal (explicit)
**Next:** `/claude-tech-squad:implement ai-docs/hexagonal-billing/blueprint.md`

## Decisions locked

| Topic | Decision | Source |
|---|---|---|
| Architecture | Hexagonal (mandated by fixture CLAUDE.md) | Fixture + architect + hex-arch |
| Port shape | `typing.Protocol` + frozen `CaptureResponse` dataclass, no `@runtime_checkable` | Planner / Backend-Arch |
| Use case signature | Raise on invariant/infra; return mutated `Invoice` for both business terminals | Planner |
| Arch test | Custom AST walker in `tests/architecture/`, zero new deps | Planner / Hex-Arch |
| Stripe API | PaymentIntent (idempotent-by-ID) + pre-flight status check | Integration-Eng |
| Idempotency in slice 1 | Deferred; mitigated via PI-reuse + pre-flight + no internal adapter retry. Explicit `idempotency_key` header lands in slice 2 with retries | PO/BA + Integration-Eng reconciliation |
| Error hierarchy | `BillingError → {BillingDomainError, GatewayError}`; `GatewayUnavailableError` in `ports/exceptions.py` | Backend-Arch |
| Logging split | Adapter logs Stripe detail (stripe_request_id, decline_code, payment_intent_id); use case logs business outcome only; centralized `RedactingFilter` | Observ |
| Feature flag | None (greenfield slice) | Orchestrator |
| Change class | C (new domain + port + adapter, single PR) | PO |

## Conflicts resolved

1. **backend-arch marked idempotency_key BLOCKING** vs **PO/BA deferred it.** Resolved via integration-eng's PaymentIntent-reuse + pre-flight approach; port signature stays minimal, effective idempotency achieved without explicit key. Recorded as explicit slice-2 follow-up.
2. **compliance flagged 3 BLOCKING** (log isolation, idempotency, secret mgmt). Resolved:
   - Log isolation → observ layer split + centralized RedactingFilter.
   - Idempotency → same mitigation as #1.
   - Secret mgmt → security env-var-only contract with fail-fast.
3. **All security/observ BLOCKING findings** reclassified as implement-phase acceptance checks (not discovery blockers). Hard gates for reviewer.

## Implement-phase must-pass checklist (handed to reviewer)

- [ ] STRIPE_API_KEY loaded from env only; adapter fails fast on missing; never in `__repr__`.
- [ ] No `str(exc)`/`repr(exc)` anywhere in logging; explicit field extraction only.
- [ ] `amount_cents: int`, bounded 1..99_999_999; reject float/bool.
- [ ] `currency` whitelist at adapter: `{usd, eur, brl}`.
- [ ] Centralized `RedactingFilter` on `billing.*` root logger; 11-field redact list enforced.
- [ ] Adapter logs `stripe_request_id`/`payment_intent_id`; use-case logs do NOT.
- [ ] Architecture AST walker: 9 deny/allow rules green; `stripe` import forbidden in domain/ports/use_cases.
- [ ] mypy --strict passes on `src/billing/domain` + `src/billing/use_cases`.
- [ ] `slots=True` on all frozen dataclasses; StrEnum for `InvoiceStatus`.
- [ ] FakePaymentGateway hand-rolled (no MagicMock).
- [ ] respx `assert_all_called=True, assert_all_mocked=True` in adapter tests.
- [ ] Test-first commit history for every AC per TDD-Specialist cycles.

## Risks accepted for slice 1
- No circuit breaker for Stripe outages — single adapter, failure propagates as `GatewayUnavailableError`. Revisit slice 2.
- No rate-limit backoff. Revisit slice 2.
- `@runtime_checkable` omitted — Protocol conformance verified by mypy + fake tests, not isinstance checks.
- No Stripe live contract test — recorded fixtures via respx only.

## Artifacts

- Blueprint: `ai-docs/hexagonal-billing/blueprint.md`
- Trace: `ai-docs/dogfood-runs/hexagonal-billing/trace.md`
- Metadata: `ai-docs/dogfood-runs/hexagonal-billing/metadata.json`
- Scorecard: `ai-docs/dogfood-runs/hexagonal-billing/scorecard.md`
- SEP log: `ai-docs/.squad-log/2026-04-22T16-16-45-discovery-hexagonal-billing-golden.md`
- ADRs: `ai-docs/hexagonal-billing/adr/ADR-001..004.md`

## result_contract

```yaml
result_contract:
  status: completed
  scenario_id: hexagonal-billing
  skill: discovery
  execution_mode: inline
  architecture_style: hexagonal
  artifacts:
    - ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z/prompt.txt
    - ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z/trace.md
    - ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z/final.md
    - ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z/metadata.yaml
    - ai-docs/dogfood-runs/hexagonal-billing/2026-04-22T16-16-45Z/scorecard.md
    - ai-docs/.squad-log/2026-04-22T16-16-45-discovery-hexagonal-billing-golden.md
    - ai-docs/.squad-log/2026-04-22T16-26-35-implement-hexagonal-billing-impl.md
  gates:
    gate_1_product_definition: approved
    gate_2_scope_validation: approved
    gate_3_technical_tradeoffs: approved
    gate_4_architecture_direction: approved
    blueprint_confirmation: approved
    implement_review: approved
    qa: pass
    uat: approved
```
