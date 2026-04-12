#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="$ROOT/plugins/claude-tech-squad"
AGENTS_DIR="$PLUGIN_DIR/agents"
SKILLS_DIR="$PLUGIN_DIR/skills"

bash "$ROOT/scripts/validate.sh"
bash "$ROOT/scripts/dogfood.sh"
bash "$ROOT/scripts/dogfood-report.sh" --schema-only

TMP_GOLDEN_DIR="$(mktemp -d)"
TMP_DIST_DIR="$(mktemp -d)"
TMP_RELEASE_REPO="$(mktemp -d)"
trap 'rm -rf "$TMP_GOLDEN_DIR" "$TMP_DIST_DIR" "$TMP_RELEASE_REPO"' EXIT
GOLDEN_RUNS_DIR="$TMP_GOLDEN_DIR" bash "$ROOT/scripts/start-golden-run.sh" layered-monolith smoke-test >/dev/null

LATEST_SCAFFOLD="$(find "$TMP_GOLDEN_DIR/layered-monolith" -mindepth 1 -maxdepth 1 -type d | sort | tail -1)"
[ -n "$LATEST_SCAFFOLD" ] || { echo "Smoke test failed: golden run scaffold was not created"; exit 1; }

for artifact in prompt.txt trace.md final.md metadata.yaml scorecard.md; do
  [ -f "$LATEST_SCAFFOLD/$artifact" ] || { echo "Smoke test failed: golden scaffold missing $artifact"; exit 1; }
done

CURRENT_VERSION=$(python3 -c "import json; d=json.load(open('$ROOT/plugins/claude-tech-squad/.claude-plugin/plugin.json')); print(d['version'])")
bash "$ROOT/scripts/verify-release.sh" "$CURRENT_VERSION" >/dev/null
DIST_DIR="$TMP_DIST_DIR" bash "$ROOT/scripts/build-release-bundle.sh" "$CURRENT_VERSION" >/dev/null
[ -f "$TMP_DIST_DIR/claude-tech-squad-$CURRENT_VERSION.tar.gz" ] || { echo "Smoke test failed: release archive not created"; exit 1; }
[ -f "$TMP_DIST_DIR/claude-tech-squad-$CURRENT_VERSION.sha256" ] || { echo "Smoke test failed: release checksum not created"; exit 1; }

bash -n "$ROOT/scripts/prepare-release-metadata.sh"
cp -R "$ROOT/." "$TMP_RELEASE_REPO/"
rm -rf "$TMP_RELEASE_REPO/.git" "$TMP_RELEASE_REPO/.codex" "$TMP_RELEASE_REPO/dist"
git -C "$TMP_RELEASE_REPO" init -q
git -C "$TMP_RELEASE_REPO" config user.name "smoke-test"
git -C "$TMP_RELEASE_REPO" config user.email "smoke-test@example.com"
git -C "$TMP_RELEASE_REPO" add .
git -C "$TMP_RELEASE_REPO" commit -q -m "chore: baseline release fixture"
git -C "$TMP_RELEASE_REPO" tag -a "v$CURRENT_VERSION" -m "baseline v$CURRENT_VERSION"
printf 'release smoke\n' > "$TMP_RELEASE_REPO/.release-smoke"
git -C "$TMP_RELEASE_REPO" add .release-smoke
git -C "$TMP_RELEASE_REPO" commit -q -m "fix: exercise release metadata automation"
NEXT_VERSION="$(bash "$TMP_RELEASE_REPO/scripts/prepare-release-metadata.sh")"
[ -n "$NEXT_VERSION" ] || { echo "Smoke test failed: release metadata automation did not emit a version"; exit 1; }
bash "$TMP_RELEASE_REPO/scripts/verify-release.sh" "$NEXT_VERSION" >/dev/null
grep -q "## \[$NEXT_VERSION\]" "$TMP_RELEASE_REPO/CHANGELOG.md" || {
  echo "Smoke test failed: generated changelog entry missing for $NEXT_VERSION"
  exit 1
}

AGENT_COUNT=$(find "$AGENTS_DIR" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
RESULT_CONTRACT_COUNT=$(grep -n '^## Result Contract$' "$AGENTS_DIR"/*.md | wc -l | tr -d ' ')
CONTEXT_FALLBACK_COUNT=$(grep -n '^## Documentation Standard — Context7 First, Repository Fallback$' "$AGENTS_DIR"/*.md | wc -l | tr -d ' ')

if [ "$RESULT_CONTRACT_COUNT" != "$AGENT_COUNT" ]; then
  echo "Smoke test failed: Result Contract count ($RESULT_CONTRACT_COUNT) != agent count ($AGENT_COUNT)"
  exit 1
fi

if [ "$CONTEXT_FALLBACK_COUNT" != "$AGENT_COUNT" ]; then
  echo "Smoke test failed: Context7 fallback section count ($CONTEXT_FALLBACK_COUNT) != agent count ($AGENT_COUNT)"
  exit 1
fi

for skill in discovery implement squad; do
  skill_file="$SKILLS_DIR/$skill/SKILL.md"
  grep -q '^### Preflight Gate$' "$skill_file" || { echo "Smoke test failed: missing Preflight Gate in $skill"; exit 1; }
  grep -q '^## Agent Result Contract (ARC)$' "$skill_file" || { echo "Smoke test failed: missing Agent Result Contract in $skill"; exit 1; }
  grep -q '^## Runtime Resilience Contract$' "$skill_file" || { echo "Smoke test failed: missing Runtime Resilience Contract in $skill"; exit 1; }
  grep -q '^### Checkpoint / Resume Rules$' "$skill_file" || { echo "Smoke test failed: missing Checkpoint / Resume Rules in $skill"; exit 1; }
done

for skill in bug-fix cloud-debug dependency-check dashboard factory-retrospective hotfix iac-review incident-postmortem llm-eval migration-plan multi-service onboarding pre-commit-lint prompt-review pr-review refactor release security-audit; do
  skill_file="$SKILLS_DIR/$skill/SKILL.md"
  [ -f "$skill_file" ] || { echo "Smoke test failed: SKILL.md missing for $skill"; exit 1; }
  grep -q '## Global Safety Contract' "$skill_file" || { echo "Smoke test failed: missing Global Safety Contract in $skill"; exit 1; }
  grep -q 'ai-docs/.squad-log' "$skill_file" || { echo "Smoke test failed: missing SEP log instruction in $skill"; exit 1; }
done

# ── LLM detection block in security-audit ───────────────────────────────────
grep -q 'llm_detected' "$SKILLS_DIR/security-audit/SKILL.md" || {
  echo "Smoke test failed: security-audit SKILL.md missing LLM detection block"
  exit 1
}
grep -q 'llm-safety-reviewer' "$SKILLS_DIR/security-audit/SKILL.md" || {
  echo "Smoke test failed: security-audit SKILL.md missing llm-safety-reviewer invocation"
  exit 1
}
grep -q 'BLOCKING' "$SKILLS_DIR/security-audit/SKILL.md" || {
  echo "Smoke test failed: security-audit SKILL.md missing BLOCKING severity for LLM findings"
  exit 1
}

for key in '^version:' '^retry_budgets:' '^severity_policy:' '^fallback_matrix:' '^checkpoint_resume:' '^reliability_metrics:'; do
  grep -q "$key" "$PLUGIN_DIR/runtime-policy.yaml" || {
    echo "Smoke test failed: runtime-policy.yaml missing $key"
    exit 1
  }
done

AGENT_TOOL_FILES=$(python3 -c "
from pathlib import Path
import re, sys
d = Path(sys.argv[1])
for f in sorted(d.glob('*.md')):
    c = f.read_text()
    m = re.match(r'^---\n(.*?)\n---', c, re.DOTALL)
    if m and '- Agent' in m.group(1):
        print(f)
" "$AGENTS_DIR" | sort || true)
EXPECTED_AGENT_TOOL_FILE="$AGENTS_DIR/incident-manager.md"
if [ "$AGENT_TOOL_FILES" != "$EXPECTED_AGENT_TOOL_FILE" ]; then
  echo "Smoke test failed: unexpected Agent tool exposure"
  printf '%s\n' "$AGENT_TOOL_FILES"
  exit 1
fi

if grep -rnE 'subagent_type = "code-debugger"|Spawn code-debugger|code-debugger \(root cause analysis' \
  "$ROOT/README.md" \
  "$ROOT/docs" \
  "$PLUGIN_DIR" >/dev/null 2>&1; then
  echo "Smoke test failed: stale invalid code-debugger reference found"
  exit 1
fi

grep -q '\[Preflight Start\]' "$ROOT/docs/EXECUTION-TRACE.md" || {
  echo "Smoke test failed: Execution trace docs missing preflight examples"
  exit 1
}

grep -q 'result_contract' "$ROOT/docs/EXECUTION-TRACE.md" || {
  echo "Smoke test failed: Execution trace docs missing result_contract examples"
  exit 1
}

for trace_line in '\[Fallback Invoked\]' '\[Resume From\]' '\[Checkpoint Saved\]'; do
  grep -q "$trace_line" "$ROOT/docs/EXECUTION-TRACE.md" || {
    echo "Smoke test failed: Execution trace docs missing $trace_line"
    exit 1
  }
done

grep -q 'skill: squad' "$SKILLS_DIR/squad/SKILL.md" || {
  echo "Smoke test failed: squad SEP log template missing"
  exit 1
}

# ── Reasoning Sandwich: Full enforcement ──────────────────────────────────
SELF_VERIFY_COUNT=$(grep -c '^## Self-Verification Protocol$' "$AGENTS_DIR"/*.md | grep -v ":0$" | wc -l | tr -d ' ')
if [ "$SELF_VERIFY_COUNT" != "$AGENT_COUNT" ]; then
  echo "Smoke test failed: Self-Verification Protocol count ($SELF_VERIFY_COUNT) != agent count ($AGENT_COUNT)"
  exit 1
fi

VERIFY_CHECKLIST_COUNT=$(grep -c 'verification_checklist:' "$AGENTS_DIR"/*.md | grep -v ":0$" | wc -l | tr -d ' ')
if [ "$VERIFY_CHECKLIST_COUNT" != "$AGENT_COUNT" ]; then
  echo "Smoke test failed: verification_checklist count ($VERIFY_CHECKLIST_COUNT) != agent count ($AGENT_COUNT)"
  exit 1
fi

ROLE_CHECKS_COUNT=$(grep -c 'Role-specific checks' "$AGENTS_DIR"/*.md | grep -v ":0$" | wc -l | tr -d ' ')
if [ "$ROLE_CHECKS_COUNT" != "$AGENT_COUNT" ]; then
  echo "Smoke test failed: Role-specific checks count ($ROLE_CHECKS_COUNT) != agent count ($AGENT_COUNT)"
  exit 1
fi

# Verify Pre-Execution Plan in execution agents and Analysis Plan in others
PRE_EXEC_COUNT=$(grep -c '^## Pre-Execution Plan$' "$AGENTS_DIR"/*.md | grep -v ":0$" | wc -l | tr -d ' ')
ANALYSIS_PLAN_COUNT=$(grep -c '^## Analysis Plan$' "$AGENTS_DIR"/*.md | grep -v ":0$" | wc -l | tr -d ' ')
TOTAL_PLAN=$((PRE_EXEC_COUNT + ANALYSIS_PLAN_COUNT))
if [ "$TOTAL_PLAN" != "$AGENT_COUNT" ]; then
  echo "Smoke test failed: Plan section count ($TOTAL_PLAN) != agent count ($AGENT_COUNT). Pre-Exec=$PRE_EXEC_COUNT, Analysis=$ANALYSIS_PLAN_COUNT"
  exit 1
fi

# ── Harness Engineering: Progressive Disclosure in orchestrator skills ──────
for skill in discovery implement squad; do
  grep -q 'Progressive Disclosure' "$SKILLS_DIR/$skill/SKILL.md" || {
    echo "Smoke test failed: missing Progressive Disclosure in $skill"
    exit 1
  }
done

# ── Harness Engineering: runtime policy new keys ───────────────────────────
for key in '^cost_guardrails:' '^doom_loop_detection:' '^auto_advance:' '^entropy_management:' '^tool_allowlists:' '^observability:'; do
  grep -q "$key" "$PLUGIN_DIR/runtime-policy.yaml" || {
    echo "Smoke test failed: runtime-policy.yaml missing Harness Engineering key $key"
    exit 1
  }
done

# ── Harness Engineering: PreToolUse hook exists and is executable ──────────
test -f "$PLUGIN_DIR/hooks/pre-tool-guard.sh" || {
  echo "Smoke test failed: missing hooks/pre-tool-guard.sh"
  exit 1
}
test -x "$PLUGIN_DIR/hooks/pre-tool-guard.sh" || {
  echo "Smoke test failed: hooks/pre-tool-guard.sh not executable"
  exit 1
}

# ── Harness Engineering: token tracking in ALL SEP log templates ───────────
for skill_dir in "$SKILLS_DIR"/*/; do
  skill=$(basename "$skill_dir")
  skill_file="$skill_dir/SKILL.md"
  [ -f "$skill_file" ] || continue
  grep -q 'tokens_input:' "$skill_file" || {
    echo "Smoke test failed: missing token tracking in $skill SEP log template"
    exit 1
  }
done

# ── Harness Engineering: teammate_token_breakdown in orchestrator skills ───
for skill in discovery implement; do
  grep -q 'teammate_token_breakdown:' "$SKILLS_DIR/$skill/SKILL.md" || {
    echo "Smoke test failed: missing teammate_token_breakdown in $skill SEP log template"
    exit 1
  }
done

# ── Harness Engineering: new trace lines documented ───────────────────────
for trace_line in 'Cost Warning' 'Doom Loop' 'Auto-Advanced' 'Entropy Check' 'SEP Log Written'; do
  grep -q "$trace_line" "$ROOT/docs/EXECUTION-TRACE.md" || {
    echo "Smoke test failed: EXECUTION-TRACE.md missing documentation for [$trace_line]"
    exit 1
  }
done

echo "claude-tech-squad smoke test passed"
