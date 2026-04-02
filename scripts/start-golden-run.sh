#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/fixtures/dogfooding/scenarios.json"
RUNS_DIR="${GOLDEN_RUNS_DIR:-$ROOT/ai-docs/dogfood-runs}"
SCENARIO_ID="${1:-}"
OPERATOR="${2:-unknown-operator}"

if [ -z "$SCENARIO_ID" ]; then
  echo "Usage: $0 <scenario-id> [operator]"
  exit 1
fi

python3 -m json.tool "$MANIFEST" >/dev/null

SCENARIO_JSON=$(python3 - <<'PY' "$MANIFEST" "$SCENARIO_ID"
import json
import sys

manifest = json.load(open(sys.argv[1]))
scenario_id = sys.argv[2]
for scenario in manifest["scenarios"]:
    if scenario["id"] == scenario_id:
        print(json.dumps(scenario))
        break
else:
    raise SystemExit(1)
PY
) || {
  echo "Unknown scenario: $SCENARIO_ID"
  exit 1
}

TIMESTAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
TARGET_DIR="$RUNS_DIR/$SCENARIO_ID/$TIMESTAMP"
mkdir -p "$TARGET_DIR"

PROMPT=$(python3 - <<'PY' "$SCENARIO_JSON"
import json
import sys
print(json.loads(sys.argv[1])["prompt"])
PY
)

WORKFLOW=$(python3 - <<'PY' "$SCENARIO_JSON"
import json
import sys
print(json.loads(sys.argv[1])["workflow"])
PY
)

FIXTURE_PATH=$(python3 - <<'PY' "$SCENARIO_JSON"
import json
import sys
print(json.loads(sys.argv[1])["repo_path"])
PY
)

printf '%s\n' "$PROMPT" > "$TARGET_DIR/prompt.txt"
cp "$ROOT/templates/golden-run-scorecard.md" "$TARGET_DIR/scorecard.md"

cat > "$TARGET_DIR/metadata.yaml" <<EOF
scenario_id: $SCENARIO_ID
workflow: $WORKFLOW
fixture_path: $FIXTURE_PATH
execution_mode: inline | tmux
timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
operator: $OPERATOR
score: pass | fail
notes: "fill after the run"
EOF

cat > "$TARGET_DIR/trace.md" <<EOF
# Trace

Paste the visible execution trace for $SCENARIO_ID here.
EOF

cat > "$TARGET_DIR/final.md" <<EOF
# Final Output

Paste the final Claude answer for $SCENARIO_ID here.
EOF

echo "Golden run scaffold created:"
echo "$TARGET_DIR"
