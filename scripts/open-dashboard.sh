#!/usr/bin/env bash
# open-dashboard.sh — Launch the live pipeline dashboard in the browser
#
# Usage (run from your project directory):
#   bash scripts/open-dashboard.sh
#   # or if using the installed plugin:
#   bash ~/.claude/plugins/cache/*/claude-tech-squad/*/scripts/open-dashboard.sh
#
# Starts a lightweight Python HTTP server so the dashboard can read
# .live-status.json without CORS issues. The server runs on localhost:3742.

set -euo pipefail

PORT="${DASHBOARD_PORT:-3742}"

# Find the dashboard HTML — check multiple locations
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Option 1: running from the plugin source repo
if [ -f "$SCRIPT_DIR/../plugins/claude-tech-squad/dashboard/live.html" ]; then
  DASHBOARD_DIR="$SCRIPT_DIR/../plugins/claude-tech-squad/dashboard"
# Option 2: running from an installed plugin cache
elif [ -f "$SCRIPT_DIR/../dashboard/live.html" ]; then
  DASHBOARD_DIR="$SCRIPT_DIR/../dashboard"
else
  # Search the plugin cache
  DASHBOARD_DIR=$(find ~/.claude/plugins/cache -path "*/claude-tech-squad/*/dashboard" -type d 2>/dev/null | head -1)
  if [ -z "$DASHBOARD_DIR" ] || [ ! -f "$DASHBOARD_DIR/live.html" ]; then
    echo "Error: Could not find dashboard/live.html"
    echo "Make sure the plugin is installed: claude plugin list"
    exit 1
  fi
fi

# Ensure the status directory exists in the current project
PROJECT_DIR="$(pwd)"
mkdir -p "$PROJECT_DIR/ai-docs"

# Create an empty status file if it doesn't exist
STATUS_FILE="$PROJECT_DIR/ai-docs/.live-status.json"
if [ ! -f "$STATUS_FILE" ]; then
  echo '{"skill":null,"phase":"waiting","teammates":[],"events":[]}' > "$STATUS_FILE"
fi

# Copy dashboard to the project's ai-docs so the server can serve both
SERVE_DIR="$PROJECT_DIR/ai-docs"
cp "$DASHBOARD_DIR/live.html" "$SERVE_DIR/dashboard.html"

# Create a wrapper HTML that reads .live-status.json from the same directory
# (no CORS issues because both files are served from the same origin)
python3 -c "
import re
html = open('$DASHBOARD_DIR/live.html').read()
# Replace the relative path to status file with same-directory path
html = html.replace('../../../ai-docs/.live-status.json', '.live-status.json')
open('$SERVE_DIR/dashboard.html', 'w').write(html)
"

echo "Dashboard: http://localhost:$PORT/dashboard.html"
echo "Status file: $STATUS_FILE"
echo ""
echo "The dashboard polls .live-status.json every 2 seconds."
echo "Run a skill (/discovery, /implement, /squad) and the dashboard updates live."
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Open in browser
URL="http://localhost:$PORT/dashboard.html"
if command -v xdg-open &>/dev/null; then
  xdg-open "$URL" 2>/dev/null &
elif command -v open &>/dev/null; then
  open "$URL" &
elif command -v start &>/dev/null; then
  start "$URL" &
else
  echo "Open this URL in your browser: $URL"
fi

# Start HTTP server serving from ai-docs/
cd "$SERVE_DIR"
python3 -m http.server "$PORT" --bind 127.0.0.1 2>/dev/null
