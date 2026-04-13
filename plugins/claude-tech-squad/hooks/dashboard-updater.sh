#!/usr/bin/env bash
# dashboard-updater.sh — Mechanical dashboard updater
#
# PostToolUse hook that updates ai-docs/.live-status.json automatically
# whenever an Agent tool is called (teammate spawned/completed).
#
# This is MECHANICAL — it fires on every tool use, parses the result,
# and updates the JSON. The orchestrator does NOT need to "remember"
# to write the JSON. The hook does it deterministically.
#
# Installation (add to .claude/settings.json):
# {
#   "hooks": {
#     "PostToolUse": [
#       {
#         "matcher": "Agent",
#         "hooks": [{ "type": "command", "command": "bash plugins/claude-tech-squad/hooks/dashboard-updater.sh" }]
#       }
#     ]
#   }
# }

set -euo pipefail

STATUS_FILE="ai-docs/.live-status.json"
mkdir -p ai-docs

INPUT=$(cat 2>/dev/null || echo "{}")

# Extract tool info
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_name', ''))
except:
    print('')
" 2>/dev/null || echo "")

# Only process Agent tool calls
if [ "$TOOL_NAME" != "Agent" ]; then
    exit 0
fi

# Parse Agent tool input/output and update status
python3 << 'PYEOF' "$INPUT" "$STATUS_FILE"
import sys, json, os
from datetime import datetime, timezone

raw_input = sys.argv[1]
status_file = sys.argv[2]

try:
    hook_data = json.loads(raw_input)
except:
    sys.exit(0)

tool_input = hook_data.get("tool_input", {})
tool_result = hook_data.get("tool_result", "")

# Extract agent info from tool input
agent_name = tool_input.get("name", tool_input.get("description", "unknown"))
subagent_type = tool_input.get("subagent_type", "")
prompt_snippet = str(tool_input.get("prompt", ""))[:100]

# Load existing status or create new
if os.path.exists(status_file):
    try:
        with open(status_file, "r") as f:
            status = json.load(f)
    except:
        status = {}
else:
    status = {}

# Initialize structure if needed
if "teammates" not in status:
    status["teammates"] = []
if "events" not in status:
    status["events"] = []
if "skill" not in status or not status.get("skill"):
    # Infer skill from subagent_type
    status["skill"] = "squad"
if "started_at" not in status or not status.get("started_at"):
    status["started_at"] = datetime.now(timezone.utc).isoformat()

now = datetime.now(timezone.utc)
time_str = now.strftime("%H:%M:%S")

# Check if this is a new teammate spawn or an update
existing = None
for tm in status["teammates"]:
    if tm.get("name") == agent_name:
        existing = tm
        break

if tool_result and str(tool_result).strip():
    # Agent completed — update status
    if existing:
        existing["status"] = "completed"
        existing["duration_ms"] = int((now - datetime.fromisoformat(existing.get("started_at", now.isoformat()).replace("Z", "+00:00"))).total_seconds() * 1000)
        result_str = str(tool_result)
        existing["output_summary"] = result_str[:120] + "..." if len(result_str) > 120 else result_str

    status["events"].append({
        "time": time_str,
        "line": f"[Teammate Done] {agent_name} | completed"
    })
else:
    # Agent being spawned
    teammate = {
        "name": agent_name,
        "subagent_type": subagent_type,
        "status": "running",
        "started_at": now.isoformat(),
        "duration_ms": None,
        "tokens_input": None,
        "tokens_output": None,
        "output_summary": None,
        "retry_count": 0,
        "fallback_from": None,
        "doom_loop": None,
        "health_signals": None
    }

    if not existing:
        status["teammates"].append(teammate)
    else:
        existing["status"] = "running"
        existing["started_at"] = now.isoformat()

    status["events"].append({
        "time": time_str,
        "line": f"[Teammate Spawned] {agent_name} | {subagent_type}"
    })

# Update phase based on latest activity
running = [t for t in status["teammates"] if t["status"] == "running"]
completed = [t for t in status["teammates"] if t["status"] == "completed"]
status["phase"] = f"{len(completed)} done, {len(running)} running"

# Keep last 50 events
status["events"] = status["events"][-50:]

# Write atomically
tmp_file = status_file + ".tmp"
with open(tmp_file, "w") as f:
    json.dump(status, f, indent=2, default=str)
os.rename(tmp_file, status_file)
PYEOF

exit 0
