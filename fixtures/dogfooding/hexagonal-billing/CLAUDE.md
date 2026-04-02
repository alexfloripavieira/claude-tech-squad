# Repository Rules

## Commands

- Test: `pytest`
- Lint: `ruff check .`
- Build: `python -m build`

## Architecture

This repository uses explicit Hexagonal Architecture for new billing features.
Keep domain entities and use cases isolated from framework code.
Outbound integrations must go through ports and adapters.

## Delivery Notes

- TDD is required
- Reviewer and TechLead must audit against the explicit hexagonal choice
- Visible execution lines are mandatory in dogfooding runs
