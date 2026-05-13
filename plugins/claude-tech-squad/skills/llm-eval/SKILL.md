---
name: llm-eval
description: This skill should be used when AI features need structured evaluation against datasets, baselines, and quality metrics such as faithfulness, relevance, and hallucination rate. Trigger with "rodar evals", "avaliar llm", "checar qualidade do ai", "llm eval", "eval suite", "regressao de prompts". NOT for prompt-only code review (use /prompt-review).
user-invocable: true
---

# /llm-eval — LLM Evaluation Suite

Runs structured evaluations on the project's LLM features. Discovers existing eval datasets, selects the appropriate framework (RAGAS, DeepEval, PromptFoo), measures quality metrics, compares against baseline, and produces a pass/fail CI gate result.

**Core principle:** Evals are tests. A prompt change without evals is a code change without tests.

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Auto-update or rollback prompts without user confirmation — evals inform, humans decide
- Send real user data to third-party eval services without PII masking
- Overwrite existing golden datasets without creating a versioned backup first
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

## When to Use

- After any change to prompts, retrieval pipeline, embedding models, or AI logic
- Before cutting a release that includes AI features
- As a periodic quality check (weekly or per-sprint)
- When the user says: "rodar evals", "avaliar llm", "checar qualidade do ai", "llm eval", "eval suite", "regressao de prompts"

## Agent Result Contract (ARC)

The llm-eval-specialist + prompt-engineer teammates must return:

```yaml
result_contract:
  status: completed | needs_input | blocked | failed
  confidence: high | medium | low
  blockers: []                     # eval failures crossing the BLOCKING threshold
  artifacts: []                    # eval reports, scorecards, golden-set diffs
  findings:
    - severity: BLOCKING|MAJOR|MINOR
      metric: faithfulness|relevance|toxicity|bias|injection-resistance|cost
      baseline: <prior_score>
      current: <new_score>
      delta: <difference>
      evidence: <eval-output-path>
  next_action: "..."
verification_checklist:
  base_checks_passed: [completeness, accuracy, contract, scope, downstream]
  role_checks_passed: [golden_set_loaded, regression_threshold_applied, pii_masking_verified]
```

**BLOCKING thresholds (mandatory user gate):** any metric regression above `runtime-policy.yaml:eval_thresholds.<metric>_regression_max`. Defaults: faithfulness/relevance ≥ 5pp drop, toxicity any uptick, bias 3pp drop, injection-resistance any drop.

## Inter-Teammate Cross-Talk Protocol

Teammates MUST exchange `SendMessage` with each other — not only with the lead — before reporting their `result_contract`. Lead does NOT relay. Required by `runtime-policy.yaml::agent_teams.cross_talk_protocol`. Enforcement is **mode-aware**: `teammate` mode opens a blocking gate on missing pairs; `inline` mode (tmux unavailable) downgrades to warning-only and the pipeline continues. Mode is resolved at preflight by `${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh`.

**Required pairs (llm-eval) — adversarial_review / advogado do diabo:**
- `llm-eval-specialist` ↔ `llm-safety-reviewer` (capability vs safety trade-off)
- `llm-cost-analyst` ↔ `llm-eval-specialist` (cost regression vs quality regression)
- `prompt-engineer` ↔ `llm-safety-reviewer` (prompt fix vs jailbreak surface)

**Advogado do diabo:** these pairs MUST challenge assumptions, risks, alternatives, missing evidence, and quality/safety/cost trade-offs directly in pt-BR before synthesis. Record any objection that changes metric severity, rollout recommendation, prompt direction, or safety posture in the SEP log with mitigation and final decision.

**Spawn-prompt rule:** every spawn prompt MUST include a `peers:` block.

**Audit:** lead dumps mailbox to `sep_log.mailbox[]`. Zero outbound `SendMessage` to a required peer triggers the Teammate Failure Protocol with `reason: cross-talk-missing` and opens `[Gate] Cross-Talk Missing | pair: <a>↔<b> | [R]espawn / [A]ccept / [X]Abort`.

## Orchestration Contract — Mandatory Phases (CTS hard requirement)

The lead orchestrator MUST execute the four phases below in order on every
run of this skill. Skipping any phase is a contract violation. The SEP log
MUST record `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`,
`language_policy_applied: pt-BR`, and `timeouts_observed: [...]`. `scripts/validate.sh`
greps each dev-flow SKILL.md for the phase tags `CTS-PHASE: skill-init`,
`CTS-PHASE: agent-spawn`, `CTS-PHASE: agent-monitor`, `CTS-PHASE: agent-cleanup`,
and `CTS-PHASE: skill-finalize` to enforce wiring.

### Phase A — Skill Branch Init (CTS-PHASE: skill-init)

Run BEFORE any `Agent(...)` call:

```bash
INIT_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/init-skill-branch.sh llm-eval)
# parse: skill_branch=<...> base_branch=<...> base_commit=<...> watchdog_pid=<...>
```

- Exit 3 → tree dirty → emit `[Preflight Failed] main worktree dirty` and STOP.
- On success emit `[Skill Branch Created] skill_branch=<...> base_branch=<...> base_commit=<...>`.
- A background watchdog daemon is launched and its pid recorded. The watchdog
  enforces the per-agent and per-skill runtime caps as a last-resort safety
  net. THE WATCHDOG DOES NOT REPLACE THE LEAD'S MONITORING DUTY — see Phase B.1.
- Persist `skill_branch` value for Phases B and D.

### Phase B — Per-Agent Spawn Wrap (CTS-PHASE: agent-spawn)

For EVERY `Agent(...)` invocation in this skill (teammate or inline mode):

```bash
SPAWN_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/spawn-agent-worktree.sh llm-eval <agent_name> <agent_id>)
# parse: path=<...> branch=<...> base=<...> spawned_at=<epoch>
```

The Agent spawn `prompt` MUST begin with, in this exact order:

1. `language_policy.spawn_prompt_preamble` — literal text from `runtime-policy.yaml::language_policy.spawn_prompt_preamble` (pt-BR mandate).
2. The five worktree fields from `runtime-policy.yaml::agent_worktrees.spawn_prompt_inject.fields_appended_to_every_prompt`:
   - `skill_branch: <...>`
   - `worktree_path: <path>`
   - `branch: <branch>`
   - `base_commit: <base>`
   - `instruction: cd into worktree_path before any Read/Edit/Write/Bash. ...`
3. The role-specific spawn prompt body that this SKILL.md defines below.

Emit `[Worktree Spawned] agent=<...> | path=<...> | branch=<...> | spawned_at=<epoch>`.
Record `spawned_at` per agent — Phase B.1 needs it.

### Phase B.1 — Active Monitoring (CTS-PHASE: agent-monitor) — LEAD'S FIRST-LINE DUTY

This is what the orchestrator exists for. The watchdog is the OS-level
backstop; the lead is the first responder.

For every spawned agent the lead MUST:

1. **Track wall-clock since `spawned_at`.** Cap per agent is
   `runtime-policy.yaml::failure_handling.agent_max_runtime_seconds`
   (default 900s = 15 minutes). Skill-level cap is `skill_max_runtime_seconds`
   (default 7200s = 2 hours).

2. **Never block-wait indefinitely on a single agent.** Between status
   checks, do other work (other teammates' messages, gate handling) or
   sleep in short increments — never sit in an unbounded wait. If your
   runtime offers a polling primitive, use it; otherwise emit a status
   probe every ~120s.

3. **Detect stalls.** A teammate is considered stalled if EITHER:
   - wall-clock since `spawned_at` exceeds the per-agent cap, OR
   - no progress signal (SendMessage, tool call, partial output) for >
     `failure_handling.idle_seconds` (default 300s).

4. **On stall:**
   - Emit `[Teammate Timeout] agent=<...> | reason=<runtime_cap|idle> | age_seconds=<n>`.
   - Send `pkill -f -- "--agent-id <agent>@<skill>"` (or equivalent) to
     terminate the agent process.
   - Run `bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <path>`
     to remove the worktree (merge of partial work optional; merge failure
     non-fatal here).
   - Decrement retry budget. If budget remains and the failure mode is
     recoverable, respawn (Phase B again, fresh `spawned_at`). Otherwise
     open `[Gate] Teammate Failure | agent=<...> | reason=timeout |
     [R]espawn / [S]kip / [X]Abort`.
   - Append `{agent, reason, age_seconds, action}` to the SEP log's
     `timeouts_observed[]`.

5. **Never wait for human input from a subagent.** If a subagent emits a
   recovery prompt ("What should Claude do instead?"), the lead treats it
   as `reason=idle` and triggers the stall handler. Subagents MUST NOT
   block the skill on interactive prompts.

The watchdog daemon spawned in Phase A enforces the same caps independently;
if the lead misses a stall (e.g. it crashed or is itself stuck), the
watchdog kills the agent and writes a `.killed` marker. The lead MUST
inspect `ai-docs/.squad-log/.agents/*.killed` on its next tick and reflect
the kill in the SEP log.

### Phase C — Per-Agent Cleanup (CTS-PHASE: agent-cleanup)

Immediately after the Agent returns its `result_contract` (or after Phase
B.1 stall handling, or on skill abort):

```bash
CLEANUP_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <worktree_path>)
```

- Exit 0 → emit `[Worktree Cleanup] agent=<...> | merged=<true|false> | commits_ahead=<n> | branch_deleted=<branch>`.
- Exit 4 → merge conflict → emit `[Worktree Cleanup Conflict]` and open `[Gate] Worktree Merge Conflict | [R]esolve / [A]bort`. Worktree and branch are preserved until the user resolves.

This phase runs ONCE PER AGENT SPAWN (including timed-out spawns) and is non-skippable.

### Phase C.5 — SEP Log Commit (CTS-PHASE: sep-commit)

After the SEP log file is written under `ai-docs/.squad-log/<skill>-<timestamp>.md`
and BEFORE Phase D finalize, the lead MUST commit it on the skill branch.
Without this commit, finalize-skill.sh will see a dirty main worktree and
abort. The skill-active-guard hook is wired to allow these specific git
operations when scoped to `ai-docs/.squad-log/`.

```bash
CTS_LEAD_OK=1 git -C "$REPO_TOPLEVEL" add ai-docs/.squad-log/
CTS_LEAD_OK=1 git -C "$REPO_TOPLEVEL" commit -m "chore(squad-log): llm-eval SEP log"
```

The lead MUST NOT delegate this step to the user — that defeats the
orchestration contract. If the commit fails, surface a `[Gate] SEP Log
Commit Failed` instead of asking the user to run the commands manually.

### Phase D — Skill Finalize (CTS-PHASE: skill-finalize)

After the last agent finishes, after the SEP log is written and committed,
and before returning control to the user:

```bash
FINAL_OUT=$(CTS_LEAD_OK=1 bash ${CLAUDE_PLUGIN_ROOT}/bin/finalize-skill.sh "$skill_branch")
```

- Exit 0 → emit `[Skill Finalized] skill_branch=<...> | orphan_worktrees=0 | orphan_branches=0`. Sentinel is removed; watchdog exits on its next tick.
- Non-zero → STOP and surface the failing invariant to the user. Do NOT mark the skill complete.

`finalize-skill.sh` does NOT push, merge to base, or delete the skill
branch — that is the user's call.

### Cross-Talk & Language Audit (mandatory checks before SEP write)

- Inspect mailbox: every Required Pair declared in this skill's
  `## Inter-Teammate Cross-Talk Protocol` must have at least one outbound
  `SendMessage`. Empty pair → Teammate Failure with `reason: cross-talk-missing`.
- The lead's user-facing output (gate prompts, narrative reports) MUST
  follow `runtime-policy.yaml::language_policy.lead_to_user_preamble` (pt-BR).
- SEP log MUST contain:
  - `language_policy_applied: pt-BR`
  - `cts_phases_completed: [skill-init, agent-spawn, agent-monitor, agent-cleanup, skill-finalize]`
  - `worktrees: [...]` (one entry per agent spawn with `path`, `branch`, `commits_ahead`, `merged`, `final_status`)
  - `timeouts_observed: [...]` (empty list if none — explicit field required)
  - `bypasses_observed: [...]` (one entry per silenced/skipped teammate: `{agent, reason, user_decision: A|R|X, gate_emitted: true}`). EMPTY LIST IF NONE — explicit field required. Marking any agent as "BYPASSED" without a `[Gate] Reviewer Bypass Requested` and explicit user choice is a contract violation. **`user_decision` MUST come from a fresh per-gate chat reply.** Session-level preferences (e.g. "no clarifying questions" directive, autonomous-run mode, prior similar bypass) DO NOT pre-authorize the gate. See `runtime-policy.yaml::failure_handling.bypass_policy.session_preferences_do_not_authorize` and `forbidden_auto_resolutions`.



## Execution

## Teammate Failure Protocol

A teammate has **failed silently** if it returns an empty response, an error, or output that does not match the expected format for its role.

**For every teammate spawned — without exception:**

1. Wait for the teammate to return a structured output.
2. If the return is empty, an error, or structurally invalid:
   - Emit: `[Teammate Retry] <name> | Reason: silent failure — re-spawning`
   - Re-spawn the teammate once with the identical prompt.
3. If the second attempt also fails:
   - Emit: `[Gate] Teammate Failure | <name> failed twice`
   - Surface to the user:

```
Teammate <name> failed to return a valid output (attempt 1 and 2).

Options:
- [R] Retry once more with the same prompt
- [S] Skip and continue — downstream quality WILL be degraded (log the risk)
- [X] Abort the run
```

4. **Sequential teammates** (output feeds the next agent): [S] degrades ALL downstream teammates that depend on this output — warn the user explicitly before accepting skip.
5. **Parallel batch teammates**: [S] on one agent does not block the batch, but the missing output must be logged as a risk in the final report.
6. **Do NOT advance to the next step** until every teammate in the current step has returned valid output, been explicitly skipped, or the run has been aborted.

### Step 0 — Prerequisite Gate (blocking)

Before running any evaluation, verify that minimum eval infrastructure exists:

```bash
# Check for eval datasets (golden datasets, test sets)
EVAL_FILES=$(find . -name "*.jsonl" -o -name "*eval*.json" -o -name "*golden*.json" -o -name "*testset*" 2>/dev/null | grep -v node_modules | grep -v .venv | head -5)
EVAL_CONFIG=$(ls promptfooconfig.yaml .promptfoo/ ragas.yaml deepeval.yaml 2>/dev/null | head -1)
BASELINE=$(ls ai-docs/llm-eval-baseline.json 2>/dev/null)

echo "Eval datasets: ${EVAL_FILES:-NONE}"
echo "Eval config: ${EVAL_CONFIG:-NONE}"
echo "Baseline: ${BASELINE:-NONE}"
```

**If NO eval datasets AND NO eval config exist:**

```
[Gate] Prerequisite Blocker | No eval dataset or eval framework config found.

Running /llm-eval without eval data produces SETUP_REQUIRED with zero useful output.

Options:
- [B] Build prerequisites first — spawn llm-eval-specialist to create a golden dataset scaffold and eval config
- [C] Continue anyway — will produce SETUP_REQUIRED status and recommendations only
- [X] Abort — set up eval infrastructure manually first
```

If the user selects [B]:
- Skip to Step 2 (spawn llm-eval-specialist) with an explicit mandate to produce a golden dataset scaffold
- After the specialist returns, re-check prerequisites before continuing to Step 3
- Log `prerequisite_gate: scaffolded` in the SEP log

If the user selects [C]:
- Continue normally — the run will produce SETUP_REQUIRED and specialist recommendations
- Log `prerequisite_gate: overridden` in the SEP log

If the user selects [X]:
- Stop. Do not run the eval.
- Log `prerequisite_gate: aborted` in the SEP log

If eval datasets OR eval config exist, skip this gate silently.

Emit: `[Prerequisite Gate] {{passed|scaffolded|overridden|aborted}} | datasets={{count}} | config={{present|absent}}`

### Step 1 — Discover AI features and eval assets

Scan the project for:
```bash
# Prompt files
find . -name "*.prompt" -o -name "*.jinja2" -o -name "*prompt*.txt" -o -name "*system_prompt*" 2>/dev/null | grep -v node_modules | grep -v .venv | head -20

# Eval datasets
find . -name "*.jsonl" -o -name "*eval*.json" -o -name "*golden*.json" -o -name "*testset*" 2>/dev/null | grep -v node_modules | head -20

# RAG configuration
find . -name "*rag*" -o -name "*retriev*" -o -name "*embed*" 2>/dev/null | grep -E "\.(py|ts|js|yaml|yml)$" | grep -v node_modules | head -20

# Eval framework config
ls promptfooconfig.yaml .promptfoo/ ragas.yaml deepeval.yaml 2>/dev/null || echo "NO_EVAL_CONFIG"
```

Also read: `CLAUDE.md`, `README.md` to understand AI feature scope.

Record:
- Prompt files found: list with paths
- Eval datasets found: list with paths and sizes (line count for JSONL)
- Eval framework: RAGAS / DeepEval / PromptFoo / none detected
- RAG present: yes/no

### Step 1b — Detect eval framework and tools

```bash
# Python: check installed eval tools
python -c "import ragas; print('ragas:', ragas.__version__)" 2>/dev/null || echo "RAGAS_NOT_INSTALLED"
python -c "import deepeval; print('deepeval:', deepeval.__version__)" 2>/dev/null || echo "DEEPEVAL_NOT_INSTALLED"
pip show promptfoo 2>/dev/null || npx promptfoo version 2>/dev/null || echo "PROMPTFOO_NOT_INSTALLED"

# Check for LangSmith tracing
python -c "import langsmith; print('langsmith:', langsmith.__version__)" 2>/dev/null || echo "LANGSMITH_NOT_INSTALLED"
```

If no eval framework is installed, emit:
```
[Warning] No eval framework detected. Spawning llm-eval-specialist to recommend setup.
```

### Step 2 — Spawn llm-eval-specialist for eval plan

Use TeamCreate to create a team named "llm-eval-team". Then spawn each agent using the Agent tool with `team_name="llm-eval-team"` and a descriptive `name` for each agent.

```
Agent(
  subagent_type = "claude-tech-squad:llm-eval-specialist",
  team_name = "llm-eval-team",
  name = "llm-eval-specialist",
  prompt = """
## LLM Eval Planning

### Project AI Features
{{ai_features_summary}}

### Prompt Files Found
{{prompt_files_list}}

### Eval Datasets Found
{{eval_datasets_list}}

### Eval Framework Available
{{framework_or_none}}

### RAG Pipeline Present
{{rag_yes_no}}

---
You are the LLM Eval Specialist. Produce an eval plan for this project.

1. **Framework recommendation** — which eval framework fits this stack and why
2. **Metrics to measure** — from: faithfulness, answer_relevance, context_precision, context_recall, hallucination_rate, toxicity, coherence, correctness (select what applies)
3. **Eval dataset assessment** — existing datasets: are they adequate? What is missing?
4. **Golden dataset gap** — if no golden dataset exists, describe how to build one (min 50 examples, balanced coverage)
5. **Regression baseline** — what score thresholds define PASS vs FAIL for CI?
6. **LLM-as-judge config** — judge model, criteria, and calibration approach
7. **RAG eval** — if RAG present: RAGAS triad targets (faithfulness ≥ x, answer_relevance ≥ x, context_precision ≥ x)
8. **Production monitoring** — top 3 metrics to track in production with alerting thresholds

Safety constraints:
- Never send real user PII to external eval services
- Never overwrite golden datasets without versioned backup
- Do NOT chain to other agents.
"""
)
```

### Step 3 — Run available evals

Based on detected framework, run evals:

**PromptFoo (if available):**
```bash
npx promptfoo eval --config promptfooconfig.yaml --output results.json 2>/dev/null || echo "PROMPTFOO_RUN_FAILED"
```

**DeepEval (if available):**
```bash
python -m deepeval test run tests/evals/ 2>/dev/null || echo "DEEPEVAL_RUN_FAILED"
```

**RAGAS (if available and dataset exists):**
```bash
python -c "
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevance, context_precision
import json, sys

# Load eval dataset
try:
    with open('evals/dataset.jsonl') as f:
        data = [json.loads(l) for l in f]
    print(f'Dataset loaded: {len(data)} examples')
except Exception as e:
    print(f'RAGAS_DATASET_NOT_FOUND: {e}')
    sys.exit(0)
" 2>/dev/null || echo "RAGAS_RUN_FAILED"
```

If no evals can run (no framework, no dataset): record `eval_status: SETUP_REQUIRED` and skip to Step 5.

### Step 4 — Compare against baseline

Check for baseline file:
```bash
cat ai-docs/llm-eval-baseline.json 2>/dev/null || echo "NO_BASELINE"
```

If baseline exists: compare current scores against baseline thresholds.

Compute per-metric delta:
- `delta = current_score - baseline_score`
- If `delta < -0.05` for any critical metric (faithfulness, answer_relevance): mark as **REGRESSION**
- If `delta < -0.02` for any secondary metric: mark as **WARNING**
- If all deltas ≥ 0: mark as **IMPROVEMENT**

If no baseline exists: current run becomes the new baseline. Save to `ai-docs/llm-eval-baseline.json`.

### Step 5 — Spawn rag-engineer for retrieval quality (if RAG present)

If RAG was detected:

```
Agent(
  subagent_type = "claude-tech-squad:rag-engineer",
  team_name = "llm-eval-team",
  name = "rag-engineer",
  prompt = """
## RAG Quality Review

### RAG Configuration
{{rag_config_files}}

### Eval Results (if available)
{{ragas_scores}}

---
You are the RAG Engineer. Review the retrieval pipeline quality.

1. **Retrieval quality assessment** — based on available metrics or code review:
   - Is the chunking strategy appropriate for the content type?
   - Is the similarity threshold well-calibrated?
   - Is hybrid search (dense + sparse) being used where beneficial?
   - Is reranking implemented?

2. **Common failure modes** — identify top 3 likely retrieval failure modes for this pipeline

3. **Quick wins** — top 2 changes with highest expected quality improvement

4. **Eval gaps** — what retrieval-specific evals are missing?

Safety: Never send document content to external services. Analyze only configuration and code.
Do NOT chain.
"""
)
```

### Step 6 — Produce eval report

Generate structured report:

```markdown
# LLM Eval Report — YYYY-MM-DD

## Summary
- Eval status: PASS | FAIL | REGRESSION | WARNING | SETUP_REQUIRED
- Framework: {{framework}}
- Examples evaluated: {{count}}
- Metrics run: {{list}}

## Scores

| Metric | Current | Baseline | Delta | Status |
|--------|---------|----------|-------|--------|
| faithfulness | x.xx | x.xx | +/-x.xx | ✅ / ⚠️ / ❌ |
| answer_relevance | x.xx | x.xx | +/-x.xx | |
| context_precision | x.xx | x.xx | +/-x.xx | |
| hallucination_rate | x.xx | x.xx | +/-x.xx | |

## Regressions Detected
{{regression_details_or_none}}

## RAG Quality
{{rag_engineer_output_if_applicable}}

## Eval Specialist Recommendations
{{llm_eval_specialist_output}}

## CI Gate
- **Result:** PASS | FAIL
- **Blocking regressions:** {{count}}
- **Warnings:** {{count}}

## Recommended Next Steps
1. {{priority_action}}
2. {{priority_action}}
```

### Step 7 — CI gate decision

If eval_status is FAIL or REGRESSION:
```
[BLOCKED] LLM Eval Gate — {{N}} regressions detected.

Failing metrics:
{{regression_list}}

This release should not proceed until regressions are addressed.
Do you want to:
[I] Investigate regressions and re-run evals
[O] Override gate (requires written justification — logged in SEP log)
[U] Update baseline to accept current scores as new standard
```

This is a blocking gate.

If eval_status is PASS or IMPROVEMENT:
```
[LLM Eval Gate] PASS — no regressions detected.
```

### Step 8 — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-llm-eval-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
parent_run_id: null
skill: llm-eval
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [prerequisite-gate-checked, preflight-passed, eval-run, ragas-gate-checked]
fallbacks_invoked: []
prerequisite_gate: passed | scaffolded | overridden | aborted
eval_status: PASS | FAIL | REGRESSION | WARNING | SETUP_REQUIRED
framework: {{framework_or_none}}
examples_evaluated: N
regressions_detected: N
gate_override: true | false
baseline_updated: true | false
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Scores
{{score_table}}
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 9 — Save report and update baseline

Write full report to `ai-docs/llm-eval-YYYY-MM-DD.md`.

If user chose [U] (update baseline) or no baseline existed:
```bash
# Save current scores as new baseline
```
Write `ai-docs/llm-eval-baseline.json` with current scores and date.

### Step 10 — Report to user

Tell the user:
- Eval status (PASS/FAIL/REGRESSION/SETUP_REQUIRED)
- Metrics that regressed (if any) with delta values
- Top recommendation from llm-eval-specialist
- Path to saved report
- If SETUP_REQUIRED: exact next steps to install the recommended framework and create a golden dataset
