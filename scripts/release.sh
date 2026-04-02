#!/usr/bin/env bash
# Fallback only.
# Official release flow is GitHub Actions automation that versions, tags, and publishes.
# Usage: ./scripts/release.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required for the fallback release path."
  exit 1
fi

VERSION="$(bash "$ROOT/scripts/prepare-release-metadata.sh")"
VERSION="$(printf '%s\n' "$VERSION" | tail -1 | tr -d '\r')"

if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "No releasable changes found."
  exit 0
fi

echo "Preparing fallback release v$VERSION..."

bash "$ROOT/scripts/smoke-test.sh"

cd "$ROOT"
git add .claude-plugin/marketplace.json plugins/claude-tech-squad/.claude-plugin/plugin.json docs/MANUAL.md CHANGELOG.md

if git diff --cached --quiet; then
  echo "No metadata changes to commit."
else
  git commit -m "chore: prepare release v$VERSION"
  git push origin main
fi

gh workflow run publish --ref main

echo ""
echo "Queued fallback release v$VERSION."
echo "GitHub Actions publish workflow will finish the tag and release creation."
