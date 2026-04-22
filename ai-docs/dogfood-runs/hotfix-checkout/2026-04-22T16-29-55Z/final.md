# Hotfix Final Report — checkout-coupon-null-guard

**Run ID:** 2026-04-22T16-29-55Z
**Skill:** /claude-tech-squad:hotfix
**Fixture:** fixtures/dogfooding/hotfix-checkout
**Execution mode:** inline (no teammate runtime / no tmux)
**Operator:** alex.vieira@a1.com.vc

## Incident

- **Symptom:** HTTP 500 on checkout submit in staging after latest release
- **Scope:** `checkout.service.total_after_discount`
- **Trigger:** release introduced optional coupon path; upstream passes `discount_cents=None` when no coupon is applied

## Root Cause

Prior revision of `total_after_discount` performed `subtotal_cents - discount_cents` without a null guard. When the new optional-coupon path propagates `discount_cents=None` through the call chain, arithmetic raises `TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'`, surfacing as HTTP 500 at the checkout API boundary.

## Minimal Patch

`src/checkout/service.py:1-2` — `return subtotal_cents - (discount_cents or 0)`
`tests/test_checkout_hotfix.py` — regression test asserting `total_after_discount(5000, None) == 5000`

Verified diff stays within one file of production code + one test. No refactor, no API change, no new dependency.

## Verification

```
$ PYTHONPATH=src pytest tests/ -q
.                                                                        [100%]
1 passed in 0.00s
```

Lint: `ruff check .` → clean.
Build: `python -m compileall src` → OK.

## Gates

| Gate | Result | Notes |
|---|---|---|
| diagnosis-confirm | approved | root cause + minimal patch path confirmed before any code change |
| deploy-checklist | approved | staging-first mandated; rollback = `git revert <sha>` |
| postmortem-prompt | defer-with-ticket | /incident-postmortem queued with parent_run_id |

## Teammates (inline)

| Teammate | Verdict | Confidence |
|---|---|---|
| techlead | root-cause identified, minimal patch proposed | high |
| python-developer | patch applied, regression test green | high |
| reviewer | APPROVED | — |
| security-reviewer | CLEAR | — |
| work-item-mapper | classified as `bug` (sev-2 production defect) | — |

## Deploy Checklist Status

- [x] PR draft prepared (branch `hotfix/checkout-coupon-null-guard`)
- [ ] PR approved by reviewer (operator action)
- [ ] Staging deploy + verification (operator action)
- [ ] Production deploy (operator action, blocked on staging green)
- [ ] 15-min post-deploy monitoring (operator action)
- [ ] Post-mortem scheduled (`/incident-postmortem`)

## Artifacts

- trace.md — structured execution trace (this run)
- metadata.yaml — machine-readable run summary
- scorecard.md — scenario contract compliance
- SEP log: `ai-docs/.squad-log/2026-04-22T16-29-55Z-hotfix-checkout-coupon-null-guard.md`

## result_contract

```yaml
result_contract:
  status: completed
  scenario_id: hotfix-checkout
  skill: hotfix
  execution_mode: inline
  artifacts:
    - ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z/prompt.txt
    - ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z/trace.md
    - ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z/final.md
    - ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z/metadata.yaml
    - ai-docs/dogfood-runs/hotfix-checkout/2026-04-22T16-29-55Z/scorecard.md
    - ai-docs/.squad-log/2026-04-22T16-29-55Z-hotfix-checkout-coupon-null-guard.md
  gates:
    diagnosis_confirm: approved
    deploy_checklist: approved
    postmortem_prompt: defer-with-ticket
  verification:
    tests: pass
    lint: clean
    security: clear
```
