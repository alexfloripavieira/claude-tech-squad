#!/usr/bin/env bash
# capture-golden-run.sh — Capture the latest run as a golden run
#
# Usage:
#   bash scripts/capture-golden-run.sh <scenario-id> [operator]
#
# This script reads the most recent SEP log for the given scenario's
# workflow and copies it into the golden run directory along with metadata.
# It does NOT replace start-golden-run.sh — use start-golden-run.sh to
# scaffold BEFORE a run, and capture-golden-run.sh to capture AFTER.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/fixtures/dogfooding/scenarios.json"
RUNS_DIR="${GOLDEN_RUNS_DIR:-$ROOT/ai-docs/dogfood-runs}"
SCENARIO_ID="${1:-}"
OPERATOR="${2:-unknown-operator}"

if [ -z "$SCENARIO_ID" ]; then
  echo "Usage: $0 <scenario-id> [operator]"
  echo ""
  echo "Available scenarios:"
  python3 -c "import json; [print(f'  {s[\"id\"]} ({s[\"workflow\"]})') for s in json.load(open('$MANIFEST'))['scenarios']]"
  exit 1
fi

# Find the scenario
WORKFLOW=$(python3 - <<'PY' "$MANIFEST" "$SCENARIO_ID"
import json, sys
manifest = json.load(open(sys.argv[1]))
for s in manifest["scenarios"]:
    if s["id"] == sys.argv[2]:
        print(s["workflow"].split("+")[0])
        break
else:
    raise SystemExit(1)
PY
) || { echo "Unknown scenario: $SCENARIO_ID"; exit 1; }

# Find the latest SEP log for this workflow
LATEST_LOG=$(ls -t "$ROOT/ai-docs/.squad-log/"*"-$WORKFLOW-"* 2>/dev/null | head -1 || true)

if [ -z "$LATEST_LOG" ]; then
  echo "No SEP log found for workflow '$WORKFLOW' in ai-docs/.squad-log/"
  echo ""
  echo "Run the skill first, then capture:"
  echo "  1. /claude-tech-squad:$WORKFLOW"
  echo "  2. bash scripts/capture-golden-run.sh $SCENARIO_ID $OPERATOR"
  exit 1
fi

# Create the golden run directory
TIMESTAMP="$(date -u +%Y-%m-%dT%H-%M-%SZ)"
TARGET_DIR="$RUNS_DIR/$SCENARIO_ID/$TIMESTAMP"
mkdir -p "$TARGET_DIR"

# Copy SEP log as trace evidence
cp "$LATEST_LOG" "$TARGET_DIR/trace.md"

# Extract metadata from SEP log
python3 - <<'PY' "$LATEST_LOG" "$TARGET_DIR" "$SCENARIO_ID" "$OPERATOR"
import sys, re
from pathlib import Path

log_path = sys.argv[1]
target_dir = sys.argv[2]
scenario_id = sys.argv[3]
operator = sys.argv[4]

content = Path(log_path).read_text()

# Extract frontmatter
fm = {}
in_fm = False
for line in content.split("\n"):
    if line.strip() == "---":
        if in_fm:
            break
        in_fm = True
        continue
    if in_fm and ":" in line:
        key, _, val = line.partition(":")
        fm[key.strip()] = val.strip()

# Write metadata
meta = f"""scenario_id: {scenario_id}
workflow: {fm.get('skill', 'unknown')}
fixture_path: fixtures/dogfooding/{scenario_id}
execution_mode: {fm.get('execution_mode', 'inline')}
timestamp: {fm.get('timestamp', 'unknown')}
operator: {operator}
score: pass
final_status: {fm.get('final_status', 'unknown')}
retry_count: {fm.get('retry_count', '0')}
tokens_input: {fm.get('tokens_input', 'not_tracked')}
tokens_output: {fm.get('tokens_output', 'not_tracked')}
estimated_cost_usd: {fm.get('estimated_cost_usd', 'not_tracked')}
total_duration_ms: {fm.get('total_duration_ms', 'not_tracked')}
notes: "auto-captured from latest SEP log"
"""
Path(f"{target_dir}/metadata.yaml").write_text(meta)

# Write prompt
prompt = f"Golden run for {scenario_id} — auto-captured after execution"
Path(f"{target_dir}/prompt.txt").write_text(prompt + "\n")

# Write final output placeholder
final = f"# Final Output\n\nAuto-captured from SEP log: {Path(log_path).name}\n\n## Output Digest\n"
# Extract output digest from log
digest_start = content.find("## Output Digest")
if digest_start >= 0:
    final += content[digest_start + len("## Output Digest"):].strip()
else:
    final += "(no output digest found in SEP log)"
Path(f"{target_dir}/final.md").write_text(final + "\n")

print(f"Captured: {target_dir}")
print(f"  Source SEP log: {log_path}")
print(f"  Status: {fm.get('final_status', 'unknown')}")
print(f"  Tokens: {fm.get('tokens_input', '?')} in / {fm.get('tokens_output', '?')} out")
PY

# Copy scorecard template
cp "$ROOT/templates/golden-run-scorecard.md" "$TARGET_DIR/scorecard.md"

echo ""
echo "Golden run captured successfully."
echo "Next: review $TARGET_DIR/scorecard.md and fill in the checklist."
echo "Then: bash scripts/dogfood-report.sh to validate."
