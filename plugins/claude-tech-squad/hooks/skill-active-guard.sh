#!/usr/bin/env bash
# skill-active-guard.sh — PreToolUse hook.
#
# When a CTS dev-flow skill is active (sentinel ai-docs/.squad-log/.active-skill
# present, written by init-skill-branch.sh and removed by finalize-skill.sh),
# block direct Edit/Write/NotebookEdit operations on paths inside the project's
# main worktree. Mutations during an active skill MUST happen inside an agent
# worktree (under $worktree_base, default /tmp/cts-worktrees) so cleanup-agent-
# worktree.sh merges them into the skill branch with --no-ff.
#
# Bash mutations (git commit, sed -i, etc.) on the main worktree are also
# blocked, with an allowlist for read-only / inspection commands.
#
# Exit 0 = allow.
# Exit 2 = block, message to stderr.
#
# The lead orchestrator can bypass by exporting CTS_LEAD_OK=1 in the same
# Bash invocation (e.g. when running cleanup-agent-worktree.sh which does
# need to touch the main worktree to perform the merge).

set -u

INPUT=$(cat)

TOOL_NAME=$(printf '%s' "$INPUT" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null \
  || echo "")

# Locate sentinel via parent dir search (hook runs from the project's CWD)
SENTINEL=""
DIR="$PWD"
while [ "$DIR" != "/" ]; do
  if [ -f "$DIR/ai-docs/.squad-log/.active-skill" ]; then
    SENTINEL="$DIR/ai-docs/.squad-log/.active-skill"
    REPO_TOPLEVEL="$DIR"
    break
  fi
  DIR=$(dirname "$DIR")
done

# No active skill -> nothing to enforce
if [ -z "$SENTINEL" ]; then
  exit 0
fi

# Lead bypass for orchestrator-side operations (cleanup merge, finalize, etc.)
if [ "${CTS_LEAD_OK:-}" = "1" ]; then
  exit 0
fi

# Read sentinel
WORKTREE_BASE=$(grep '^worktree_base=' "$SENTINEL" | cut -d= -f2-)
SKILL=$(grep '^skill=' "$SENTINEL" | cut -d= -f2-)
SKILL_BRANCH=$(grep '^skill_branch=' "$SENTINEL" | cut -d= -f2-)

block() {
  local reason="$1"
  cat >&2 <<EOF
[CTS Skill Guard] BLOCKED — skill '${SKILL}' is active (skill_branch=${SKILL_BRANCH}).
${reason}

Allowed mutation paths:
  - Inside an agent worktree under: ${WORKTREE_BASE}/

To finish the skill cleanly, complete Phase C (cleanup-agent-worktree.sh)
for every spawned agent and Phase D (finalize-skill.sh). The finalize
helper removes this sentinel.

Emergency bypass (operator only): export CTS_LEAD_OK=1 before this call.
EOF
  exit 2
}

case "$TOOL_NAME" in
  Edit|Write|NotebookEdit)
    FILE_PATH=$(printf '%s' "$INPUT" | python3 -c \
      "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" \
      2>/dev/null || echo "")
    if [ -z "$FILE_PATH" ]; then
      exit 0
    fi
    # Allow paths that live under the agent worktree base
    case "$FILE_PATH" in
      "$WORKTREE_BASE"/*) exit 0 ;;
      "$REPO_TOPLEVEL"/ai-docs/.squad-log/*) exit 0 ;;
      "$REPO_TOPLEVEL"/.gitignore) exit 0 ;;
    esac
    # Anything else inside the repo toplevel = direct main-worktree edit
    case "$FILE_PATH" in
      "$REPO_TOPLEVEL"/*)
        block "Direct ${TOOL_NAME} on main worktree path: ${FILE_PATH}"
        ;;
    esac
    exit 0
    ;;
  Bash)
    CMD=$(printf '%s' "$INPUT" | python3 -c \
      "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" \
      2>/dev/null || echo "")
    # Allow any cmd that runs inside agent worktree base
    if printf '%s' "$CMD" | grep -qF "$WORKTREE_BASE"; then
      exit 0
    fi
    # Allow CTS helpers (lead invokes them on main worktree intentionally)
    if printf '%s' "$CMD" | grep -qE 'bin/(spawn-agent-worktree|cleanup-agent-worktree|finalize-skill|init-skill-branch|watchdog)\.sh'; then
      exit 0
    fi
    # Allow lead's SEP log lifecycle on main worktree: git add/commit limited
    # to ai-docs/.squad-log/ paths. Lead writes the SEP log there and commits
    # it on the skill branch before finalize. Match either explicit pathspec
    # or commit subjects scoped to the squad log namespace.
    if printf '%s' "$CMD" | grep -qE 'git[[:space:]]+(add|commit)[^|;&]*ai-docs/\.squad-log'; then
      exit 0
    fi
    if printf '%s' "$CMD" | grep -qE 'git[[:space:]]+commit[^|;&]*"[^"]*squad-log'; then
      exit 0
    fi
    # Allow lead to maintain top-level .gitignore (e.g. add .claude/ exclude
    # so finalize sees a clean tree). git add/commit limited to .gitignore.
    if printf '%s' "$CMD" | grep -qE 'git[[:space:]]+(add|commit)[^|;&]*\.gitignore'; then
      exit 0
    fi
    if printf '%s' "$CMD" | grep -qE 'git[[:space:]]+commit[^|;&]*"[^"]*gitignore'; then
      exit 0
    fi
    # Block obvious main-worktree mutators
    if printf '%s' "$CMD" | grep -qE '(^|[[:space:]])(git[[:space:]]+(commit|add|merge|rebase|reset|checkout)|sed[[:space:]]+-i|>[[:space:]]*[^|&]*\.(py|md|ts|tsx|js|jsx|yml|yaml|json|sh)([[:space:]]|$))'; then
      block "Bash mutation outside agent worktree: ${CMD}"
    fi
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
