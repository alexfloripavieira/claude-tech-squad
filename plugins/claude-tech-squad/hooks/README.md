# Runtime Hooks — Mechanical Enforcers

These hooks implement the **Mechanical Enforcers** pillar of Harness Engineering. They intercept tool calls at runtime and block patterns that violate the Global Safety Contract — deterministically, without relying on prompt compliance.

## Available Hooks

### `pre-tool-guard.sh` — PreToolUse Guard

Intercepts `Bash` tool calls and blocks:

| Pattern | Violation |
|---------|-----------|
| `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` | Destructive SQL without rollback |
| `git push --force` | Force push to any branch |
| `git push ... main/master/develop` | Direct push to protected branches |
| `git commit --no-verify` | Skipping pre-commit hooks |
| `terraform destroy`, `pulumi destroy` | Infrastructure destruction |
| `tsuru app-remove`, `heroku apps:destroy` | Application deletion |
| `rm -rf /` | Dangerous recursive deletion |
| `eval $` | Unsanitized dynamic execution |
| Production database direct access | Unprotected prod DB connections |

## Installation

Add to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash plugins/claude-tech-squad/hooks/pre-tool-guard.sh"
          }
        ]
      }
    ]
  }
}
```

Or add to your user-level settings at `~/.claude/settings.json`.

## How It Works

1. Claude Code calls a Bash tool
2. The hook receives the tool input as JSON on stdin
3. The script extracts the command string
4. Each pattern is checked against the command
5. If a match is found: exit code 2 + error message to stderr (blocks the call)
6. If no match: exit code 0 (allows the call)

## Testing

```bash
# Should be blocked (exit 2):
echo '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' | bash hooks/pre-tool-guard.sh

# Should pass (exit 0):
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin feature/my-branch"}}' | bash hooks/pre-tool-guard.sh
```

## Extending

Add new patterns by appending `grep -qE` blocks to `pre-tool-guard.sh`. Each block should:
1. Match a specific dangerous pattern
2. Print a descriptive error to stderr
3. Exit with code 2

### test-gate.sh (PostToolUse)

Fires after every `Agent` tool call. Acts only when:
- the tool was `Agent`,
- the `subagent_type` is `claude-tech-squad:test-automation-engineer`,
- the active skill is in `mandatory_test_gate.skills_in_scope`.

Calls `squad-cli test-gate evaluate` and propagates the verdict via exit code:
- `0` — PASS or WARNING (continue)
- `2` — BLOCKING (halt pipeline)

See `runtime-policy.yaml#mandatory_test_gate` and `docs/superpowers/specs/2026-04-26-mandatory-test-automation-design.md`.
