# `/squad` — References

Supplementary documentation for the `/squad` end-to-end orchestrator. Core workflow lives in `../SKILL.md`. The references here are shared with `/implement` and `/discovery` — see the linked files instead of duplicating.

| Topic                       | Source of truth                                              |
|-----------------------------|--------------------------------------------------------------|
| ARC schema                  | `../../implement/references/arc-schema.md`                   |
| Gate catalog (impl phase)   | `../../implement/references/gates-catalog.md`                |
| Discovery gates             | `../../discovery/references/gates-catalog.md`                |
| Runtime resilience          | `../../implement/references/runtime-resilience.md`           |
| Runtime policy (canonical)  | `plugins/claude-tech-squad/runtime-policy.yaml`              |

`/squad` is a composition of `/discovery` + `/implement` + release prep, so its reference surface is intentionally derived from those skills.
