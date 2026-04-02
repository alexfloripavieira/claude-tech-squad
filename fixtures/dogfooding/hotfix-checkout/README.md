# Hotfix Checkout Fixture

This fixture simulates a production checkout service that just regressed after a deploy.

## Incident

- Symptom: HTTP 500 on checkout submit
- Trigger: latest release added an optional coupon path
- Goal: diagnose root cause, patch minimally, and keep staging-before-prod discipline

The expected workflow is `/claude-tech-squad:hotfix`.
