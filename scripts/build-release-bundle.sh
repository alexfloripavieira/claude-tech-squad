#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW_VERSION="${1:-}"
VERSION="${RAW_VERSION#v}"
DIST_DIR="${DIST_DIR:-$ROOT/dist}"

if [ -z "$VERSION" ]; then
  echo "Usage: $0 <version|tag>  (e.g. $0 5.25.0 or $0 v5.25.0)"
  exit 1
fi

bash "$ROOT/scripts/verify-release.sh" "$VERSION" >/dev/null

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

PACKAGE_ROOT="$STAGING_DIR/claude-tech-squad-$VERSION"
mkdir -p "$PACKAGE_ROOT"
mkdir -p "$DIST_DIR"

cp "$ROOT/README.md" "$PACKAGE_ROOT/"
cp "$ROOT/LICENSE" "$PACKAGE_ROOT/"
cp "$ROOT/CHANGELOG.md" "$PACKAGE_ROOT/"
cp -r "$ROOT/docs" "$PACKAGE_ROOT/docs"
cp -r "$ROOT/examples" "$PACKAGE_ROOT/examples"
cp -r "$ROOT/.claude-plugin" "$PACKAGE_ROOT/.claude-plugin"
cp -r "$ROOT/plugins" "$PACKAGE_ROOT/plugins"

ARCHIVE_PATH="$DIST_DIR/claude-tech-squad-$VERSION.tar.gz"
CHECKSUM_PATH="$DIST_DIR/claude-tech-squad-$VERSION.sha256"

tar -C "$STAGING_DIR" -czf "$ARCHIVE_PATH" "claude-tech-squad-$VERSION"
sha256sum "$ARCHIVE_PATH" > "$CHECKSUM_PATH"

echo "Archive: $ARCHIVE_PATH"
echo "Checksum: $CHECKSUM_PATH"
