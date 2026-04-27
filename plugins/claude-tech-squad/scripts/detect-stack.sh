#!/usr/bin/env bash
# detect-stack.sh — heuristic stack detection for claude-tech-squad profile setup.
#
# Walks the project root (CLAUDE_PROJECT_DIR or pwd) and prints a newline-delimited
# list of detected stack tags to stdout. Used by /claude-tech-squad:setup to suggest
# a starting profile.
#
# Output tags: django, react, vue, typescript, mobile-rn, flutter, terraform,
#              dbt, airflow, ai-rag, postgres, celery, fastapi, flask, nextjs,
#              monorepo, python, node

set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$ROOT" 2>/dev/null || exit 0

emit() { echo "$1"; }

# Search the project root and one level deep (covers monorepos like django/+frontend/).
find_first() {
  local name="$1"
  find "$ROOT" -maxdepth 2 -name "$name" -not -path "*/node_modules/*" \
    -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/.git/*" \
    -print -quit 2>/dev/null
}

has_file() {
  [ -f "$ROOT/$1" ] || [ -n "$(find_first "$1")" ]
}

has_dir() {
  [ -d "$ROOT/$1" ] || [ -n "$(find "$ROOT" -maxdepth 3 -type d -name "$(basename "$1")" -path "*$1" -print -quit 2>/dev/null)" ]
}

grep_file() {
  local pattern="$1" basename="$2"
  local hit
  hit=$(find_first "$basename")
  [ -n "$hit" ] && grep -qiE "$pattern" "$hit"
}

# Python ecosystem
if has_file "manage.py"; then emit django; fi
if grep_file '^django' "requirements.txt"; then emit django; fi
if grep_file 'django' "pyproject.toml"; then emit django; fi
if has_file "requirements.txt" || has_file "pyproject.toml" || has_file "Pipfile"; then emit python; fi
if grep_file 'fastapi' "requirements.txt" || grep_file 'fastapi' "pyproject.toml"; then emit fastapi; fi
if grep_file '^flask' "requirements.txt" || grep_file 'flask' "pyproject.toml"; then emit flask; fi
if grep_file 'celery' "requirements.txt" || grep_file 'celery' "pyproject.toml"; then emit celery; fi

# JavaScript ecosystem
if has_file "package.json"; then
  emit node
  pkg_json=$(find_first "package.json")
  if [ -n "$pkg_json" ]; then
    if grep -qE '"react"[[:space:]]*:' "$pkg_json"; then emit react; fi
    if grep -qE '"react-native"[[:space:]]*:' "$pkg_json"; then emit mobile-rn; fi
    if grep -qE '"vue"[[:space:]]*:' "$pkg_json"; then emit vue; fi
    if grep -qE '"next"[[:space:]]*:' "$pkg_json"; then emit nextjs; fi
  fi
fi
if has_file "tsconfig.json"; then emit typescript; fi

# Mobile
if has_file "pubspec.yaml"; then emit flutter; fi

# Infra & data
if ls "$ROOT"/*.tf >/dev/null 2>&1; then emit terraform; fi
if has_file "dbt_project.yml"; then emit dbt; fi
if has_dir "airflow/dags" || has_dir "dags"; then emit airflow; fi

# AI/RAG signals
ai_hits=$(grep -rliE --include=requirements.txt --include=pyproject.toml --include=package.json \
  'openai|langchain|pgvector|anthropic|llamaindex|chromadb|pinecone' \
  "$ROOT" \
  --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=venv --exclude-dir=.git \
  2>/dev/null | head -1)
[ -n "$ai_hits" ] && emit ai-rag

# Postgres
for compose in "$ROOT/docker-compose.yml" "$ROOT/docker-compose.yaml"; do
  [ -f "$compose" ] && grep -qiE 'postgres' "$compose" && emit postgres && break
done

# Monorepo signals
if has_file "lerna.json" || has_file "pnpm-workspace.yaml" || has_file "turbo.json"; then
  emit monorepo
fi

exit 0
