#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 -m json.tool "$ROOT/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "$ROOT/plugins/claude-tech-squad/.claude-plugin/plugin.json" >/dev/null

test -f "$ROOT/LICENSE"
test -f "$ROOT/docs/USAGE-BOUNDARIES.md"
test -f "$ROOT/docs/RELEASING.md"
test -f "$ROOT/plugins/claude-tech-squad/skills/discovery/SKILL.md"
test -f "$ROOT/plugins/claude-tech-squad/skills/implement/SKILL.md"
test -f "$ROOT/plugins/claude-tech-squad/skills/squad/SKILL.md"

if rg -n "\bA1\b|Fifi|Wooba|Cangooroo|Compozy|Botpress" \
  "$ROOT/README.md" \
  "$ROOT/docs" \
  "$ROOT/plugins/claude-tech-squad" >/dev/null; then
  echo "Found project-specific residue in plugin repository."
  exit 1
fi

echo "claude-tech-squad validation passed"
