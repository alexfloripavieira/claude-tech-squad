#!/usr/bin/env bash
# stale-skill-detector.sh — SessionStart hook.
#
# Detects orphaned skill state from a previous run (sentinel present but
# watchdog dead, OR sentinel age exceeds the skill-level cap). If found,
# emit a banner via stdout (Claude Code injects SessionStart stdout as
# additionalContext) telling the user to either /claude-tech-squad:reset
# or run a one-line cleanup. Never blocks — purely advisory.

set -u

# Search upward from CWD for an active-skill sentinel
DIR="$PWD"
SENTINEL=""
REPO=""
while [ "$DIR" != "/" ]; do
  if [ -f "$DIR/ai-docs/.squad-log/.active-skill" ]; then
    SENTINEL="$DIR/ai-docs/.squad-log/.active-skill"
    REPO="$DIR"
    break
  fi
  DIR=$(dirname "$DIR")
done

[ -z "$SENTINEL" ] && exit 0

SKILL=$(grep '^skill=' "$SENTINEL" | cut -d= -f2-)
SKILL_BRANCH=$(grep '^skill_branch=' "$SENTINEL" | cut -d= -f2-)
STARTED_AT=$(grep '^started_at=' "$SENTINEL" | cut -d= -f2-)
WORKTREE_BASE=$(grep '^worktree_base=' "$SENTINEL" | cut -d= -f2-)

NOW=$(date +%s)
AGE=$(( NOW - ${STARTED_AT:-$NOW} ))

# Check watchdog
WD_PID_FILE="$REPO/ai-docs/.squad-log/.watchdog.pid"
WD_ALIVE=false
if [ -f "$WD_PID_FILE" ]; then
  WD_PID=$(cat "$WD_PID_FILE" 2>/dev/null || echo "")
  if [ -n "$WD_PID" ] && kill -0 "$WD_PID" 2>/dev/null; then
    WD_ALIVE=true
  fi
fi

# Stale criteria: age > 2h OR watchdog dead
SKILL_CAP="${SKILL_MAX_RUNTIME_SECONDS:-7200}"
STALE=false
if [ "$AGE" -gt "$SKILL_CAP" ] || [ "$WD_ALIVE" = "false" ]; then
  STALE=true
fi

[ "$STALE" = "false" ] && exit 0

cat <<EOF
[CTS Stale Skill Detected]

Sentinel: $SENTINEL
  skill=$SKILL
  skill_branch=$SKILL_BRANCH
  age=${AGE}s (cap=${SKILL_CAP}s)
  watchdog_alive=$WD_ALIVE

A previous skill run did not finalize cleanly. Until you clean it up, the
skill-active-guard hook will block Edit/Write/Bash mutations on this
repo's main worktree.

Recover with one of:

  # automatic — kills survivors, removes worktrees, deletes branches, clears sentinel
  bash \${CLAUDE_PLUGIN_ROOT}/bin/finalize-skill.sh "$SKILL_BRANCH" || true
  find "$WORKTREE_BASE" -maxdepth 1 -name "cts-${SKILL}-*" -exec rm -rf {} +
  cd "$REPO" && git worktree prune && git branch -D \$(git for-each-ref --format='%(refname:short)' refs/heads/cts/) 2>/dev/null
  rm -f "$REPO/ai-docs/.squad-log/.active-skill" "$REPO/ai-docs/.squad-log/.watchdog.pid"
  rm -f "$REPO/ai-docs/.squad-log/.agents/"*.spawned 2>/dev/null

  # or restart in a fresh tmux + flag pair after cleanup above
EOF
exit 0
