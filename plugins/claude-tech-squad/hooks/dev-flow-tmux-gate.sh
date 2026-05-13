#!/usr/bin/env bash
# dev-flow-tmux-gate.sh — UserPromptSubmit hook.
#
# This hook used to block dev-flow prompts and offer a tmux re-launch
# choice. The runtime now resolves teammate vs inline automatically in
# preflight, so the hook is intentionally non-blocking.
#
# Exit 0 = allow the prompt unchanged.

set -u

INPUT=$(cat)
PROMPT=$(printf '%s' "$INPUT" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null \
  || echo "")

if [ -z "$PROMPT" ]; then
  exit 0
fi

DEV_FLOW_RE='(^|[[:space:]])/(claude-tech-squad:)?(mini-squad|squad|discovery|implement|refactor|tech-debt-audit|pentest-deep|incident-postmortem|llm-eval|iac-review|pr-review|from-ticket|multi-service|hotfix|bug-fix|inception|onboarding|security-audit|migration-plan|prompt-review)([[:space:]]|$)'

if ! printf '%s' "$PROMPT" | grep -qE "$DEV_FLOW_RE"; then
  exit 0
fi

exit 0
