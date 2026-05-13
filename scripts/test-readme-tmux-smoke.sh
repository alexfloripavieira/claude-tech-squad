#!/usr/bin/env bash
set -euo pipefail

README_PATH="${README_PATH:-README.md}"

if [[ ! -f "$README_PATH" ]]; then
  echo "FAIL: README.md not found at $README_PATH" >&2
  exit 1
fi

if ! grep -q "## Claude Tech Squad Tmux Smoke Test" "$README_PATH"; then
  echo "FAIL: heading '## Claude Tech Squad Tmux Smoke Test' not found in $README_PATH" >&2
  exit 1
fi

if ! grep -q "teammate mode com tmux" "$README_PATH"; then
  echo "FAIL: phrase 'teammate mode com tmux' not found in $README_PATH" >&2
  exit 1
fi

if ! grep -q "governanca automatica" "$README_PATH"; then
  echo "FAIL: phrase 'governanca automatica' not found in $README_PATH" >&2
  exit 1
fi

echo "PASS: README tmux smoke assertions satisfied"
exit 0
