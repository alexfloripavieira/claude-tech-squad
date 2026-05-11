#!/usr/bin/env bash
# finalize-skill.sh — last step of a skill run.
#
# Verifies that NO per-agent worktree or `cts/<skill>/...` branch
# remains. The orchestrator's skill branch (`cts/skill/<skill>-<epoch>`)
# stays checked out in the main project worktree, holding the merged
# work of every agent. The user can then PR/merge it to the original
# base branch (e.g. main) themselves — finalize-skill.sh does NOT push,
# merge to main, or delete the skill branch.
#
# Usage:
#   finalize-skill.sh <skill_branch> [base_branch]
#
# Output (single line, key=value):
#   skill_branch=<name> orphan_worktrees=<N> orphan_branches=<N> main_worktree_clean=<true|false> on_skill_branch=<true|false>
#
# Exit codes:
#   0 — clean: only the project main worktree on the skill branch remains
#   2 — orphan agent worktrees still present (caller must clean them)
#   3 — orphan agent branches still present (caller must inspect)
#   4 — main worktree dirty after consolidation (unexpected)
#   5 — main worktree is NOT on the expected skill branch

set -euo pipefail

SKILL_BRANCH="${1:?skill branch required}"
BASE_BRANCH="${2:-}"

REPO_TOPLEVEL=$(git rev-parse --show-toplevel)
cd "$REPO_TOPLEVEL"

# Drain any pruned worktree records first
git worktree prune >/dev/null 2>&1 || true

# Count surviving per-agent worktrees (exclude the main one)
ORPHAN_WTS=$(git worktree list --porcelain | awk '
  /^worktree / { p=$2; next }
  /^bare/ { p=""; next }
  /^$/ { if (p && p != "'"$REPO_TOPLEVEL"'") c++; p="" }
  END { if (p && p != "'"$REPO_TOPLEVEL"'") c++; print c+0 }
')

# Count surviving per-agent branches under cts/<skill>/...
ORPHAN_BRANCHES=$({
  git for-each-ref --format='%(refname:short)' refs/heads/cts/ 2>/dev/null || true
} | { grep -v "^${SKILL_BRANCH}$" || true; } | wc -l | tr -d ' ')

CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "DETACHED")
ON_SKILL=false
[ "$CURRENT_BRANCH" = "$SKILL_BRANCH" ] && ON_SKILL=true

CLEAN=true
# Exclude ai-docs/.squad-log/ from cleanliness check — those files are
# orchestration metadata (sentinel, watchdog log, agent markers) that
# legitimately exist during the run. CLAUDE.md mandates they are
# gitignored in production repos.
# Exclude paths that are not part of the skill delivery from the
# cleanliness check:
#   - ai-docs/.squad-log/*: orchestration metadata (sentinel, watchdog,
#     spawn markers) populated during the run.
#   - .claude/*: Claude Code per-project workspace (session state, plan
#     files, command output snapshots).
#   - .gitignore at the repo root: written by init-skill-branch.sh if
#     missing; lead may commit later, but finalize must not block on it.
# Use -u (--untracked-files=all) so directories with only untracked
# content surface as per-file entries rather than a single `?? dir/`
# entry that defeats path-level excludes.
DIRTY=$(git status --porcelain -u -- . \
  ':(exclude)ai-docs/.squad-log' \
  ':(exclude)ai-docs/.squad-log/**' \
  ':(exclude).claude' \
  ':(exclude).claude/**' \
  ':(exclude).gitignore' \
  2>/dev/null || true)
[ -n "$DIRTY" ] && CLEAN=false

printf 'skill_branch=%s orphan_worktrees=%s orphan_branches=%s main_worktree_clean=%s on_skill_branch=%s\n' \
  "$SKILL_BRANCH" "$ORPHAN_WTS" "$ORPHAN_BRANCHES" "$CLEAN" "$ON_SKILL"

if [ "$ORPHAN_WTS" -gt 0 ]; then exit 2; fi
if [ "$ORPHAN_BRANCHES" -gt 0 ]; then exit 3; fi
if [ "$CLEAN" = "false" ]; then exit 4; fi
if [ "$ON_SKILL" = "false" ]; then exit 5; fi

# ── M2: SEP log schema validation (AC3) ──
# If a SEP log was written for this skill and the validator exists, run it.
# Exit 6 on schema violation to halt pipeline. Missing validator = warning-only.
SKILL_NAME=$(printf '%s' "$SKILL_BRANCH" | sed -nE 's|^cts/skill/(.+)-[0-9]+$|\1|p')
VALIDATOR="${REPO_TOPLEVEL}/plugins/claude-tech-squad/bin/validate-sep-log.py"
if [ -n "$SKILL_NAME" ] && [ -x "$VALIDATOR" ]; then
  LATEST_SEP=$(ls -t "${REPO_TOPLEVEL}/ai-docs/.squad-log/"*-"${SKILL_NAME}"-*.md 2>/dev/null | head -1)
  if [ -n "$LATEST_SEP" ] && [ -f "$LATEST_SEP" ]; then
    if ! python3 "$VALIDATOR" "$LATEST_SEP" >&2; then
      echo "[SEP Schema Violation] $LATEST_SEP failed schema validation" >&2
      exit 6
    fi
  fi
fi

# Kill watchdog daemon before clearing sentinel (defense in depth: it would
# self-exit on next tick anyway when the sentinel disappears).
WATCHDOG_PID_FILE="${REPO_TOPLEVEL}/ai-docs/.squad-log/.watchdog.pid"
if [ -f "$WATCHDOG_PID_FILE" ]; then
  WD_PID=$(cat "$WATCHDOG_PID_FILE" 2>/dev/null || echo "")
  if [ -n "$WD_PID" ] && kill -0 "$WD_PID" 2>/dev/null; then
    kill -TERM "$WD_PID" 2>/dev/null || true
  fi
  rm -f "$WATCHDOG_PID_FILE" 2>/dev/null || true
fi

# Clear active-skill sentinel so the skill-active-guard hook stops blocking
rm -f "${REPO_TOPLEVEL}/ai-docs/.squad-log/.active-skill" 2>/dev/null || true

# Prune spawned markers (cleanup-agent-worktree handles per-marker removal,
# but be defensive — leftover .spawned files would mislead future runs).
rm -f "${REPO_TOPLEVEL}/ai-docs/.squad-log/.agents/"*.spawned 2>/dev/null || true
rm -f "${REPO_TOPLEVEL}/ai-docs/.squad-log/.agents/"*.killed 2>/dev/null || true

# Sweep $CTS_WORKTREE_BASE for leftover non-worktree files (debug scripts
# created mid-run by the lead, stray logs, etc.). Worktrees themselves
# were removed by cleanup-agent-worktree.sh — anything still here is
# garbage. Only sweeps files directly inside the base dir, not nested.
WORKTREE_BASE="${CTS_WORKTREE_BASE:-${TMPDIR:-/tmp}/cts-worktrees}"
if [ -d "$WORKTREE_BASE" ]; then
  find "$WORKTREE_BASE" -maxdepth 1 -type f -delete 2>/dev/null || true
fi

exit 0
