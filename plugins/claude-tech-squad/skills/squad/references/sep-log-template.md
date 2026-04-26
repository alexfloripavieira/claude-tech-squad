# SEP Log Template (squad)

## Generation

```bash
# Get cost summary
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli cost --run-id {{feature_slug}} --policy ${CLAUDE_PLUGIN_ROOT}/runtime-policy.yaml --state-dir .squad-state

# Generate SEP log from collected state
python3 ${CLAUDE_PLUGIN_ROOT}/bin/squad-cli sep-log --run-id {{feature_slug}} --output-dir ai-docs/.squad-log --state-dir .squad-state
```

The `cost` command returns `tokens_in`, `tokens_out`, `estimated_cost_usd`, `budget_percent`, and `per_teammate` breakdown. Emit:

```
[Run Summary] /squad | teammates: {{N}} | tokens: {{total_input}}K in / {{total_output}}K out | est. cost: ~${{usd}} | duration: {{elapsed}}
```

The `sep-log` command generates the complete SEP log file with YAML frontmatter from the state collected during the run (all teammate data, checkpoints, health signals, fallbacks, doom loops).

If `squad-cli` is not available: sum tokens manually across all teammates, estimate cost at input x $15/M + output x $75/M, and write the SEP log manually to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-squad-{{run_id}}.md` with full YAML frontmatter. When writing manually, substitute every `{{...}}` placeholder with the captured value — including `{{team_cleanup_status}}` from the Team Cleanup section (use `success` or `failed: <reason>`; never leave the literal placeholder).

## Required frontmatter fields (squad)

```yaml
---
run_id: {{run_id}}
skill: squad
timestamp: {{ISO8601}}
last_updated_at: {{ISO8601}}       # required — refresh on every edit
final_status: completed | in_flight | aborted
execution_mode: teammates
architecture_style: {{style}}
checkpoints: [preflight-passed, discovery-complete, implement-complete, quality-complete, release-prepared]
teammates_spawned: {{N}}
fallbacks_invoked: []
retry_count: {{N}}
tokens_input: {{actual_or_null}}   # required — actual measurement or null; 0 placeholder forbidden
tokens_output: {{actual_or_null}}  # required — actual measurement or null; 0 placeholder forbidden
estimated_cost_usd: {{usd}}
total_duration_ms: {{ms}}
escape_hatch_used: false
skipped_phases: []
team_cleanup_status: {{team_cleanup_status}}
---
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

## Final Output Template

```
## Squad Complete

### Agent Execution Log
- Team: squad
- Phase: discovery
  - Teammate: pm | Status: completed
  - Teammate: business-analyst | Status: completed
  - Teammate: po | Status: completed (Gate 2 passed)
  - Teammate: planner | Status: completed (Gate 3 passed)
  - Teammate: architect | Status: completed
  - Teammate: techlead | Status: completed (Gate 4 passed)
  - Batch: specialist-bench | Teammates: [...] | Status: completed
  - Batch: quality-baseline | Teammates: [...] | Status: completed
  - Teammate: design-principles | Status: completed
  - Teammate: test-planner | Status: completed
  - Teammate: tdd-specialist | Status: completed (Gate 5 passed)
- Phase: implementation
  - Teammate: tdd-impl | Status: failing tests written
  - Batch: implementation | Teammates: [...] | Status: completed
  - Teammate: reviewer | Status: APPROVED
  - Teammate: qa | Status: PASS
  - Teammate: techlead-audit | Status: CONFORMANT
  - Batch: quality-bench | Teammates: [..., code-quality] | Status: completed
  - Teammate: docs-writer | Status: completed
  - Teammate: jira-confluence | Status: completed
  - Teammate: pm-uat | Status: APPROVED (Gate 6 passed)
- Phase: release
  - Teammate: release | Status: completed
  - Teammate: sre | Status: GO

### Product
- User story: [...]
- Acceptance criteria: [...]
- Release slice: [...]

### Architecture
- Overall design: [...]
- Tech lead plan: completed
- Specialist notes: [summary]
- Design guardrails: completed
- Quality baselines: completed
- Test plan: completed
- TDD delivery plan: completed

### Delivery
- Workstreams executed: [...]
- Delivery mode: TDD-first / exception declared
- Review: APPROVED
- QA: PASS
- Specialist reviews: [summary]
- Docs: updated
- Jira / Confluence: updated
- UAT: APPROVED

### Release
- Release plan: completed
- SRE sign-off: GO
- Breaking changes: [...]
- Rollback plan: defined

### Stack Validation
- Docs checked via context7 for: [...]
```
