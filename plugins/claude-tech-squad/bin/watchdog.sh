#!/usr/bin/env bash
# watchdog.sh — per-skill background daemon that enforces per-agent
# runtime caps. Launched by init-skill-branch.sh, stopped by
# finalize-skill.sh.
#
# Behavior:
#   - Polls every WATCHDOG_INTERVAL_SECONDS (default 30s).
#   - Reads spawn markers from ai-docs/.squad-log/.agents/*.spawned.
#     Each marker contains: agent, skill, path, branch, spawned_at.
#   - For each marker whose age > AGENT_MAX_RUNTIME_SECONDS (default 900),
#     finds any claude process matching `--agent-id <agent>@<skill>` and
#     kills it (SIGTERM, then SIGKILL after 5s). Calls
#     cleanup-agent-worktree.sh on the path. Writes a .killed marker.
#   - When the .active-skill sentinel disappears, watchdog exits.
#   - Whole-skill cap: if sentinel age > SKILL_MAX_RUNTIME_SECONDS
#     (default 7200 = 2h), watchdog kills any surviving teammate
#     processes and writes ai-docs/.squad-log/.skill-timed-out.
#
# Usage:
#   watchdog.sh <repo_toplevel>
#
# Runs detached; PID is written to <repo>/ai-docs/.squad-log/.watchdog.pid
# by init-skill-branch.sh.

set -u

REPO="${1:?repo toplevel required}"
LOG_DIR="$REPO/ai-docs/.squad-log"
SENTINEL="$LOG_DIR/.active-skill"
AGENTS_DIR="$LOG_DIR/.agents"
LOG_FILE="$LOG_DIR/.watchdog.log"

INTERVAL="${WATCHDOG_INTERVAL_SECONDS:-30}"
AGENT_CAP="${AGENT_MAX_RUNTIME_SECONDS:-900}"
SKILL_CAP="${SKILL_MAX_RUNTIME_SECONDS:-7200}"

mkdir -p "$AGENTS_DIR"

log() {
  printf '%s [watchdog pid=%s] %s\n' "$(date -Iseconds)" "$$" "$1" >>"$LOG_FILE"
}

now() { date +%s; }

kill_agent_procs() {
  local agent="$1" skill="$2"
  local pattern="--agent-id ${agent}@${skill}"
  local pids
  pids=$(pgrep -f -- "$pattern" 2>/dev/null || pgrep -f "$pattern" 2>/dev/null || true)
  if [ -z "$pids" ]; then
    return 0
  fi
  log "killing pids for ${agent}@${skill}: $pids"
  for p in $pids; do kill -TERM "$p" 2>/dev/null || true; done
  sleep 5
  for p in $pids; do kill -KILL "$p" 2>/dev/null || true; done
}

log "started repo=$REPO agent_cap=${AGENT_CAP}s skill_cap=${SKILL_CAP}s interval=${INTERVAL}s"

while [ -f "$SENTINEL" ]; do
  # ── skill-level cap ──
  STARTED_AT=$(grep '^started_at=' "$SENTINEL" 2>/dev/null | cut -d= -f2-)
  if [ -n "$STARTED_AT" ]; then
    AGE=$(( $(now) - STARTED_AT ))
    if [ "$AGE" -gt "$SKILL_CAP" ]; then
      log "SKILL CAP HIT: age=${AGE}s > ${SKILL_CAP}s — killing all teammates and aborting"
      SKILL=$(grep '^skill=' "$SENTINEL" 2>/dev/null | cut -d= -f2-)
      for pid in $(pgrep -f -- "--team-name ${SKILL}" 2>/dev/null || pgrep -f "team-name ${SKILL}" 2>/dev/null || true); do
        kill -TERM "$pid" 2>/dev/null || true
      done
      sleep 5
      for pid in $(pgrep -f -- "--team-name ${SKILL}" 2>/dev/null || pgrep -f "team-name ${SKILL}" 2>/dev/null || true); do
        kill -KILL "$pid" 2>/dev/null || true
      done
      printf 'skill=%s aborted_at=%s reason=skill_cap age_seconds=%s\n' \
        "$SKILL" "$(now)" "$AGE" >"$LOG_DIR/.skill-timed-out"
      log "wrote .skill-timed-out marker"
      break
    fi
  fi

  # ── per-agent cap ──
  for marker in "$AGENTS_DIR"/*.spawned; do
    [ -f "$marker" ] || continue
    SPAWNED_AT=$(grep '^spawned_at=' "$marker" | cut -d= -f2-)
    [ -n "$SPAWNED_AT" ] || continue
    AGE=$(( $(now) - SPAWNED_AT ))
    if [ "$AGE" -gt "$AGENT_CAP" ]; then
      AGENT=$(grep '^agent=' "$marker" | cut -d= -f2-)
      SKILL=$(grep '^skill=' "$marker" | cut -d= -f2-)
      PATH_=$(grep '^path=' "$marker" | cut -d= -f2-)
      log "AGENT CAP HIT: ${AGENT}@${SKILL} age=${AGE}s > ${AGENT_CAP}s — killing"
      kill_agent_procs "$AGENT" "$SKILL"
      # Force cleanup of worktree (best-effort; merge may fail, that's OK)
      if [ -d "$PATH_" ]; then
        CTS_LEAD_OK=1 bash "${CLAUDE_PLUGIN_ROOT:-/home/alex/claude-tech-squad/plugins/claude-tech-squad}/bin/cleanup-agent-worktree.sh" "$PATH_" >>"$LOG_FILE" 2>&1 || true
      fi
      mv "$marker" "${marker%.spawned}.killed" 2>/dev/null || rm -f "$marker"
      log "agent ${AGENT} killed, marker moved to .killed"
    fi
  done

  sleep "$INTERVAL"
done

log "sentinel gone — exiting cleanly"
exit 0
