#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURES_DIR="$ROOT/fixtures/dogfooding"
MANIFEST="$FIXTURES_DIR/scenarios.json"

fail() {
  echo "Dogfood check failed: $1"
  exit 1
}

require_file() {
  [ -f "$1" ] || fail "missing file: ${1#$ROOT/}"
}

require_dir() {
  [ -d "$1" ] || fail "missing directory: ${1#$ROOT/}"
}

python3 -m json.tool "$MANIFEST" >/dev/null

SCENARIO_COUNT=$(python3 -c "import json; d=json.load(open('$MANIFEST')); print(len(d['scenarios']))")
[ "$SCENARIO_COUNT" = "3" ] || fail "expected 3 scenarios in manifest, found $SCENARIO_COUNT"

if [ "${1:-}" = "--print-prompts" ]; then
  python3 -c "import json; d=json.load(open('$MANIFEST')); [print(f\"[{s['id']}]\\n{s['prompt']}\\n\") for s in d['scenarios']]"
  exit 0
fi

LAYERED="$FIXTURES_DIR/layered-monolith"
require_dir "$LAYERED/src/modules/audit-log/api"
require_dir "$LAYERED/src/modules/audit-log/service"
require_dir "$LAYERED/src/modules/audit-log/repo"
require_file "$LAYERED/README.md"
require_file "$LAYERED/CLAUDE.md"
require_file "$LAYERED/package.json"
require_file "$LAYERED/test/auditLogFilters.test.ts"
rg -q '"test"' "$LAYERED/package.json" || fail "layered fixture missing test script"
rg -q '"lint"' "$LAYERED/package.json" || fail "layered fixture missing lint script"
rg -q '"build"' "$LAYERED/package.json" || fail "layered fixture missing build script"
rg -q 'Preserve the current layered/module pattern' "$LAYERED/CLAUDE.md" || fail "layered fixture missing layered architecture rule"
if find "$LAYERED/src" -type d \( -name ports -o -name adapters \) | grep -q .; then
  fail "layered fixture unexpectedly contains hexagonal directories"
fi

HEXAGONAL="$FIXTURES_DIR/hexagonal-billing"
require_dir "$HEXAGONAL/src/billing/domain"
require_dir "$HEXAGONAL/src/billing/ports"
require_dir "$HEXAGONAL/src/billing/adapters"
require_dir "$HEXAGONAL/tests"
require_file "$HEXAGONAL/README.md"
require_file "$HEXAGONAL/CLAUDE.md"
require_file "$HEXAGONAL/pyproject.toml"
require_file "$HEXAGONAL/tests/test_capture_invoice.py"
rg -q '\[tool\.pytest\.ini_options\]' "$HEXAGONAL/pyproject.toml" || fail "hexagonal fixture missing pytest config"
rg -q '\[tool\.ruff\]' "$HEXAGONAL/pyproject.toml" || fail "hexagonal fixture missing ruff config"
rg -q '\[tool\.mypy\]' "$HEXAGONAL/pyproject.toml" || fail "hexagonal fixture missing mypy config"
rg -q 'explicit Hexagonal Architecture' "$HEXAGONAL/CLAUDE.md" || fail "hexagonal fixture missing explicit hexagonal rule"

HOTFIX="$FIXTURES_DIR/hotfix-checkout"
require_dir "$HOTFIX/src/checkout"
require_dir "$HOTFIX/tests"
require_dir "$HOTFIX/deploy"
require_dir "$HOTFIX/docs"
require_file "$HOTFIX/README.md"
require_file "$HOTFIX/CLAUDE.md"
require_file "$HOTFIX/docs/incident-brief.md"
require_file "$HOTFIX/deploy/last-release.md"
require_file "$HOTFIX/tests/test_checkout_hotfix.py"
rg -q 'Verify staging before production' "$HOTFIX/CLAUDE.md" || fail "hotfix fixture missing staging rule"
rg -q 'valid plugin subagent' "$HOTFIX/CLAUDE.md" || fail "hotfix fixture missing plugin namespace rule"
if rg -n 'code-debugger' "$HOTFIX" >/dev/null 2>&1; then
  fail "hotfix fixture contains stale code-debugger reference"
fi

echo "claude-tech-squad dogfood fixtures passed"
