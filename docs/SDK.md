# Claude Tech Squad SDK

The SDK is a lightweight Python facade over deterministic helper contracts. It does not launch Claude agents and does not call external Jira, Linear, GitHub, or Confluence APIs by itself.

Use it when another script needs the same structured outputs as `squad-cli`.

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

## Methods

### `onboarding_plan()`

Returns the same contract as:

```bash
python3 plugins/claude-tech-squad/bin/squad-cli onboarding-plan --project-root .
```

### `dashboard_report(limit=30)`

Reads SEP logs from `ai-docs/.squad-log/` and returns the same `DashboardReport` model used by `/dashboard`.

### `ticket_plan(raw, ticket_json=None, text_file=None)`

Normalizes Jira, Linear, GitHub Issue, JQL, or pasted ticket content and recommends the skill to run.

```python
plan = client.ticket_plan("PROJ-123")
print(plan.recommended_skill)
print(plan.launch_context)
```

For external integrations, fetch the ticket with the vendor API or MCP tool first, save or pass the normalized fields, then call `ticket_plan`.
