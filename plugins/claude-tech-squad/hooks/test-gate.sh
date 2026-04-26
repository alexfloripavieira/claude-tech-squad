#!/usr/bin/env bash
set -euo pipefail

[[ "${CLAUDE_TOOL_NAME:-}" == "Agent" ]] || exit 0

SUBAGENT="${CLAUDE_TOOL_INPUT_subagent_type:-}"
SKILL="${CLAUDE_SKILL_NAME:-}"
RUN_ID="${CLAUDE_RUN_ID:-unknown}"

[[ "$SUBAGENT" == "claude-tech-squad:test-automation-engineer" ]] || exit 0

case "$SKILL" in
    squad|implement|refactor|bug-fix|hotfix) ;;
    *) exit 0 ;;
esac

REPO_ROOT="${CLAUDE_PROJECT_ROOT:-$(pwd)}"
SQUAD_CLI="${REPO_ROOT}/plugins/claude-tech-squad/bin/squad-cli"

if [[ ! -x "$SQUAD_CLI" ]]; then
    echo "test-gate: squad-cli not found at $SQUAD_CLI" >&2
    exit 0
fi

set +e
"$SQUAD_CLI" test-gate evaluate --skill "$SKILL" --run-id "$RUN_ID" --repo-root "$REPO_ROOT"
RC=$?
set -e

case $RC in
    0) exit 0 ;;
    2) echo "test-gate: BLOCKING — production file without paired test" >&2; exit 2 ;;
    *) echo "test-gate: internal error rc=$RC" >&2; exit 1 ;;
esac
