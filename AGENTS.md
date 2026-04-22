# Repository Guidelines

## Project Structure & Module Organization

This repository ships the `claude-tech-squad` plugin and its delivery assets. Core plugin content lives in `plugins/claude-tech-squad/`: specialist agents in `agents/`, orchestration skills in `skills/`, runtime policy in `runtime-policy.yaml`, hooks in `hooks/`, and the Python helper CLI in `bin/squad_cli/`. Validation and release automation live in `scripts/`. Operator and architecture docs live in `docs/`. Reusable templates live in `templates/`. Dogfooding sample repos and fixture expectations live in `fixtures/dogfooding/`. Generated or captured run artifacts belong in `ai-docs/`.

## Build, Test, and Development Commands

There is no application build step; changes are validated through shell scripts.

- `bash scripts/validate.sh` — structural contract checks for agents, skills, versions, and policy files.
- `bash scripts/smoke-test.sh` — broader validation ladder, including release bundle checks.
- `bash scripts/dogfood.sh` — verifies dogfooding fixtures; add `--print-prompts` to inspect scenario prompts.
- `bash scripts/dogfood-report.sh --schema-only` — validates the golden-run report schema.
- `bash scripts/start-golden-run.sh <scenario-id> <operator>` — scaffolds a real golden run.
- `bash scripts/build-release-bundle.sh <version>` — packages a verified release tarball.

## Coding Style & Naming Conventions

Match the existing file style exactly. Use Markdown for agents, skills, and docs; keep headings stable because validation scripts grep for exact section names. Use 4-space indentation in Python and prefer type hints, as in `plugins/claude-tech-squad/bin/squad_cli/`. Write Bash with `set -euo pipefail` and small helper functions. Name new agents and skills with lowercase kebab-case slugs such as `backend-dev.md` or `skills/refactor/SKILL.md`.

## Testing Guidelines

Treat the validation ladder as the test suite. Run the four required commands from `CONTRIBUTING.md` before opening a PR. When behavior changes, update fixture expectations and, for Class C/D changes, prepare or refresh golden runs. Keep test fixtures repository-realistic; do not add placeholder files that bypass script checks.

## Commit & Pull Request Guidelines

Follow conventional commit style used in history: `feat:`, `fix:`, `docs:`, `chore:`, with optional scopes like `feat(plugin): ...`. PRs should state change class, impacted skills or agents, risk level, validation evidence, and whether golden runs were updated. Use `.github/PULL_REQUEST_TEMPLATE.md`. Do not hand-edit routine release artifacts such as `CHANGELOG.md`, `docs/MANUAL.md`, or plugin manifests unless the change specifically requires it.

## Security & Release Notes

Follow `SECURITY.md` for vulnerability handling. Never commit secrets, tokens, or customer data into docs, fixtures, or `ai-docs/`. For release work, verify version alignment with `bash scripts/verify-release.sh <version>` before packaging.
