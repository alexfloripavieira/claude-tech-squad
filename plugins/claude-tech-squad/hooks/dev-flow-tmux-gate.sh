#!/usr/bin/env bash
# dev-flow-tmux-gate.sh — UserPromptSubmit hook.
#
# When the user invokes a dev-flow skill (mini-squad, squad, discovery,
# implement, refactor, tech-debt-audit, pentest-deep, etc.) AND tmux is
# installed AND we are NOT inside a tmux session AND the experimental
# Agent Teams flag is NOT set AND the user has not opted into inline
# mode, BLOCK the prompt and present two choices:
#
#   1. Reinicializar — paste a shell command that relaunches claude
#      inside a fresh tmux session with the flag, plus a ready-to-paste
#      prompt for the chat once claude is back.
#   2. Continuar inline — set CTS_INLINE=1 (or rerun with no tmux change).
#
# Stdin: Claude Code passes JSON {"prompt": "...", ...}.
# Exit 0  = allow.
# Exit 2  = block, stderr shown to user.

set -u

INPUT=$(cat)
PROMPT=$(printf '%s' "$INPUT" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('prompt',''))" 2>/dev/null \
  || echo "")

if [ -z "$PROMPT" ]; then
  exit 0
fi

# Dev-flow skills that orchestrate teammates. Matches "/mini-squad",
# "/claude-tech-squad:squad", "/squad ...", etc.
DEV_FLOW_RE='(^|[[:space:]])/(claude-tech-squad:)?(mini-squad|squad|discovery|implement|refactor|tech-debt-audit|pentest-deep|incident-postmortem|llm-eval|iac-review|pr-review|from-ticket|multi-service|hotfix|bug-fix|inception|onboarding|security-audit|migration-plan|prompt-review)([[:space:]]|$)'

if ! printf '%s' "$PROMPT" | grep -qE "$DEV_FLOW_RE"; then
  exit 0
fi

# User opted into inline mode for this session.
if [ "${CTS_INLINE:-}" = "1" ]; then
  exit 0
fi

# tmux not installed -> nothing to enforce; fall through to inline.
if ! command -v tmux >/dev/null 2>&1; then
  exit 0
fi

# Already inside tmux + flag set -> all good.
if [ -n "${TMUX:-}" ] && [ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" = "1" ]; then
  exit 0
fi

SESSION="cts-$(date +%s)"
PROMPT_ESCAPED=$(printf '%s' "$PROMPT" | sed "s/'/'\\\\''/g")

cat >&2 <<EOF
[CTS Gate] Skill de dev-flow detectada fora de tmux teammate mode.

tmux instalado neste device, mas claude rodando sem CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
e/ou fora de uma sessão tmux. Sem isso teammates rodam em mode=inline
(sem painéis, sem cross-talk adversarial bloqueante).

Escolha uma opção:

────────────────────────────────────────────────────────────────────────
[A] Reinicializar dentro de tmux (recomendado)

   Saia deste claude (Ctrl+D) e rode:

      CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 \\
        tmux new-session -A -s ${SESSION} claude

   Depois, cole no chat:

      ${PROMPT}

────────────────────────────────────────────────────────────────────────
[B] Continuar inline (sem teammates separados, sem tmux)

   Saia, exporte e relance:

      export CTS_INLINE=1
      claude

   Ou nesta sessão atual: setar a env não afeta o claude já em execução,
   então a escolha B exige relançar mesmo (sem tmux, com CTS_INLINE=1).

────────────────────────────────────────────────────────────────────────

Prompt original preservado acima ([A] copia-e-cola pronto).
EOF

exit 2
