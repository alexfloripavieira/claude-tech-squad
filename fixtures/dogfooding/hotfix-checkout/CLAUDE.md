# Repository Rules

## Commands

- Test: `pytest tests/test_checkout_hotfix.py`
- Lint: `ruff check .`
- Build: `python -m compileall src`

## Hotfix Rules

- Reproduce the failure first
- Patch minimally
- Verify staging before production
- Keep rollback notes updated in deploy docs

## Delivery Notes

- Diagnosis gate must be explicit
- Root cause must be delegated through a valid plugin subagent
- Do not reference external agents outside the plugin namespace
