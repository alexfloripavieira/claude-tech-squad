#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/fixtures/dogfooding/scenarios.json"
RUNS_DIR="$ROOT/ai-docs/dogfood-runs"

fail() {
  echo "Golden run check failed: $1"
  exit 1
}

require_file() {
  [ -f "$1" ] || fail "missing file: ${1#$ROOT/}"
}

schema_only=0
if [ "${1:-}" = "--schema-only" ]; then
  schema_only=1
fi

python3 -m json.tool "$MANIFEST" >/dev/null

python3 - <<'PY' "$MANIFEST" || exit 1
import json
import sys

manifest = json.load(open(sys.argv[1]))
required = {
    "id",
    "workflow",
    "repo_path",
    "prompt",
    "expected_architecture_style",
    "expected_agents",
    "forbidden_default_agents",
    "required_trace_lines",
    "forbidden_strings",
    "artifact_contract",
}

for scenario in manifest["scenarios"]:
    missing = sorted(required - set(scenario))
    if missing:
        raise SystemExit(f"scenario {scenario.get('id', '<unknown>')} missing keys: {', '.join(missing)}")
PY

if [ "$schema_only" = "1" ]; then
  echo "claude-tech-squad golden run schema passed"
  exit 0
fi

[ -d "$RUNS_DIR" ] || fail "missing directory: ai-docs/dogfood-runs"

SCENARIOS=$(python3 -c "import json; d=json.load(open('$MANIFEST')); [print(s['id']) for s in d['scenarios']]")

while IFS= read -r scenario_id; do
  [ -n "$scenario_id" ] || continue
  scenario_dir="$RUNS_DIR/$scenario_id"
  [ -d "$scenario_dir" ] || fail "missing run directory for scenario: ai-docs/dogfood-runs/$scenario_id"

  latest_run="$(find "$scenario_dir" -mindepth 1 -maxdepth 1 -type d | sort | tail -1)"
  [ -n "$latest_run" ] || fail "no run folders found for scenario: $scenario_id"

  ARTIFACTS=$(python3 -c "import json; d=json.load(open('$MANIFEST')); s=next(x for x in d['scenarios'] if x['id']=='$scenario_id'); [print(a) for a in s['artifact_contract']]")
  while IFS= read -r artifact; do
    [ -n "$artifact" ] || continue
    require_file "$latest_run/$artifact"
  done <<< "$ARTIFACTS"

  require_file "$latest_run/metadata.yaml"
  require_file "$latest_run/trace.md"
  require_file "$latest_run/final.md"

  grep -q "scenario_id: $scenario_id" "$latest_run/metadata.yaml" || fail "metadata missing scenario_id for $scenario_id"
  grep -q "score: pass" "$latest_run/metadata.yaml" || fail "metadata score is not pass for $scenario_id"
  grep -q "result_contract" "$latest_run/final.md" || fail "final artifact missing result_contract evidence for $scenario_id"

  REQUIRED_TRACE_LINES=$(python3 -c "import json; d=json.load(open('$MANIFEST')); s=next(x for x in d['scenarios'] if x['id']=='$scenario_id'); [print(x) for x in s['required_trace_lines']]")
  while IFS= read -r trace_line; do
    [ -n "$trace_line" ] || continue
    grep -F -q "$trace_line" "$latest_run/trace.md" || fail "trace missing '$trace_line' for $scenario_id"
  done <<< "$REQUIRED_TRACE_LINES"

  FORBIDDEN_STRINGS=$(python3 -c "import json; d=json.load(open('$MANIFEST')); s=next(x for x in d['scenarios'] if x['id']=='$scenario_id'); [print(x) for x in s['forbidden_strings']]")
  while IFS= read -r forbidden; do
    [ -n "$forbidden" ] || continue
    if grep -rnF "$forbidden" "$latest_run" >/dev/null 2>&1; then
      fail "forbidden string '$forbidden' found in run artifacts for $scenario_id"
    fi
  done <<< "$FORBIDDEN_STRINGS"
done <<< "$SCENARIOS"

# SEP log schema validation — validate any .md SEP logs found in .squad-log/
SEP_LOG_DIR="$ROOT/ai-docs/.squad-log"
SEP_SCHEMA="$SEP_LOG_DIR/sep-log.schema.json"

if [ -f "$SEP_SCHEMA" ] && compgen -G "$SEP_LOG_DIR/*.md" >/dev/null 2>&1; then
  python3 - <<'PY' "$SEP_SCHEMA" "$SEP_LOG_DIR" || exit 1
import sys
import json
import re
import os

schema_path = sys.argv[1]
log_dir = sys.argv[2]

schema = json.load(open(schema_path))
required_fields = schema.get("required", [])

errors = []
validated = 0

for fname in sorted(os.listdir(log_dir)):
    if not fname.endswith(".md"):
        continue
    fpath = os.path.join(log_dir, fname)
    content = open(fpath).read()
    # Extract YAML frontmatter between --- delimiters
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        errors.append(f"{fname}: missing YAML frontmatter")
        continue
    frontmatter_text = match.group(1)
    # Parse simple key: value pairs (not full YAML — avoids dependency on PyYAML)
    keys = set(re.findall(r"^(\w[\w_-]*):", frontmatter_text, re.MULTILINE))
    missing = [f for f in required_fields if f not in keys]
    if missing:
        errors.append(f"{fname}: missing required fields: {', '.join(missing)}")
    validated += 1

if errors:
    for e in errors:
        print(f"SEP log schema error: {e}", file=sys.stderr)
    raise SystemExit(f"{len(errors)} SEP log(s) failed schema validation")

if validated > 0:
    print(f"SEP log schema: {validated} log(s) validated OK")
PY
fi

echo "claude-tech-squad golden runs passed"
