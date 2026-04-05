#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="$ROOT/plugins/claude-tech-squad"
AGENTS_DIR="$PLUGIN_DIR/agents"
SKILLS_DIR="$PLUGIN_DIR/skills"

# ── JSON validity ────────────────────────────────────────────────────────────
python3 -m json.tool "$ROOT/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "$PLUGIN_DIR/.claude-plugin/plugin.json" >/dev/null

# ── Version consistency ──────────────────────────────────────────────────────
MARKETPLACE_VERSION=$(python3 -c "import json; d=json.load(open('$ROOT/.claude-plugin/marketplace.json')); print(d['plugins'][0]['version'])")
PLUGIN_VERSION=$(python3 -c "import json; d=json.load(open('$PLUGIN_DIR/.claude-plugin/plugin.json')); print(d['version'])")
MANUAL_VERSION=$(python3 -c "import re; s=open('$ROOT/docs/MANUAL.md').read(); m=re.search(r'\\*\\*Versão:\\*\\*\\s*([0-9.]+)', s); print(m.group(1) if m else '')")

if [ "$MARKETPLACE_VERSION" != "$PLUGIN_VERSION" ]; then
  echo "Version mismatch: marketplace.json ($MARKETPLACE_VERSION) != plugin.json ($PLUGIN_VERSION)"
  exit 1
fi

if [ -z "$MANUAL_VERSION" ] || [ "$MANUAL_VERSION" != "$PLUGIN_VERSION" ]; then
  echo "Version mismatch: MANUAL.md ($MANUAL_VERSION) != plugin.json ($PLUGIN_VERSION)"
  exit 1
fi

# ── Required top-level files ─────────────────────────────────────────────────
test -f "$ROOT/LICENSE"
test -f "$ROOT/CONTRIBUTING.md"
test -f "$ROOT/SECURITY.md"
test -f "$ROOT/docs/USAGE-BOUNDARIES.md"
test -f "$ROOT/docs/RELEASING.md"
test -f "$ROOT/docs/GETTING-STARTED.md"
test -f "$ROOT/docs/MANUAL.md"
test -f "$ROOT/docs/DOGFOODING.md"
test -f "$ROOT/docs/EXECUTION-TRACE.md"
test -f "$ROOT/docs/GOLDEN-RUNS.md"
test -f "$ROOT/docs/ENGINEERING-OPERATING-SYSTEM.md"
test -f "$ROOT/docs/OPERATIONAL-PLAYBOOK.md"
test -f "$ROOT/CHANGELOG.md"
test -f "$ROOT/scripts/release.sh"
test -f "$ROOT/scripts/smoke-test.sh"
test -f "$ROOT/scripts/dogfood.sh"
test -f "$ROOT/scripts/dogfood-report.sh"
test -f "$ROOT/scripts/start-golden-run.sh"
test -f "$ROOT/scripts/prepare-release-metadata.sh"
test -f "$ROOT/scripts/verify-release.sh"
test -f "$ROOT/scripts/build-release-bundle.sh"
test -f "$PLUGIN_DIR/runtime-policy.yaml"
test -f "$ROOT/fixtures/dogfooding/scenarios.json"
test -f "$ROOT/fixtures/dogfooding/layered-monolith/CLAUDE.md"
test -f "$ROOT/fixtures/dogfooding/hexagonal-billing/CLAUDE.md"
test -f "$ROOT/fixtures/dogfooding/hotfix-checkout/CLAUDE.md"
test -f "$ROOT/templates/rfc-template.md"
test -f "$ROOT/templates/service-readiness-review.md"
test -f "$ROOT/templates/golden-run-scorecard.md"
test -f "$ROOT/.github/CODEOWNERS"
test -f "$ROOT/.github/PULL_REQUEST_TEMPLATE.md"
test -f "$ROOT/.github/ISSUE_TEMPLATE/bug-report.md"
test -f "$ROOT/.github/ISSUE_TEMPLATE/workflow-change.md"
test -f "$ROOT/.github/ISSUE_TEMPLATE/config.yml"
test -f "$ROOT/ai-docs/.squad-log/.gitkeep"
test -f "$ROOT/ai-docs/dogfood-runs/.gitkeep"

# ── Required skills ──────────────────────────────────────────────────────────
REQUIRED_SKILLS=(
  discovery
  implement
  squad
  bug-fix
  security-audit
  migration-plan
  cloud-debug
  dependency-check
  factory-retrospective
  pre-commit-lint
)

for skill in "${REQUIRED_SKILLS[@]}"; do
  if [ ! -f "$SKILLS_DIR/$skill/SKILL.md" ]; then
    echo "Missing skill: $skill/SKILL.md"
    exit 1
  fi
done

# ── Required agents ──────────────────────────────────────────────────────────
REQUIRED_AGENTS=(
  accessibility-reviewer
  agent-architect
  ai-engineer
  analytics-engineer
  api-designer
  architect
  backend-architect
  backend-dev
  business-analyst
  chaos-engineer
  ci-cd
  cloud-architect
  code-quality
  compliance-reviewer
  conversational-designer
  cost-optimizer
  data-architect
  data-engineer
  dba
  design-principles-specialist
  design-system-engineer
  developer-relations
  devex-engineer
  devops
  docs-writer
  frontend-architect
  frontend-dev
  growth-engineer
  hexagonal-architect
  incident-manager
  integration-engineer
  integration-qa
  jira-confluence-specialist
  llm-eval-specialist
  ml-engineer
  mobile-dev
  monitoring-specialist
  observability-engineer
  performance-engineer
  planner
  platform-dev
  pm
  po
  privacy-reviewer
  prompt-engineer
  qa
  rag-engineer
  release
  reviewer
  search-engineer
  security-engineer
  security-reviewer
  solutions-architect
  sre
  tdd-specialist
  techlead
  tech-writer
  test-automation-engineer
  test-planner
  ux-designer
)

for agent in "${REQUIRED_AGENTS[@]}"; do
  if [ ! -f "$AGENTS_DIR/$agent.md" ]; then
    echo "Missing agent: $agent.md"
    exit 1
  fi
done

AGENT_COUNT=$(ls "$AGENTS_DIR"/*.md 2>/dev/null | wc -l)
echo "Agents found: $AGENT_COUNT"

# ── Agent frontmatter validation ─────────────────────────────────────────────
for agent_file in "$AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file" .md)
  if ! grep -q "^name:" "$agent_file"; then
    echo "Agent missing 'name:' frontmatter: $agent_name"
    exit 1
  fi
  if ! grep -q "^description:" "$agent_file"; then
    echo "Agent missing 'description:' frontmatter: $agent_name"
    exit 1
  fi
  if ! grep -q "^## Result Contract$" "$agent_file"; then
    echo "Agent missing Result Contract section: $agent_name"
    exit 1
  fi
  if ! grep -q "^## Documentation Standard — Context7 First, Repository Fallback$" "$agent_file"; then
    echo "Agent missing Context7 fallback section: $agent_name"
    exit 1
  fi
done

# ── Skill frontmatter validation ─────────────────────────────────────────────
for skill_file in "$SKILLS_DIR"/*/SKILL.md; do
  skill_name=$(basename "$(dirname "$skill_file")")
  if ! grep -q "^name:" "$skill_file"; then
    echo "Skill missing 'name:' frontmatter: $skill_name"
    exit 1
  fi
  if ! grep -q "^description:" "$skill_file"; then
    echo "Skill missing 'description:' frontmatter: $skill_name"
    exit 1
  fi
done

for skill in discovery implement squad; do
  skill_file="$SKILLS_DIR/$skill/SKILL.md"
  if ! grep -q "^## Agent Result Contract (ARC)$" "$skill_file"; then
    echo "Skill missing Agent Result Contract section: $skill"
    exit 1
  fi
  if ! grep -q "^### Preflight Gate$" "$skill_file"; then
    echo "Skill missing Preflight Gate section: $skill"
    exit 1
  fi
  if ! grep -q "^## Runtime Resilience Contract$" "$skill_file"; then
    echo "Skill missing Runtime Resilience Contract section: $skill"
    exit 1
  fi
  if ! grep -q "^### Checkpoint / Resume Rules$" "$skill_file"; then
    echo "Skill missing Checkpoint / Resume Rules section: $skill"
    exit 1
  fi
done

for key in '^version:' '^retry_budgets:' '^severity_policy:' '^fallback_matrix:' '^checkpoint_resume:' '^reliability_metrics:'; do
  if ! grep -q "$key" "$PLUGIN_DIR/runtime-policy.yaml"; then
    echo "runtime-policy.yaml missing required key matching: $key"
    exit 1
  fi
done

if ! grep -q 'skill: squad' "$SKILLS_DIR/squad/SKILL.md"; then
  echo "Squad skill missing SEP log template"
  exit 1
fi

if ! grep -q 'bash scripts/smoke-test.sh' "$ROOT/.github/workflows/validate.yml"; then
  echo "validate workflow must run scripts/smoke-test.sh"
  exit 1
fi

if ! grep -q 'bash scripts/smoke-test.sh' "$ROOT/.github/workflows/release.yml"; then
  echo "release workflow must run scripts/smoke-test.sh"
  exit 1
fi

if ! grep -q 'branches:' "$ROOT/.github/workflows/release.yml" || ! grep -q -- '- main' "$ROOT/.github/workflows/release.yml"; then
  echo "release workflow must publish from main branch"
  exit 1
fi

for release_step in 'bash scripts/verify-release.sh' 'bash scripts/build-release-bundle.sh'; do
  if ! grep -q "$release_step" "$ROOT/.github/workflows/release.yml"; then
    echo "release workflow missing step: $release_step"
    exit 1
  fi
done

if ! grep -q 'bash scripts/prepare-release-metadata.sh' "$ROOT/.github/workflows/release.yml"; then
  echo "release workflow must run scripts/prepare-release-metadata.sh"
  exit 1
fi

if ! grep -q 'paths-ignore:' "$ROOT/.github/workflows/release.yml"; then
  echo "release workflow must ignore metadata-only pushes to avoid recursion"
  exit 1
fi

for path in 'ai-docs/.squad-log/*' 'ai-docs/dogfood-runs/*'; do
  if ! grep -F -q "$path" "$ROOT/.gitignore"; then
    echo ".gitignore missing artifact ignore path: $path"
    exit 1
  fi
done

# ── Absolute Prohibitions in execution agents ────────────────────────────────
EXECUTION_AGENTS=(
  release
  sre
  backend-dev
  devops
  ci-cd
  dba
  cloud-architect
  platform-dev
  incident-manager
)

for agent in "${EXECUTION_AGENTS[@]}"; do
  agent_file="$AGENTS_DIR/$agent.md"
  if [ ! -f "$agent_file" ]; then
    echo "Execution agent file not found: $agent.md"
    exit 1
  fi
  if ! grep -q "^## Absolute Prohibitions$" "$agent_file"; then
    echo "Execution agent missing Absolute Prohibitions block: $agent"
    exit 1
  fi
done

# ── No agent self-chaining (except incident-manager) ────────────────────────
# incident-manager is the only agent authorized to use Agent tool for
# orchestration — it coordinates real-time incident response (fan-out pattern).
# All other agents must return output to the orchestrator.
SELF_CHAIN_FILES=$(grep -rl 'subagent_type' "$AGENTS_DIR"/*.md | grep -v 'incident-manager.md' || true)
if [ -n "$SELF_CHAIN_FILES" ]; then
  echo "Self-chaining detected (subagent_type in agent files):"
  echo "$SELF_CHAIN_FILES"
  exit 1
fi

AGENT_TOOL_FILES=""
for agent_file in "$AGENTS_DIR"/*.md; do
  agent_name=$(basename "$agent_file")
  if [ "$agent_name" = "incident-manager.md" ]; then
    continue
  fi

  if python3 -c "from pathlib import Path; import sys
lines = Path(sys.argv[1]).read_text().splitlines()
in_frontmatter = False
seen_start = False
agent_tool = False
for line in lines:
    if line.strip() == '---' and not seen_start:
        seen_start = True
        in_frontmatter = True
        continue
    if line.strip() == '---' and in_frontmatter:
        break
    if in_frontmatter and line.strip() == '- Agent':
        agent_tool = True
        break
raise SystemExit(0 if agent_tool else 1)" "$agent_file"
  then
    AGENT_TOOL_FILES="${AGENT_TOOL_FILES}${agent_file}"$'\n'
  fi
done

if [ -n "$AGENT_TOOL_FILES" ]; then
  echo "Only incident-manager may expose the Agent tool. Found in:"
  printf "%s" "$AGENT_TOOL_FILES"
  exit 1
fi

# ── All subagent_type references must stay inside plugin namespace ──────────
INVALID_SUBAGENT_TYPES=$(grep -rnP 'subagent_type\s*[:=]\s*"(?!claude-tech-squad:)[^"]+"' \
  "$PLUGIN_DIR/skills" \
  "$PLUGIN_DIR/agents" || true)
if [ -n "$INVALID_SUBAGENT_TYPES" ]; then
  echo "Invalid subagent_type namespace detected:"
  echo "$INVALID_SUBAGENT_TYPES"
  exit 1
fi


for trace_line in '\[Fallback Invoked\]' '\[Resume From\]' '\[Checkpoint Saved\]'; do
  if ! grep -q "$trace_line" "$ROOT/docs/EXECUTION-TRACE.md"; then
    echo "Execution trace docs missing runtime resilience line: $trace_line"
    exit 1
  fi
done

echo "claude-tech-squad validation passed (v$PLUGIN_VERSION, $AGENT_COUNT agents)"
