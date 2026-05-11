#!/usr/bin/env bash
# RED-STATE: expected to FAIL against current main (bin/validate-sep-log.py does
# not yet exist; hooks/sep-log.schema.json does not yet exist).
# AC coverage: AC3, AC4, AC5 (AC5 partially — finalize integration tested separately).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATOR="${REPO_ROOT}/plugins/claude-tech-squad/bin/validate-sep-log.py"
TMP="$(mktemp -d -t cts-sep-schema-test.XXXXXX)"

fail_count=0
pass() { echo "[TEST] $1: PASS"; }
fail() { echo "[TEST] $1: FAIL — $2"; fail_count=$((fail_count + 1)); }

cleanup() { rm -rf "${TMP}"; }
trap cleanup EXIT

if [ ! -f "${VALIDATOR}" ]; then
  fail "validator-present" "validate-sep-log.py missing at ${VALIDATOR}"
  echo "[TEST SUMMARY] failures=${fail_count}"
  exit 1
fi

# ----- Fixture 1: valid SEP log frontmatter -----
cat >"${TMP}/valid.md" <<'EOF'
---
schema_version: 1
run_id: test-run-1
skill: discovery
status: completed
tokens_input: 12345
tokens_output: 6789
estimated_cost_usd: 0.042
total_duration_ms: 18000
worktrees: []
language_policy_applied: pt-BR
---

# SEP body
EOF

OUT1="$(mktemp)"
python3 "${VALIDATOR}" "${TMP}/valid.md" >"${OUT1}" 2>&1
rc=$?
if [ "${rc}" -eq 0 ]; then
  pass "fixture-1-valid-exits-zero"
else
  fail "fixture-1-valid-exits-zero" "expected exit 0, got ${rc}; output: $(tr '\n' '|' <"${OUT1}")"
fi

# ----- Fixture 2: missing tokens_input -----
cat >"${TMP}/missing-tokens.md" <<'EOF'
---
schema_version: 1
run_id: test-run-2
skill: discovery
status: completed
tokens_output: 6789
estimated_cost_usd: 0.042
total_duration_ms: 18000
worktrees: []
language_policy_applied: pt-BR
---
EOF

OUT2="$(mktemp)"
python3 "${VALIDATOR}" "${TMP}/missing-tokens.md" >"${OUT2}" 2>&1
rc=$?
if [ "${rc}" -eq 5 ]; then
  pass "fixture-2-missing-tokens-exits-5"
else
  fail "fixture-2-missing-tokens-exits-5" "expected exit 5, got ${rc}"
fi

if grep -q "\[SEP Schema Violation\]" "${OUT2}" && grep -q "tokens_input" "${OUT2}"; then
  pass "fixture-2-error-mentions-tokens_input"
else
  fail "fixture-2-error-mentions-tokens_input" "expected [SEP Schema Violation] + tokens_input in stderr, got: $(tr '\n' '|' <"${OUT2}")"
fi

# ----- Fixture 3: wrong type worktrees -----
cat >"${TMP}/wrong-type.md" <<'EOF'
---
schema_version: 1
run_id: test-run-3
skill: discovery
status: completed
tokens_input: 1
tokens_output: 1
estimated_cost_usd: 0.001
total_duration_ms: 100
worktrees: "not-a-list"
language_policy_applied: pt-BR
---
EOF

OUT3="$(mktemp)"
python3 "${VALIDATOR}" "${TMP}/wrong-type.md" >"${OUT3}" 2>&1
rc=$?
if [ "${rc}" -eq 5 ]; then
  pass "fixture-3-wrong-type-exits-5"
else
  fail "fixture-3-wrong-type-exits-5" "expected exit 5, got ${rc}"
fi

if grep -q "worktrees" "${OUT3}"; then
  pass "fixture-3-error-mentions-worktrees"
else
  fail "fixture-3-error-mentions-worktrees" "expected 'worktrees' in error output"
fi

echo "[TEST SUMMARY] failures=${fail_count}"
[ "${fail_count}" -eq 0 ] || exit 1
exit 0
