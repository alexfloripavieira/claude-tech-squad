#!/usr/bin/env bash
# RED-STATE: expected to FAIL against current main (bin/watchdog.sh does not yet
# emit [Kill Confirmed] / [Kill Failed] tags nor create .kill-failed-<pid> markers).
# AC coverage: AC1, AC2.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WATCHDOG="${REPO_ROOT}/plugins/claude-tech-squad/bin/watchdog.sh"
WORKBASE="$(mktemp -d -t cts-watchdog-test.XXXXXX)"
export CTS_WORKTREE_BASE="${WORKBASE}"

fail_count=0
pass() { echo "[TEST] $1: PASS"; }
fail() { echo "[TEST] $1: FAIL — $2"; fail_count=$((fail_count + 1)); }

cleanup() {
  # Best-effort cleanup of any stragglers.
  [ -n "${NORMAL_PID:-}" ] && kill -9 "${NORMAL_PID}" 2>/dev/null || true
  [ -n "${ZOMBIE_PID:-}" ] && kill -9 "${ZOMBIE_PID}" 2>/dev/null || true
  rm -rf "${WORKBASE}"
}
trap cleanup EXIT

if [ ! -x "${WATCHDOG}" ]; then
  fail "watchdog-binary-present" "watchdog.sh missing or not executable at ${WATCHDOG}"
  echo "[TEST SUMMARY] failures=${fail_count}"
  exit 1
fi

# ----- Fixture 1: normal process -----
sleep 60 &
NORMAL_PID=$!
disown "${NORMAL_PID}" 2>/dev/null || true

OUT_NORMAL="$(mktemp)"
"${WATCHDOG}" --kill "${NORMAL_PID}" >"${OUT_NORMAL}" 2>&1 || true

if grep -q "\[Kill Confirmed\]" "${OUT_NORMAL}"; then
  pass "normal-process-kill-confirmed"
else
  fail "normal-process-kill-confirmed" "expected [Kill Confirmed] in watchdog output, got: $(tr '\n' '|' <"${OUT_NORMAL}")"
fi

if ! kill -0 "${NORMAL_PID}" 2>/dev/null; then
  pass "normal-process-actually-dead"
else
  fail "normal-process-actually-dead" "PID ${NORMAL_PID} still alive after watchdog --kill"
fi

# ----- Fixture 2: zombie / uninterruptible (simulated by trap-ignoring TERM/KILL is not
# truly possible from a shell — SIGKILL is uncatchable in POSIX. Simulate the failure
# path by passing a PID that does not exist anymore + a sentinel mode the watchdog
# supports for testing, or by spawning a process and having watchdog observe failure
# via --simulate-failure flag. The contract: when kill cannot confirm death, watchdog
# MUST emit [Kill Failed] and create .kill-failed-<pid>.
# Test invokes the documented test hook: --kill --simulate-failure <pid> -----
sleep 60 &
ZOMBIE_PID=$!
disown "${ZOMBIE_PID}" 2>/dev/null || true

OUT_ZOMBIE="$(mktemp)"
"${WATCHDOG}" --kill --simulate-failure "${ZOMBIE_PID}" >"${OUT_ZOMBIE}" 2>&1 || true

if grep -q "\[Kill Failed\]" "${OUT_ZOMBIE}"; then
  pass "zombie-process-kill-failed-tag"
else
  fail "zombie-process-kill-failed-tag" "expected [Kill Failed] in watchdog output, got: $(tr '\n' '|' <"${OUT_ZOMBIE}")"
fi

if [ -f "${CTS_WORKTREE_BASE}/.kill-failed-${ZOMBIE_PID}" ]; then
  pass "zombie-process-marker-file"
else
  fail "zombie-process-marker-file" "expected ${CTS_WORKTREE_BASE}/.kill-failed-${ZOMBIE_PID} to exist"
fi

# Real cleanup of the simulated zombie.
kill -9 "${ZOMBIE_PID}" 2>/dev/null || true

echo "[TEST SUMMARY] failures=${fail_count}"
[ "${fail_count}" -eq 0 ] || exit 1
exit 0
