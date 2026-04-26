# `/implement` — References

Supplementary documentation for the `/implement` orchestrator skill. The core workflow and contracts live in `../SKILL.md`; this directory contains deep-dive references that would bloat the SKILL.md if inlined.

| File                       | Purpose                                                              |
|----------------------------|----------------------------------------------------------------------|
| `arc-schema.md`            | Canonical Agent Result Contract schema and failure modes             |
| `gates-catalog.md`         | Every gate in the pipeline, what it consumes, auto-advance rules     |
| `runtime-resilience.md`    | Retry budgets, fallback matrix, doom-loop heuristics, cost guardrails|

These references are read by the orchestrator on demand — they are not injected into teammate prompts. Teammate prompt templates remain in `SKILL.md` so that the runtime can fill placeholders deterministically.
