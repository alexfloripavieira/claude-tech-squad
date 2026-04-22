#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="$ROOT/plugins/claude-tech-squad"

export PYTHONPATH="$PLUGIN_DIR/bin"

python3 - <<'PY'
import json
from squad_cli.sdk import (
    SDK_API_VERSION,
    TicketSourceError,
    create_client,
    to_json,
)

client = create_client(
    project_root="fixtures/dogfooding/llm-rag",
    plugin_root="plugins/claude-tech-squad",
)

assert SDK_API_VERSION == "1.0"

onboarding = client.onboarding_plan()
assert onboarding.stack == "python", onboarding
assert json.loads(onboarding.to_json())["stack"] == "python"

dashboard = client.dashboard_report(limit=5)
assert "logs_analyzed" in json.loads(dashboard.to_json())

ticket = client.ticket_plan("PROJ-123")
assert ticket.source == "jira", ticket
assert json.loads(ticket.to_json())["ticket_id"] == "PROJ-123"

from_context = client.ticket_plan_from_context(ticket.extracted_context)
assert from_context.ticket_id == "PROJ-123", from_context
assert json.loads(to_json(from_context))["recommended_skill"] == ticket.recommended_skill

try:
    client.ticket_plan("PROJ-123", ticket_json="missing.json")
except TicketSourceError:
    pass
else:
    raise AssertionError("missing ticket_json should raise TicketSourceError")
PY

python3 "$ROOT/examples/sdk_ticket_plan.py" >/dev/null
python3 "$ROOT/examples/sdk_dashboard_report.py" >/dev/null
python3 "$ROOT/examples/sdk_onboarding_plan.py" >/dev/null

echo "claude-tech-squad SDK tests passed"
