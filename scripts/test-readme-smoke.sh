#!/usr/bin/env bash
set -euo pipefail

README_PATH="${README_PATH:-README.md}"

if [[ ! -f "$README_PATH" ]]; then
  echo "FAIL: README.md not found at $README_PATH" >&2
  exit 1
fi

if ! grep -q "## CTS Teammate Mode Smoke Test" "$README_PATH"; then
  echo "FAIL: heading '## CTS Teammate Mode Smoke Test' not found in $README_PATH" >&2
  exit 1
fi

if ! grep -q "teammate mode com governanca automatica" "$README_PATH"; then
  echo "FAIL: phrase 'teammate mode com governanca automatica' not found in $README_PATH" >&2
  exit 1
fi

echo "PASS: README smoke assertions satisfied"
exit 0
