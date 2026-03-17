# claude-tech-squad

Generic Claude Code plugin for end-to-end software delivery with a complete specialist squad.

## Use This Plugin When

- the task crosses product, engineering, QA, docs, and release boundaries
- you want one orchestrated workflow rather than hand-assembling agents
- you need specialists selected according to the actual repository and feature

## Do Not Use This Plugin For

- machine bootstrap or global defaults
- storing reusable templates and generic rules
- product-specific artifacts outside the repository being worked on

For those, use `claude-config`.
For install scopes and prompt examples, see [GETTING-STARTED.md](../../docs/GETTING-STARTED.md).

## Commands

- `/claude-tech-squad:discovery`
- `/claude-tech-squad:implement`
- `/claude-tech-squad:squad`

## Principles

- repository-aware first
- specialist bench, not specialist noise
- validate decisions against current docs and real stack evidence
- finish through review, docs, and release impact, not just implementation
