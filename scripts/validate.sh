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

if [ "$MARKETPLACE_VERSION" != "$PLUGIN_VERSION" ]; then
  echo "Version mismatch: marketplace.json ($MARKETPLACE_VERSION) != plugin.json ($PLUGIN_VERSION)"
  exit 1
fi

# ── Required top-level files ─────────────────────────────────────────────────
test -f "$ROOT/LICENSE"
test -f "$ROOT/docs/USAGE-BOUNDARIES.md"
test -f "$ROOT/docs/RELEASING.md"
test -f "$ROOT/docs/GETTING-STARTED.md"
test -f "$ROOT/docs/MANUAL.md"
test -f "$ROOT/docs/EXECUTION-TRACE.md"
test -f "$ROOT/docs/OPERATIONAL-PLAYBOOK.md"
test -f "$ROOT/CHANGELOG.md"
test -f "$ROOT/scripts/release.sh"

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

# ── No project-specific residue ──────────────────────────────────────────────
if rg -n "\bA1\b|Fifi|Wooba|Cangooroo|Compozy|Botpress" \
  "$ROOT/README.md" \
  "$ROOT/docs" \
  "$PLUGIN_DIR" >/dev/null 2>&1; then
  echo "Found project-specific residue in plugin repository."
  exit 1
fi

echo "claude-tech-squad validation passed (v$PLUGIN_VERSION, $AGENT_COUNT agents)"
