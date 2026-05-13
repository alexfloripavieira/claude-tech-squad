#!/usr/bin/env bash
# detect-team-mode.sh — resolves Agent Teams execution mode at preflight.
#
# Output: single line emitted to stdout in the form
#   mode=<teammate|inline> tmux=<0|1> inside_tmux=<0|1> flag=<0|1> version=<x.y.z|unknown>
#
# Exit codes:
#   0 — mode resolved (read stdout to determine teammate vs inline)
#   2 — unrecoverable preflight error (e.g. claude binary missing)
#
# Caller (skill orchestrator) emits the canonical operator line:
#   [Team Mode Resolved] mode=<...> | tmux=<...> | inside_tmux=<...> | flag=<...> | version=<...>
#
# Behavior:
#   - tmux binary missing                  -> mode=inline
#   - CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS != 1 -> mode=inline
#   - claude --version < 2.1.32            -> mode=inline
#   - tmux present but $TMUX empty          -> mode=inline
#   - tmux present and inside session with both flags -> mode=teammate

set -u

REQUIRED_VERSION="2.1.32"

bool() { if [ "$1" = "1" ] || [ "$1" = "true" ]; then echo 1; else echo 0; fi; }

if command -v tmux >/dev/null 2>&1; then
  TMUX_BINARY=1
else
  TMUX_BINARY=0
fi

if [ -n "${TMUX:-}" ]; then
  INSIDE_TMUX=1
else
  INSIDE_TMUX=0
fi

if [ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" = "1" ] && [ "${CLAUDE_CODE_TEAMMATE_MODE:-}" = "tmux" ]; then
  FLAG=1
else
  FLAG=0
fi

if command -v claude >/dev/null 2>&1; then
  RAW_VERSION="$(claude --version 2>/dev/null | awk '{print $1}' | head -n1)"
  VERSION="${RAW_VERSION:-unknown}"
else
  VERSION="unknown"
fi

ver_ge() {
  # ver_ge <a> <b> -> 0 if a >= b
  [ "$1" = "$2" ] && return 0
  printf '%s\n%s\n' "$2" "$1" | sort -V -C 2>/dev/null
}

VERSION_OK=0
if [ "$VERSION" != "unknown" ]; then
  if ver_ge "$VERSION" "$REQUIRED_VERSION"; then
    VERSION_OK=1
  fi
fi

if [ "$TMUX_BINARY" = "1" ] && [ "$INSIDE_TMUX" = "1" ] && [ "$FLAG" = "1" ] && [ "$VERSION_OK" = "1" ]; then
  MODE="teammate"
else
  MODE="inline"
fi

printf 'mode=%s tmux=%s inside_tmux=%s flag=%s version=%s\n' \
  "$MODE" "$TMUX_BINARY" "$INSIDE_TMUX" "$FLAG" "$VERSION"
