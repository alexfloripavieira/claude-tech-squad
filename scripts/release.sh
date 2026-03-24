#!/usr/bin/env bash
# Usage: ./scripts/release.sh 5.2.0
# Bumps versions in marketplace.json and plugin.json, commits, tags, and pushes.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version>  (e.g. $0 5.2.0)"
  exit 1
fi

# Validate format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "Version must be in semver format: MAJOR.MINOR.PATCH"
  exit 1
fi

echo "Releasing v$VERSION..."

# Validate plugin before touching anything
bash "$ROOT/scripts/validate.sh"

# Bump marketplace.json
python3 - <<EOF
import json, pathlib
path = pathlib.Path("$ROOT/.claude-plugin/marketplace.json")
data = json.loads(path.read_text())
data["plugins"][0]["version"] = "$VERSION"
path.write_text(json.dumps(data, indent=2) + "\n")
EOF

# Bump plugin.json
python3 - <<EOF
import json, pathlib
path = pathlib.Path("$ROOT/plugins/claude-tech-squad/.claude-plugin/plugin.json")
data = json.loads(path.read_text())
data["version"] = "$VERSION"
path.write_text(json.dumps(data, indent=2) + "\n")
EOF

echo "Versions bumped. Checking CHANGELOG..."

# Check CHANGELOG has an entry for this version
if ! grep -q "## \[$VERSION\]" "$ROOT/CHANGELOG.md"; then
  echo "CHANGELOG.md is missing an entry for [$VERSION]. Add it before releasing."
  exit 1
fi

# Validate again after bumps
bash "$ROOT/scripts/validate.sh"

# Commit and tag
cd "$ROOT"
git add .claude-plugin/marketplace.json plugins/claude-tech-squad/.claude-plugin/plugin.json
git commit -m "chore: release v$VERSION"
git tag "v$VERSION"
git push origin main
git push origin "v$VERSION"

echo ""
echo "Released v$VERSION."
echo "GitHub Actions will create the release automatically."
