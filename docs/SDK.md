# Claude Tech Squad SDK

The SDK is a lightweight Python facade over deterministic helper contracts. It does not launch Claude agents and does not call external Jira, Linear, GitHub, or Confluence APIs by itself.

Use it when another script needs the same structured outputs as `squad-cli`.

Public API version: `1.0`.

## Import

```bash
PYTHONPATH=plugins/claude-tech-squad/bin python3 your-script.py
```

```python
from squad_cli.sdk import create_client

client = create_client(
    project_root=".",
    plugin_root="plugins/claude-tech-squad",
)
```

All public result models expose:

```python
result.to_dict()
result.to_json()
```

The JSON output is deterministic (`sort_keys=True`) for CI and automation consumers.

## Methods

### `onboarding_plan()`

Returns the same contract as:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli onboarding-plan --project-root .
```

### `dashboard_report(limit=30)`

Reads SEP logs from `ai-docs/.squad-log/` and returns the same `DashboardReport` model used by `/dashboard`.

### `ticket_plan(raw, ticket_json=None, text_file=None)`

Normalizes Jira, Linear, GitHub Issue, JQL, or pasted ticket content and recommends the skill to run. `ticket_json` can be a Jira, Linear, GitHub, or already-normalized object captured by an external MCP/API client.

```python
plan = client.ticket_plan("PROJ-123")
print(plan.recommended_skill)
print(plan.launch_context)
```

### `ticket_plan_from_context(context)`

Builds a plan from an already-normalized `TicketContext` or dictionary. Use this from external adapters that already fetched ticket data.

```python
plan = client.ticket_plan_from_context({
    "source": "github",
    "ticket_id": "owner/repo#42",
    "title": "Fix checkout error",
    "labels": ["bug"],
    "priority": "High",
})
```

## Errors

Catch SDK-specific errors instead of parser or filesystem internals:

```python
from squad_cli.sdk import CatalogError, ReportParseError, TicketSourceError
```

- `CatalogError` covers onboarding catalog failures.
- `ReportParseError` covers dashboard report parsing.
- `TicketSourceError` covers ticket normalization failures.

## Examples

Executable examples live in `examples/`:

```bash
PYTHONPATH=plugins/claude-tech-squad/bin python3 examples/sdk_ticket_plan.py
PYTHONPATH=plugins/claude-tech-squad/bin python3 examples/sdk_dashboard_report.py
PYTHONPATH=plugins/claude-tech-squad/bin python3 examples/sdk_onboarding_plan.py
```

For external integrations, fetch the ticket with the vendor API or MCP tool first, then pass the captured JSON or normalized fields to the SDK.
