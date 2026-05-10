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
ORPHAN_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/heads/cts/ 2>/dev/null \
  | grep -v "^${SKILL_BRANCH}$" \
  | wc -l \
  | tr -d ' ')

CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "DETACHED")
ON_SKILL=false
[ "$CURRENT_BRANCH" = "$SKILL_BRANCH" ] && ON_SKILL=true

CLEAN=true
[ -n "$(git status --porcelain)" ] && CLEAN=false

printf 'skill_branch=%s orphan_worktrees=%s orphan_branches=%s main_worktree_clean=%s on_skill_branch=%s\n' \
  "$SKILL_BRANCH" "$ORPHAN_WTS" "$ORPHAN_BRANCHES" "$CLEAN" "$ON_SKILL"

if [ "$ORPHAN_WTS" -gt 0 ]; then exit 2; fi
if [ "$ORPHAN_BRANCHES" -gt 0 ]; then exit 3; fi
if [ "$CLEAN" = "false" ]; then exit 4; fi
if [ "$ON_SKILL" = "false" ]; then exit 5; fi

# Clear active-skill sentinel so the skill-active-guard hook stops blocking
rm -f "${REPO_TOPLEVEL}/ai-docs/.squad-log/.active-skill" 2>/dev/null || true

exit 0
