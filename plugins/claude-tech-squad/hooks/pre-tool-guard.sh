#!/usr/bin/env bash
# pre-tool-guard.sh — Mechanical enforcer for destructive operations
#
# This hook is designed to be used as a Claude Code PreToolUse hook.
# It intercepts Bash tool calls and blocks patterns that match the
# Global Safety Contract prohibitions.
#
# Installation (add to .claude/settings.json):
# {
#   "hooks": {
#     "PreToolUse": [
#       {
#         "matcher": "Bash",
#         "hooks": [
#           {
#             "type": "command",
#             "command": "bash plugins/claude-tech-squad/hooks/pre-tool-guard.sh"
#           }
#         ]
#       }
#     ]
#   }
# }
#
# The hook reads the tool input from stdin (JSON with "tool_name" and "tool_input").
# Exit 0 = allow, exit 2 = block with message to stderr.

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ "$TOOL_NAME" != "Bash" ] || [ -z "$COMMAND" ]; then
  exit 0
fi

# ── Destructive SQL patterns ────────────────────────────────────────────────
if echo "$COMMAND" | grep -qiE '(DROP\s+(TABLE|DATABASE|INDEX|COLUMN)|TRUNCATE\s+TABLE)'; then
  echo "BLOCKED by pre-tool-guard: Destructive SQL detected (DROP/TRUNCATE). This violates the Global Safety Contract. Use a migration with rollback script instead." >&2
  exit 2
fi

# ── Force push to protected branches ────────────────────────────────────────
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force'; then
  echo "BLOCKED by pre-tool-guard: Force push detected. This violates the Global Safety Contract. Use a regular push or rebase workflow." >&2
  exit 2
fi

# ── Direct commit to protected branches ─────────────────────────────────────
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*\s+(main|master|develop)\b'; then
  echo "BLOCKED by pre-tool-guard: Direct push to protected branch detected. Use a pull request workflow." >&2
  exit 2
fi

# ── Skip pre-commit hooks ──────────────────────────────────────────────────
if echo "$COMMAND" | grep -qE 'git\s+commit\s+.*--no-verify'; then
  echo "BLOCKED by pre-tool-guard: Skipping pre-commit hooks (--no-verify) violates the Global Safety Contract." >&2
  exit 2
fi

# ── Infrastructure destruction ──────────────────────────────────────────────
if echo "$COMMAND" | grep -qE '(terraform\s+destroy|pulumi\s+destroy|cdk\s+destroy)'; then
  echo "BLOCKED by pre-tool-guard: Infrastructure destruction command detected. This violates the Global Safety Contract." >&2
  exit 2
fi

# ── Application deletion ───────────────────────────────────────────────────
if echo "$COMMAND" | grep -qE '(tsuru\s+app-remove|heroku\s+apps:destroy|gcloud\s+app\s+.*delete|aws\s+.*delete-stack)'; then
  echo "BLOCKED by pre-tool-guard: Application deletion command detected. This violates the Global Safety Contract." >&2
  exit 2
fi

# ── Dangerous recursive deletions ──────────────────────────────────────────
if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+/'; then
  echo "BLOCKED by pre-tool-guard: Recursive deletion from root detected (rm -rf /). This is extremely dangerous." >&2
  exit 2
fi

# ── Unsanitized eval/exec ──────────────────────────────────────────────────
if echo "$COMMAND" | grep -qE '\beval\s+\$'; then
  echo "BLOCKED by pre-tool-guard: Unsanitized eval with variable expansion detected. This violates the Global Safety Contract." >&2
  exit 2
fi

# ── Production database access without safeguards ──────────────────────────
if echo "$COMMAND" | grep -qiE '(production|prod)\b.*\b(psql|mysql|mongo|redis-cli)\b'; then
  echo "BLOCKED by pre-tool-guard: Direct production database access detected. Use a read-replica or staging environment." >&2
  exit 2
fi

# All checks passed
exit 0
