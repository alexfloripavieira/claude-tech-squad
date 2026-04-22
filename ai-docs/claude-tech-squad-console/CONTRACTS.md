# Claude Tech Squad Console Contracts

Status: frozen for Console MVP v1.

These contracts define the HTTP/API and fixture boundary for the local Console. The source of truth remains the plugin SDK and CLI:

- `TicketContext` and `TicketPlan`: `plugins/claude-tech-squad/bin/squad_cli/ticket.py`
- `DashboardReport` and `SepRun`: `plugins/claude-tech-squad/bin/squad_cli/dashboard.py`
- SDK facade version: `plugins/claude-tech-squad/bin/squad_cli/sdk.py`

The frontend and API must consume these shapes instead of reimplementing skill selection, complexity, cost, or SEP parsing rules.

## Compatibility Policy

The Console uses additive compatibility for SDK/API contract version `1.x`.

- Required fields in the v1 schemas cannot be removed or renamed without a major contract version bump.
- New optional fields may be added in minor releases.
- Enum expansion is allowed when consumers treat unknown values as displayable strings.
- Numeric units are stable: costs are USD floats, token counts are integer tokens, and rates are percentages from 0 to 100.
- Timestamps are ISO 8601 strings when available. Empty strings are allowed for legacy SEP logs that do not expose a timestamp.
- Raw SEP Markdown remains the audit artifact. Indexed/API records must keep a filesystem path back to the original log.
- External ticket payloads are untrusted input. Adapters normalize them into `TicketContext`; consumers should not depend on source-specific raw payload fields.

Breaking changes require:

1. A new schema version directory or filename.
2. A migration note in this file.
3. Smoke validation that covers old and new fixtures.
4. SDK/API documentation updates before frontend changes depend on the new shape.

## TicketContext

Schema: `schemas/ticket-context.schema.json`

Normalized input context for a single ticket. It is accepted from pasted text, normalized JSON, or adapters for GitHub, Jira, and Linear.

Required fields:

- `source`: ticket source slug such as `pasted`, `github`, `jira`, `jira-jql`, or `linear`.
- `ticket_id`: stable ticket identifier or `pasted`.
- `title`
- `description`
- `issue_type`
- `priority`
- `acceptance_criteria`
- `subtasks`
- `labels`
- `linked_issues`
- `comments`

List fields contain strings after adapter normalization.

## TicketSourceClient

Source: `plugins/claude-tech-squad/bin/squad_cli/ticket_sources/base.py`

External integrations must implement this interface instead of letting the Console frontend call vendor APIs directly:

- `source`: stable source slug such as `github`, `jira`, or `linear`.
- `fetch_ticket(identifier)`: returns the raw source payload and may raise `TicketSourceError`.
- `to_context(payload)`: normalizes the raw payload to `TicketContext`.

When `fetch_ticket` fails because credentials, tools, or connectivity are unavailable, API code should call `fetch_context_with_fallback(...)`. The fallback result preserves the error text, marks `fallback_used`, and continues with a pasted or captured JSON payload normalized through the same `TicketContext` contract.

## TicketPlan

Schema: `schemas/ticket-plan.schema.json`

Planning result returned by `squad_cli.ticket.build_ticket_plan` and `SquadSDK.ticket_plan*`.

Required fields:

- `source`
- `ticket_id`
- `issue_type`
- `priority`
- `complexity_tier`: `small`, `medium`, or `large`.
- `recommended_skill`: skill slug selected by SDK/CLI rules.
- `estimated_agents`
- `estimated_tokens`
- `estimated_cost_usd`
- `alternatives`: list of `{ "skill": "...", "when": "..." }`.
- `extracted_context`: normalized `TicketContext` payload.
- `launch_context`: Markdown context intended for Claude Code launch.

The Console may display these values but must not recompute them in the frontend.

## DashboardReport

Schema: `schemas/dashboard-report.schema.json`

Aggregated dashboard result returned by `squad_cli.dashboard.build_dashboard_report`.

Required fields:

- `generated_at`
- `logs_analyzed`
- `skills_covered`
- `overall_success_rate`
- `skill_summaries`
- `pending_hotfixes`
- `recent_runs`
- `source_log_dir`

`skill_summaries` entries expose per-skill run count, success rate, blocked gates, fallback counts, and flags.

## SepRun

Schema: `schemas/sep-run.schema.json`

Indexed representation of one SEP Markdown log. It is derived from frontmatter plus output digest text.

Required fields:

- `path`: path to original Markdown log.
- `run_id`
- `skill`
- `timestamp`
- `final_status`
- `checkpoints`
- `fallbacks_invoked`
- `gates_blocked`
- `findings_critical`
- `findings_high`
- `postmortem_recommended`
- `parent_run_id`
- `summary`

`final_status` is a string to preserve compatibility with existing logs, including `completed`, `failed`, `blocked`, `aborted`, and legacy custom values.

## RunEvent

Schema: `schemas/run-event.schema.json`

Structured audit/observability event for Console actions.

Required fields:

- `event_type`
- `payload`
- `created_at`

Optional correlation fields:

- `run_id`
- `ticket_id`
- `ticket_source`

Initial event types:

- `ticket.plan.created`
- `ticket.plan.failed`
- `ticket.fetch.started`
- `ticket.fetch.failed`
- `run.indexed`
- `run.completed`
- `run.failed`
- `fallback.invoked`
- `external_update.previewed`
- `external_update.confirmed`
- `external_update.failed`
