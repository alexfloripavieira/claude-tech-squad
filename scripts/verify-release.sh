#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW_VERSION="${1:-}"
VERSION="${RAW_VERSION#v}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version|tag>  (e.g. $0 5.25.0 or $0 v5.25.0)"
  exit 1
fi

if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Version must be in semver format: MAJOR.MINOR.PATCH"
  exit 1
fi

MARKETPLACE_VERSION=$(python3 -c "import json; d=json.load(open('$ROOT/.claude-plugin/marketplace.json')); print(d['plugins'][0]['version'])")
PLUGIN_VERSION=$(python3 -c "import json; d=json.load(open('$ROOT/plugins/claude-tech-squad/.claude-plugin/plugin.json')); print(d['version'])")
MANUAL_VERSION=$(python3 -c "import re; s=open('$ROOT/docs/MANUAL.md').read(); m=re.search(r'\*\*Version:\*\*\s*([0-9.]+)', s); print(m.group(1) if m else '')")

[ "$MARKETPLACE_VERSION" = "$VERSION" ] || { echo "marketplace.json version ($MARKETPLACE_VERSION) does not match $VERSION"; exit 1; }
[ "$PLUGIN_VERSION" = "$VERSION" ] || { echo "plugin.json version ($PLUGIN_VERSION) does not match $VERSION"; exit 1; }
[ "$MANUAL_VERSION" = "$VERSION" ] || { echo "MANUAL.md version ($MANUAL_VERSION) does not match $VERSION"; exit 1; }

if ! grep -q "## \[$VERSION\]" "$ROOT/CHANGELOG.md"; then
  echo "CHANGELOG.md is missing an entry for [$VERSION]"
  exit 1
fi

NOTES_FILE="$(mktemp)"
trap 'rm -f "$NOTES_FILE"' EXIT
awk "/^\#\# \[$VERSION\]/{found=1; next} found && /^\#\# \[/{exit} found{print}" "$ROOT/CHANGELOG.md" > "$NOTES_FILE"

if ! grep -q '[^[:space:]]' "$NOTES_FILE"; then
  echo "CHANGELOG.md entry for [$VERSION] is empty"
  exit 1
fi

echo "claude-tech-squad release metadata passed ($VERSION)"
