# Gates Catalog — Phase Gates and Quality Bench

## Phase 1 (Discovery) gates

Sequential chain with gates:

1. Spawn `pm` (subagent_type: `{{pm_agent}}`) → **Gate 1: Product Definition**
2. Spawn `business-analyst` with PM output
3. Spawn `po` → **Gate 2: Scope Validation**
4. Spawn `planner` → **Gate 3: Technical Tradeoffs**
5. Spawn `architect`
6. Spawn `techlead` (subagent_type: `{{techlead_agent}}`) → **Gate 4: Architecture Direction**
7. Spawn specialist batch in parallel (from TechLead list)
   - If `ai_feature: true`: add `ai-engineer`, `rag-engineer` (if RAG detected), `prompt-engineer` to this batch.
8. Spawn quality baseline batch in parallel
9. Spawn `design-principles`
10. Spawn `test-planner`
11. Spawn `tdd-specialist` → **Gate 5: Blueprint Confirmation**
12. If `ai_feature: true`: Spawn `llm-eval-specialist` for eval plan (after blueprint) — no gate, automatic.
13. If `ai_feature: true`: Spawn `llm-safety-reviewer` for threat model (after blueprint) — no gate, automatic.
14. If `ai_feature: true`: Spawn `llm-cost-analyst` for token cost attribution and model routing analysis (after blueprint) — no gate, automatic.

## Phase 2 (Implementation) gates

Sequential with parallel batches:

1. Spawn `tdd-impl` (subagent_type: `tdd-specialist`) — write first failing tests.
2. Spawn implementation batch in parallel (only relevant workstreams): `backend-dev`, `frontend-dev`, `platform-dev`.
3. Spawn `reviewer` — review implementation. Reviewer prompt must include the implementation diff and this output contract:

   ```
   You are the Reviewer. Review for correctness, simplicity, maintainability,
   TDD compliance, lint compliance, and documentation compliance.
   Flag bugs, regressions, missing tests, and unnecessary complexity.

   **Output contract — you MUST produce ALL of the following before ending your turn:**
   1. A section `## Findings` with in-scope issues (empty if none)
   2. A section `## Pre-existing Findings` for issues found in code NOT changed by this PR — classify each as Major or Minor
   3. A final verdict line: either `APPROVED` or `CHANGES REQUESTED: <item list>`
   4. A `result_contract` block and a `verification_checklist` block

   Do NOT stop mid-turn after reading files. Do NOT chain to other agents.
   ```

   - If CHANGES REQUESTED: retry relevant impl agent(s) — **max 3 review cycles**.
   - If the 3rd review still fails: consult `fallback_matrix.squad.reviewer` and run one fallback review pass before surfacing the gate.
   - After fallback failure: emit `[Gate] Review Limit Reached` and surface to user: `[A]ccept as-is / [S]kip review / [X]Abort`.

4. Spawn `qa` — run real tests against implementation.
   - If FAIL: retry relevant impl agent(s), then re-review and re-qa — **max 2 QA cycles**.
   - If the 2nd QA cycle still fails: consult `fallback_matrix.squad.qa` and run one fallback verification pass before surfacing the gate.
   - After fallback failure: emit `[Gate] QA Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`.

5. Spawn `techlead-audit` → **Conformance Gate**: verifica workstreams cobertos, conformidade arquitetural, TDD compliance e rastreabilidade de requisitos.
   - If NON-CONFORMANT: retry impl agent(s) for each gap, then re-run reviewer → QA → techlead-audit — **max 2 conformance cycles**.
   - If the 2nd conformance cycle still fails: consult `fallback_matrix.squad.techlead-audit` and run one fallback conformance pass before surfacing the gate.
   - After fallback failure: emit `[Gate] Conformance Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`.

6. Spawn quality bench in parallel (after Conformance CONFORMANT): `security-rev`, `privacy-rev`, `perf-eng`, `access-rev`, `integ-qa`, `code-quality`.
   - If `ai_feature: true`: add `llm-safety-reviewer` to quality bench (prompt injection + tool authorization review).
   - If `ai_feature: true`: spawn `llm-eval-specialist` for eval gate (runs `/llm-eval` inline) — if eval score REGRESSED, present to user before UAT.
   - **After all bench agents return**, classify findings by severity:
     - **BLOCKING** (must fix): security vulns, PII/data leaks, privacy violations, CI-breaking lint errors, WCAG A/AA failures.
     - **WARNING** (should fix): perf regressions, non-critical accessibility, integration risks, code quality debt.
   - If BLOCKING issues: emit `[Gate] Quality Bench Blocking Issues | N findings`, spawn the relevant impl agent(s) to fix, re-run only the agents that flagged issues — **max 2 fix cycles**.
   - If a bench agent fails structurally: consult `fallback_matrix.squad.<agent-name>` before surfacing the failure gate.
   - If blocking persists after 2 cycles: emit `[Gate] Quality Bench Unresolved` → surface `[A]ccept with known issues / [X]Abort`.
   - If only WARNINGS: surface summary → `[A]ccept and advance / [F]ix before advancing`.

6b. **CodeRabbit Final Review Gate** (deterministic, tool-based — complementar ao LLM reviewer):
   - Run `bash plugins/claude-tech-squad/bin/coderabbit_gate.sh` and capture exit code.
   - Exit `0`: emit `[Gate] CodeRabbit Final Review | clean or skipped` → advance to Step 7.
   - Exit `2` (findings detected):
     - Re-spawn `reviewer` (subagent_type: `{{reviewer_agent}}`) with the CodeRabbit output as `{{coderabbit_findings}}` and instruction: "Resolva cada finding, aplique apenas o minimo necessario, retorne disposicao por finding (fixed / false-positive-ignored-because-<reason>)."
     - Re-run the gate script after reviewer finishes.
     - Repeat — **max 2 remediation cycles**.
     - If findings persist after 2 cycles: emit `[Gate] CodeRabbit Final Review Unresolved` → surface `[A]ccept with known issues (document as tech debt in SEP log) / [X]Abort`.
   - Exit `1` (CLI error/auth): emit `[Gate Error] CodeRabbit Final Review | <reason>` → surface `[R]etry / [S]kip gate (document as risk) / [X]Abort`.

7. Spawn `docs-writer`.
8. Spawn `jira-confluence` (subagent_type: `jira-confluence-specialist`).
9. Spawn `pm-uat` (subagent_type: `pm`) → **Gate 6: UAT Approval**.
   - If REJECTED: fix gaps and re-run reviewer → QA → techlead-audit → quality bench → UAT — **max 2 UAT cycles**.
   - If the 2nd UAT cycle still fails: consult `fallback_matrix.squad.pm` and run one fallback product acceptance pass before surfacing the gate.
   - After fallback failure: emit `[Gate] UAT Limit Reached` and surface to user: `[A]ccept as-is / [X]Abort`.
