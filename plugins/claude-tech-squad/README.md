# claude-tech-squad

Generic Claude Code plugin for end-to-end software delivery with a complete specialist squad.

## Use This Plugin When

- the task crosses product, engineering, QA, docs, and release boundaries
- you want one orchestrated workflow rather than hand-assembling agents
- you need specialists selected according to the actual repository and feature
- you want TDD cycle planning separated cleanly from QA acceptance validation
- you want explicit structural guidance for SOLID, Clean Architecture, Ports and Adapters, and Hexagonal-style boundaries
- you want `/squad` to run code delivery in TDD-first mode by default

## Do Not Use This Plugin For

- machine bootstrap or global defaults
- storing reusable templates and generic rules
- product-specific artifacts outside the repository being worked on

For those, use `claude-config`.
For install scopes and prompt examples, see [GETTING-STARTED.md](../../docs/GETTING-STARTED.md).
For visible execution interpretation, see [EXECUTION-TRACE.md](../../docs/EXECUTION-TRACE.md).

## Commands

- `/claude-tech-squad:discovery`
- `/claude-tech-squad:implement`
- `/claude-tech-squad:squad`

## Principles

- repository-aware first
- specialist bench, not specialist noise
- validate decisions against current docs and real stack evidence
- use TDD cycle planning when the delivery strategy benefits from red-green-refactor execution
- apply design principles pragmatically, not dogmatically
- finish through review, docs, and release impact, not just implementation

## Visible Execution

The plugin workflows emit explicit progress lines for phase changes, agent handoffs, retries, and batch execution.

Expect output such as:

- `[Phase Start] Build`
- `[Agent Start] Backend Dev | claude-tech-squad:backend-dev | Implement backend slice`
- `[Agent Done] Backend Dev | Status: completed | Output: endpoints and tests updated`

Final outputs also include an `Agent Execution Log`.

Use [EXECUTION-TRACE.md](../../docs/EXECUTION-TRACE.md) to interpret these lines during real runs.
