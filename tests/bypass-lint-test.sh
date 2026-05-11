#!/usr/bin/env bash
# RED-STATE: expected to FAIL against current main (scripts/validate.sh does not
# yet implement bypass-pattern lint; bypass_patterns key does not exist in
# runtime-policy.yaml). AC coverage: AC9.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALIDATE="${REPO_ROOT}/scripts/validate.sh"
FIXTURE_SRC="${REPO_ROOT}/tests/fixtures/skill-with-bypass.md"
SKILLS_DIR="${REPO_ROOT}/plugins/claude-tech-squad/skills"

fail_count=0
pass() { echo "[TEST] $1: PASS"; }
fail() { echo "[TEST] $1: FAIL — $2"; fail_count=$((fail_count + 1)); }

if [ ! -f "${FIXTURE_SRC}" ]; then
  fail "fixture-present" "tests/fixtures/skill-with-bypass.md missing"
  echo "[TEST SUMMARY] failures=${fail_count}"
  exit 1
fi

# Stage the bypass fixture into the skills directory under a temp slug.
STAGED_DIR="${SKILLS_DIR}/__bypass-lint-fixture"
STAGED="${STAGED_DIR}/SKILL.md"
mkdir -p "${STAGED_DIR}"
cp "${FIXTURE_SRC}" "${STAGED}"

cleanup() {
  rm -rf "${STAGED_DIR}"
}
trap cleanup EXIT

OUT="$(mktemp)"
bash "${VALIDATE}" >"${OUT}" 2>&1
rc=$?

if [ "${rc}" -ne 0 ]; then
  pass "validate-fails-with-bypass-fixture"
else
  fail "validate-fails-with-bypass-fixture" "expected non-zero exit; validate.sh passed despite bypass fixture"
fi

if grep -qi "bypass" "${OUT}"; then
  pass "validate-output-mentions-bypass"
else
  fail "validate-output-mentions-bypass" "expected 'bypass' in validate.sh output"
fi

echo "[TEST SUMMARY] failures=${fail_count}"
[ "${fail_count}" -eq 0 ] || exit 1
exit 0
