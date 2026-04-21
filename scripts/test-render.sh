#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0

check_diff() {
  local name="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    echo "[PASS] $name"
  else
    echo "[FAIL] $name"
    diff -u <(printf '%s' "$expected") <(printf '%s' "$actual") || true
    fail=1
  fi
}

actual=$(cat scripts/test-fixtures/teammate-card-input.json \
  | plugins/claude-tech-squad/scripts/render-teammate-card.sh)
expected=$(cat scripts/test-fixtures/teammate-card-expected.txt)
check_diff "teammate-card" "$actual" "$expected"

actual=$(plugins/claude-tech-squad/scripts/render-pipeline-board.sh \
  scripts/test-fixtures/pipeline-board-input.json)
expected=$(cat scripts/test-fixtures/pipeline-board-expected.txt)
check_diff "pipeline-board" "$actual" "$expected"

exit "$fail"
