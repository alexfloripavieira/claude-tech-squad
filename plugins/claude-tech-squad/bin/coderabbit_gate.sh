#!/usr/bin/env bash
# CodeRabbit final review gate for /implement and /squad.
#
# Behavior:
#   - If coderabbit CLI is missing, emit a SKIP marker and exit 0 (graceful degrade).
#   - Otherwise run `coderabbit review --plain --type <mode>` against local changes.
#   - Parse "Review completed: N finding(s)" from output.
#   - Exit 0 when N == 0 (clean). Exit 2 when N > 0 (findings detected, caller must re-spawn reviewer).
#   - Exit 1 on unexpected errors (network, auth, etc).
#
# Env:
#   CODERABBIT_GATE_MODE   uncommitted | committed | all   (default: uncommitted)
#   CODERABBIT_GATE_BASE   optional base branch for --base
#
# Output:
#   Prints the full CodeRabbit output to stdout. Prints markers on stderr for the orchestrator.

set -uo pipefail

MODE="${CODERABBIT_GATE_MODE:-uncommitted}"
BASE_ARG=()
if [ -n "${CODERABBIT_GATE_BASE:-}" ]; then
  BASE_ARG=(--base "$CODERABBIT_GATE_BASE")
fi

if ! command -v coderabbit >/dev/null 2>&1; then
  echo "[Gate Skipped] coderabbit-final-review | CLI ausente — instale coderabbit CLI para ativar" >&2
  exit 0
fi

TMP_OUT="$(mktemp -t cr-gate.XXXXXX)"
trap 'rm -f "$TMP_OUT"' EXIT

echo "[Gate] coderabbit-final-review | mode=$MODE ${BASE_ARG[*]}" >&2

set +e
coderabbit review --plain --no-color --type "$MODE" "${BASE_ARG[@]}" >"$TMP_OUT" 2>&1
CR_STATUS=$?
set -e

cat "$TMP_OUT"

if grep -qiE "not (logged in|authenticated)|auth( |entication) (required|failed)|invalid api key" "$TMP_OUT"; then
  echo "[Gate Error] coderabbit-final-review | autenticacao falhou — rode: coderabbit auth login" >&2
  exit 1
fi

FINDINGS=$(grep -oE 'Review completed: [0-9]+ finding' "$TMP_OUT" | grep -oE '[0-9]+' | head -1 || true)
FINDINGS="${FINDINGS:-0}"

if [ "$CR_STATUS" -ne 0 ] && [ "$FINDINGS" -eq 0 ]; then
  if grep -qiE "no changes|nothing to review|no files found" "$TMP_OUT"; then
    echo "[Gate Clean] coderabbit-final-review | sem mudancas para revisar" >&2
    exit 0
  fi
  echo "[Gate Error] coderabbit-final-review | CLI retornou $CR_STATUS sem findings parseaveis" >&2
  exit 1
fi

if [ "$FINDINGS" -gt 0 ]; then
  echo "[Gate Blocked] coderabbit-final-review | $FINDINGS finding(s) detectado(s)" >&2
  exit 2
fi

echo "[Gate Clean] coderabbit-final-review | sem findings" >&2
exit 0
