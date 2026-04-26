---
name: llm-eval
description: Runs a structured LLM evaluation suite against the project's AI features. Discovers eval datasets, measures quality metrics (faithfulness, relevance, hallucination rate), runs regression against baseline, integrates as CI gate, and produces a structured eval report. Trigger with "rodar evals", "avaliar llm", "checar qualidade do ai", "llm eval", "eval suite", "regressao de prompts".
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
