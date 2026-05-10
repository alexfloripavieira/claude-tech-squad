#!/usr/bin/env bash
# cleanup-agent-worktree.sh — finalize one agent worktree.
#
# Steps (in order):
#   1. If the agent committed work, merge its branch into the orchestrator's
#      skill branch (the branch checked out in the MAIN project worktree).
#      Uses --no-ff so the agent boundary is preserved in history.
#   2. Remove the per-agent worktree.
#   3. Delete the agent branch unconditionally — its commits are now in
#      the orchestrator's skill branch.
#
# At the end of a skill run, no per-agent worktree or branch remains;
# all consolidated work lives in the orchestrator's skill branch on the
# project's main worktree.
#
# Usage:
#   cleanup-agent-worktree.sh <worktree_path> [orchestrator_branch]
#
# Output (single line, key=value):
#   removed=<path> branch=<branch> merged=<true|false> commits_ahead=<N> conflict=<true|false>
#
# Exit codes:
#   0 — worktree removed; merge succeeded (or nothing to merge)
#   2 — worktree path missing
#   3 — failed to remove the worktree even with rm -rf
#   4 — merge produced a conflict (worktree NOT removed; user must resolve)

set -euo pipefail

WORKTREE_PATH="${1:?worktree path required}"
ORCH_BRANCH="${2:-}"

if [ ! -d "$WORKTREE_PATH" ]; then
  echo "cleanup-agent-worktree: no worktree at $WORKTREE_PATH" >&2
  exit 2
fi

REPO_TOPLEVEL=$(git rev-parse --show-toplevel)

BRANCH=""
WT_HEAD=""
if git -C "$WORKTREE_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  BRANCH=$(git -C "$WORKTREE_PATH" symbolic-ref --short HEAD 2>/dev/null || true)
  WT_HEAD=$(git -C "$WORKTREE_PATH" rev-parse HEAD 2>/dev/null || true)
fi

# Resolve orchestrator branch — defaults to the branch currently checked
# out in the main worktree (which init-skill-branch.sh placed there).
if [ -z "$ORCH_BRANCH" ]; then
  ORCH_BRANCH=$(git -C "$REPO_TOPLEVEL" symbolic-ref --short HEAD 2>/dev/null || true)
fi

BASE_SHA=""
if [ -n "$BRANCH" ] && [ -n "$ORCH_BRANCH" ]; then
  BASE_SHA=$(git -C "$REPO_TOPLEVEL" merge-base "$ORCH_BRANCH" "$BRANCH" 2>/dev/null || true)
fi

COMMITS_AHEAD=0
if [ -n "$WT_HEAD" ] && [ -n "$BASE_SHA" ] && [ "$WT_HEAD" != "$BASE_SHA" ]; then
  COMMITS_AHEAD=$(git -C "$REPO_TOPLEVEL" rev-list --count "${BASE_SHA}..${WT_HEAD}" 2>/dev/null || echo 0)
fi

MERGED=false
CONFLICT=false

if [ "$COMMITS_AHEAD" != "0" ] && [ -n "$ORCH_BRANCH" ] && [ -n "$BRANCH" ]; then
  # Merge agent branch into orchestrator's skill branch in the MAIN worktree.
  if git -C "$REPO_TOPLEVEL" merge --no-ff --no-edit \
       -m "merge: agent worktree ${BRANCH} into ${ORCH_BRANCH}" \
       "$BRANCH" >/dev/null 2>&1; then
    MERGED=true
  else
    # Conflict: leave the merge in progress for the user to resolve, do
    # NOT remove the worktree (the operator may still need to inspect it).
    CONFLICT=true
    printf 'removed=false branch=%s merged=false commits_ahead=%s conflict=true\n' \
      "$BRANCH" "$COMMITS_AHEAD"
    exit 4
  fi
fi

# Remove the worktree (force handles dirty state from agent edits)
if ! git -C "$REPO_TOPLEVEL" worktree remove --force "$WORKTREE_PATH" >/dev/null 2>&1; then
  if ! rm -rf "$WORKTREE_PATH"; then
    echo "cleanup-agent-worktree: failed to remove $WORKTREE_PATH" >&2
    exit 3
  fi
  git -C "$REPO_TOPLEVEL" worktree prune >/dev/null 2>&1 || true
fi

# Branch is no longer needed: its commits are in the skill branch (if any).
if [ -n "$BRANCH" ]; then
  git -C "$REPO_TOPLEVEL" branch -D "$BRANCH" >/dev/null 2>&1 || true
fi

# Remove watchdog spawn marker (if any) — branch name encodes agent+id.
SENTINEL_DIR="$REPO_TOPLEVEL/ai-docs/.squad-log"
if [ -d "$SENTINEL_DIR/.agents" ] && [ -n "${BRANCH:-}" ]; then
  # BRANCH = cts/<skill>/<agent>-<epoch>-<id>
  TAIL="${BRANCH#cts/*/}"
  AGENT_PART="${TAIL%-*-*}"
  ID_PART="${TAIL##*-}"
  rm -f "$SENTINEL_DIR/.agents/${AGENT_PART}-${ID_PART}.spawned" 2>/dev/null || true
fi

printf 'removed=%s branch=%s merged=%s commits_ahead=%s conflict=%s\n' \
  "$WORKTREE_PATH" "${BRANCH:-unknown}" "$MERGED" "$COMMITS_AHEAD" "$CONFLICT"
