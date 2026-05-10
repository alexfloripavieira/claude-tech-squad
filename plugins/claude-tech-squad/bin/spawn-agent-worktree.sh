#!/usr/bin/env bash
# spawn-agent-worktree.sh — create an isolated git worktree for one agent spawn.
#
# Usage:
#   spawn-agent-worktree.sh <skill> <agent_name> [agent_id]
#
# Output (single line, key=value pairs):
#   path=<absolute_worktree_path> branch=<branch_name> base=<base_commit_sha>
#
# Exit codes:
#   0 — worktree created
#   2 — preconditions not met (not a git repo, etc.)
#   3 — git worktree add failed
#
# Notes:
#   - Worktrees are placed under $CTS_WORKTREE_BASE (default $TMPDIR/cts-worktrees
#     or /tmp/cts-worktrees) so they never pollute the main repo working tree.
#   - The branch is created from the current HEAD of the main checkout.
#   - The orchestrator MUST pass `path=` to the agent's spawn prompt and call
#     cleanup-agent-worktree.sh after the agent's result_contract is received.

set -euo pipefail

SKILL="${1:?skill name required (arg 1)}"
AGENT="${2:?agent name required (arg 2)}"
AGENT_ID="${3:-$$}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "spawn-agent-worktree: not inside a git repository" >&2
  exit 2
fi

REPO_TOPLEVEL=$(git rev-parse --show-toplevel)
BASE_SHA=$(git -C "$REPO_TOPLEVEL" rev-parse HEAD)

EPOCH=$(date +%s)
SAFE_SKILL="${SKILL//[^a-zA-Z0-9-]/-}"
SAFE_AGENT="${AGENT//[^a-zA-Z0-9-]/-}"
SAFE_ID="${AGENT_ID//[^a-zA-Z0-9-]/-}"

NAME="cts-${SAFE_SKILL}-${SAFE_AGENT}-${EPOCH}-${SAFE_ID}"
BRANCH="cts/${SAFE_SKILL}/${SAFE_AGENT}-${EPOCH}-${SAFE_ID}"
BASE_DIR="${CTS_WORKTREE_BASE:-${TMPDIR:-/tmp}/cts-worktrees}"
WORKTREE_PATH="${BASE_DIR}/${NAME}"

mkdir -p "$BASE_DIR"

if ! git -C "$REPO_TOPLEVEL" worktree add -b "$BRANCH" "$WORKTREE_PATH" "$BASE_SHA" >/dev/null 2>&1; then
  echo "spawn-agent-worktree: git worktree add failed (branch=$BRANCH path=$WORKTREE_PATH)" >&2
  exit 3
fi

printf 'path=%s branch=%s base=%s\n' "$WORKTREE_PATH" "$BRANCH" "$BASE_SHA"
