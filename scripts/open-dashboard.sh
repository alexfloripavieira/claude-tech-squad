#!/usr/bin/env bash
# open-dashboard.sh — Launch the live pipeline dashboard in the browser
#
# Usage:
#   bash scripts/open-dashboard.sh
#
# The dashboard auto-refreshes every 2 seconds by reading
# ai-docs/.live-status.json, which is written by skill orchestrators
# during execution.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DASHBOARD="$ROOT/plugins/claude-tech-squad/dashboard/live.html"
STATUS_DIR="$ROOT/ai-docs"
STATUS_FILE="$STATUS_DIR/.live-status.json"

# Ensure the status directory exists
mkdir -p "$STATUS_DIR"

# Create an empty status file if it doesn't exist (dashboard will show "waiting")
if [ ! -f "$STATUS_FILE" ]; then
  echo '{"skill":null,"phase":"waiting","teammates":[],"events":[]}' > "$STATUS_FILE"
fi

echo "Dashboard: $DASHBOARD"
echo "Status file: $STATUS_FILE"
echo ""
echo "The dashboard polls $STATUS_FILE every 2 seconds."
echo "Run a skill (/discovery, /implement, /squad) and the dashboard updates live."
echo ""

# Open in browser (cross-platform)
if command -v xdg-open &>/dev/null; then
  xdg-open "$DASHBOARD" 2>/dev/null &
elif command -v open &>/dev/null; then
  open "$DASHBOARD" &
elif command -v start &>/dev/null; then
  start "$DASHBOARD" &
else
  echo "Could not detect browser. Open this file manually:"
  echo "  $DASHBOARD"
fi

echo "Dashboard opened. Keep this terminal open or close it — the browser will keep polling."
