#!/usr/bin/env bash
# init-skill-branch.sh — at skill preflight, create the orchestrator's
# skill branch on the MAIN project worktree. Every per-agent worktree
# spawned during this skill run derives from this branch (because
# spawn-agent-worktree.sh branches from HEAD), and on cleanup their
# commits are merged back into this branch. The skill branch itself
# stays in the project's main worktree the whole time.
#
# Usage:
#   init-skill-branch.sh <skill_name>
#
# Output (single line, key=value):
#   skill_branch=<name> base_branch=<orig_branch> base_commit=<sha>
#
# Exit codes:
#   0 — branch created and checked out in main worktree
#   2 — not a git repo
#   3 — main worktree dirty (untracked or modified files); user must commit/stash first
#   4 — git checkout -b failed

set -euo pipefail

SKILL="${1:?skill name required}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "init-skill-branch: not inside a git repository" >&2
  exit 2
fi

REPO_TOPLEVEL=$(git rev-parse --show-toplevel)
cd "$REPO_TOPLEVEL"

# Refuse to create the skill branch on a dirty tree — agent merges later
# would conflict with uncommitted user work.
if [ -n "$(git status --porcelain)" ]; then
  echo "init-skill-branch: main worktree is dirty; commit or stash before running this skill" >&2
  exit 3
fi

ORIG_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --short HEAD)
BASE_COMMIT=$(git rev-parse HEAD)

EPOCH=$(date +%s)
SAFE_SKILL="${SKILL//[^a-zA-Z0-9-]/-}"
SKILL_BRANCH="cts/skill/${SAFE_SKILL}-${EPOCH}"

if ! git checkout -b "$SKILL_BRANCH" "$BASE_COMMIT" >/dev/null 2>&1; then
  echo "init-skill-branch: git checkout -b $SKILL_BRANCH failed" >&2
  exit 4
fi

SENTINEL_DIR="${REPO_TOPLEVEL}/ai-docs/.squad-log"
mkdir -p "$SENTINEL_DIR"
SENTINEL="${SENTINEL_DIR}/.active-skill"
WORKTREE_BASE="${CTS_WORKTREE_BASE:-${TMPDIR:-/tmp}/cts-worktrees}"
{
  printf 'skill=%s\n' "$SAFE_SKILL"
  printf 'skill_branch=%s\n' "$SKILL_BRANCH"
  printf 'base_branch=%s\n' "$ORIG_BRANCH"
  printf 'base_commit=%s\n' "$BASE_COMMIT"
  printf 'worktree_base=%s\n' "$WORKTREE_BASE"
  printf 'repo_toplevel=%s\n' "$REPO_TOPLEVEL"
  printf 'started_at=%s\n' "$EPOCH"
} >"$SENTINEL"

printf 'skill_branch=%s base_branch=%s base_commit=%s\n' \
  "$SKILL_BRANCH" "$ORIG_BRANCH" "$BASE_COMMIT"
