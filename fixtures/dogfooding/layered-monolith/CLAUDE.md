# Repository Rules

## Commands

- Test: `npm test`
- Lint: `npm run lint`
- Build: `npm run build`

## Architecture

Preserve the current layered/module pattern.
Do not introduce Ports & Adapters unless the user explicitly requests Hexagonal Architecture.

## Delivery Notes

- Keep audit-log concerns inside the existing module
- Prefer a small backend bench
- Show preflight and execution lines in orchestration output
