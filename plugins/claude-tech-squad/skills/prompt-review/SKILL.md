---
name: prompt-review
description: Reviews changes to prompt files, system prompts, and AI templates. Runs regression tests against golden examples, checks for prompt injection vulnerabilities, validates token budget, and produces a versioned diff with quality assessment. Trigger with "revisar prompt", "review de prompt", "mudei o prompt", "checar regressao de prompt", "prompt review", "validar prompt".
user-invocable: true
---

# /prompt-review — Prompt Change Review and Regression Testing

Reviews prompt changes like code changes. Diffs current vs. previous version, checks for regressions on golden examples, scans for injection vulnerabilities, validates token cost, and produces a quality verdict before the change ships.

**Core principle:** A prompt is a contract between your product and the model. Changes to it must be reviewed and tested — not just visually inspected.

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Auto-deploy changed prompts without user confirmation
- Send real user data (PII, emails, documents) to evaluate prompt quality — use synthetic examples only
- Overwrite prompt files or golden datasets without creating a backup
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

## When to Use

- After modifying any system prompt, user prompt template, or few-shot examples
- Before merging a PR that changes AI behavior
- When the user says: "revisar prompt", "review de prompt", "mudei o prompt", "checar regressao de prompt", "prompt review", "validar prompt"

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

### Step 1 — Discover prompt changes

```bash
# Git diff of prompt files
git diff HEAD -- "*.prompt" "*.jinja2" "*prompt*.txt" "*system_prompt*" "prompts/" "templates/" 2>/dev/null | head -200

# Also check staged changes
git diff --cached -- "*.prompt" "*.jinja2" "*prompt*.txt" "*system_prompt*" "prompts/" "templates/" 2>/dev/null | head -200

# List all prompt files
find . -name "*.prompt" -o -name "*.jinja2" -o -path "*/prompts/*" -name "*.txt" -o -path "*/prompts/*" -name "*.md" 2>/dev/null | grep -v node_modules | grep -v .venv | head -30
```

If no diff found, ask the user:
```
No staged or unstaged prompt changes detected.

Please specify:
1. Which prompt file changed? (path)
2. What changed? (paste old and new versions)
```

This is a blocking gate.

### Step 2 — Load golden examples

```bash
# Find golden examples for this prompt
find . -name "*golden*" -o -name "*examples*" -o -name "*testcases*" 2>/dev/null | grep -E "\.(json|jsonl|yaml|yml)$" | head -10
```

If golden examples found: read them. These are the regression test cases.

If not found: emit `[Warning] No golden examples found for regression testing. Quality assessment will be analytical only.`

### Step 3 — Spawn prompt-engineer for review and regression

Use TeamCreate to create a team named "prompt-review-team". Then spawn the agent using the Agent tool with `team_name="prompt-review-team"` and a descriptive `name`.

```
Agent(
  subagent_type = "claude-tech-squad:prompt-engineer",
  team_name = "prompt-review-team",
  name = "prompt-engineer",
  prompt = """
## Prompt Change Review

### Prompt Diff
{{prompt_diff}}

### Current Prompt (full)
{{current_prompt}}

### Previous Prompt (full, from git)
{{previous_prompt}}

### Golden Examples (if available)
{{golden_examples_or_none}}

### Model and Use Case
{{model_name}} — {{use_case_description}}

---
You are the Prompt Engineer. Perform a thorough review of this prompt change.

1. **Behavioral diff** — what does this change actually do to model behavior?
   - Intent: what was the author trying to achieve?
   - Risk: what could go wrong with this change?
   - Scope: is the change narrowly targeted or broadly impactful?

2. **Regression test** — for each golden example, predict whether the output would:
   - Remain the same (STABLE)
   - Improve (BETTER)
   - Degrade (REGRESSION)
   - Become unpredictable (RISK)

3. **Injection vulnerability check** — does the new prompt:
   - Properly escape or delimit user-provided content?
   - Prevent the user from overriding system instructions?
   - Guard against indirect prompt injection (via retrieved documents, tool outputs)?
   - Leak system prompt content via simple requests?

4. **Token cost impact** — estimate token delta between old and new prompt (input tokens per call)

5. **Model compatibility** — does this prompt rely on behaviors specific to one model? (GPT-4o patterns, Claude-specific formatting, etc.)

6. **Few-shot quality** — if few-shot examples were changed: are new examples diverse, representative, and free of bias?

7. **Verdict:** APPROVED | CHANGES REQUESTED | BLOCKED (injection risk)

Safety constraints:
- Use only provided golden examples — do not call external LLM APIs
- Flag any PII found in golden examples as a finding
- Do NOT chain to other agents
"""
)
```

### Step 4 — Security scan for prompt injection

Scan prompt files for common injection vulnerability patterns:

```bash
# Check for unescaped user input interpolation
grep -rn --include="*.prompt" --include="*.jinja2" --include="*.py" --include="*.ts" \
  -E '\{user_input\}|\{message\}|\{query\}|\{content\}' . \
  --exclude-dir=node_modules --exclude-dir=.venv 2>/dev/null | head -20

# Check for instruction boundary markers
grep -rn --include="*.prompt" --include="*.jinja2" \
  -E "(SYSTEM:|HUMAN:|ASSISTANT:|<\|im_start\|>|<\|im_end\|>)" . \
  --exclude-dir=node_modules 2>/dev/null | head -10
```

Also check if retrieved documents are interpolated without sanitization (indirect prompt injection vector):
```bash
grep -rn --include="*.py" --include="*.ts" --include="*.js" \
  -E '(context|document|chunk|retrieved)\s*[+]=|f".*\{(context|document|chunk)\}"' . \
  --exclude-dir=node_modules --exclude-dir=.venv 2>/dev/null | head -20
```

### Step 5 — Token budget analysis

Count tokens in changed prompts (approximate):
```bash
# Word-based approximation (tokens ≈ words / 0.75)
wc -w prompts/*.prompt 2>/dev/null || wc -w $(find . -name "*.prompt" | head -5) 2>/dev/null || echo "TOKEN_COUNT_UNAVAILABLE"
```

If token count increased by > 20%: emit `[Cost Warning] Prompt grew by {{N}} tokens. Estimated cost increase: {{estimate}} per 1M calls.`

### Step 6 — Produce review report

```markdown
# Prompt Review — YYYY-MM-DD

## Changed File(s)
{{prompt_files_changed}}

## Behavioral Summary
{{what_changed_in_plain_language}}

## Regression Test Results

| Example | Predicted Impact | Risk |
|---------|-----------------|------|
| {{example_1}} | STABLE / BETTER / REGRESSION / RISK | {{reason}} |

## Security Assessment

| Check | Result |
|-------|--------|
| User input escaping | SAFE / RISK |
| Instruction override prevention | SAFE / RISK |
| Indirect injection (retrieved docs) | SAFE / RISK |
| System prompt leakage | SAFE / RISK |

## Token Cost Impact
- Token delta: +/-N tokens per call
- Cost impact at 1M calls: {{estimate}}

## Verdict
**{{APPROVED | CHANGES REQUESTED | BLOCKED}}**

{{reason_and_required_changes_if_not_approved}}
```

### Step 7 — Gate

If verdict is BLOCKED: present to user and halt. Prompt must not be merged until injection risk is fixed.

If verdict is CHANGES REQUESTED: present changes to user. User decides whether to fix and re-run or proceed.

If verdict is APPROVED:
```
[Prompt Review] APPROVED — no regressions or injection risks detected.
```

### Step 8 — Version the prompt

If prompt is approved: create a versioned snapshot.

```bash
PROMPT_VERSION_DIR="ai-docs/prompt-versions/$(date +%Y-%m-%d)"
mkdir -p "$PROMPT_VERSION_DIR"
# Copy each changed prompt file to versioned directory
```

Emit: `[Prompt Versioned] Snapshot saved to ai-docs/prompt-versions/{{date}}/`

### Step 9 — Write SEP log (SEP Contrato 1)

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-prompt-review-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: prompt-review
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [preflight-passed, review-complete, verdict-issued]
fallbacks_invoked: []
verdict: APPROVED | CHANGES_REQUESTED | BLOCKED
injection_risks_found: N
regression_risks_found: N
token_delta: +/-N
prompt_versioned: true | false
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`

### Step 10 — Report to user

Tell the user:
- Verdict (APPROVED / CHANGES REQUESTED / BLOCKED)
- Behavioral summary in plain language
- Any injection risks found
- Any regression risks on golden examples
- Token cost impact
- Path to versioned prompt snapshot (if approved)
