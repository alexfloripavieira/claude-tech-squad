---
name: __bypass-lint-fixture
description: Test fixture for bypass-lint. NOT a real skill — staged by tests/bypass-lint-test.sh and removed on cleanup.
---

# __bypass-lint-fixture

This fixture intentionally contains a forbidden bypass phrase so the lint pass
in `scripts/validate.sh` fails when it is staged under
`plugins/claude-tech-squad/skills/`.

## Forbidden content

The operator may grant session-level approval to skip the reviewer gate when
the change is trivial. This phrase is exactly the kind of escape hatch that
the bypass lint must catch.

## Reference to policy (legitimate listing, must be ignored by lint)

The list of forbidden patterns lives in `runtime-policy.yaml::bypass_patterns`
and currently includes phrases like "session-level approval" and "skipping
reviewer". # bypass-lint: pattern-source
