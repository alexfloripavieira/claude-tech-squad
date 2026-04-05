---
name: onboarding
description: Bootstraps a new project or repository for squad usage. Creates ai-docs/ structure, generates a CLAUDE.md template from the detected stack, configures SEP artifacts, runs initial security and dependency audits, and produces a project health baseline. Trigger with "onboarding do projeto", "configurar squad", "bootstrap projeto", "setup squad", "iniciar projeto com squad".
user-invocable: true
---

# /onboarding — Project Bootstrap for Squad Usage

## Global Safety Contract

**This contract applies to every agent and operation in this workflow. Violating it requires explicit written user confirmation.**

No agent may, under any circumstances:
- Overwrite or delete existing `CLAUDE.md`, `.gitignore`, or CI configuration files — only create if absent or append with user confirmation
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, or any destructive SQL
- Delete cloud resources (S3 buckets, databases, clusters, queues) in any environment
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push (`git push --force`) to any protected branch
- Skip pre-commit hooks (`git commit --no-verify`) without explicit user authorization
- Commit or push files that contain secrets, tokens, or credentials
- Execute `eval()`, dynamic shell injection, or unsanitized external input in commands

If any operation requires one of these actions, STOP and surface the decision to the user before proceeding.

Sets up a new repository to work with `claude-tech-squad`. Detects the stack, creates the artifact structure, generates a `CLAUDE.md` template, and produces an initial health baseline so the first `/discovery` or `/squad` run starts with full context.

## When to Use

- First time running the squad in a repository
- Migrating an existing project to use the squad workflow
- When the user says: "onboarding do projeto", "configurar squad", "bootstrap projeto", "setup squad", "iniciar projeto com squad"

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

### Step 1 — Detect project stack

Read the following files to determine the stack:

- `package.json`, `yarn.lock`, `pnpm-lock.yaml` → JavaScript / Node / frontend framework
- `pyproject.toml`, `requirements.txt`, `Pipfile` → Python
- `pom.xml` → Java / Maven
- `build.gradle` → Java / Kotlin / Gradle
- `go.mod` → Go
- `Cargo.toml` → Rust
- `composer.json` → PHP
- `Gemfile` → Ruby
- `docker-compose.yml`, `Dockerfile` → containerized
- `.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml` → CI/CD

Also check for:
- `README.md` — project description, setup instructions
- Existing `CLAUDE.md` — already configured?
- Existing `ai-docs/` — already has artifacts?

**LLM/AI detection — scan for these patterns:**

```bash
# Python LLM libraries
grep -r "openai\|anthropic\|langchain\|llama.index\|llamaindex\|pgvector\|chromadb\|pinecone\|weaviate\|cohere\|tiktoken\|transformers\|sentence.transformers\|ragas\|deepeval\|promptfoo" \
  requirements.txt pyproject.toml Pipfile 2>/dev/null | head -10

# JavaScript/TypeScript LLM libraries
grep -r "\"openai\"\|\"@anthropic-ai\"\|\"langchain\"\|\"llamaindex\"\|\"pgvector\"\|\"pinecone\"\|\"weaviate\"\|\"cohere\"\|\"tiktoken\"\|\"ai\"\|\"@ai-sdk" \
  package.json 2>/dev/null | head -10

# Prompt files
find . -name "*.prompt" -o -name "*.jinja2" -o -name "system-prompt*" -o -name "prompts/*.txt" 2>/dev/null | head -10
```

If any LLM library is found: set `llm_detected=true`. Record: which libraries, whether prompt files exist.

Record: primary languages, frameworks, databases, CI/CD platform, container setup, `llm_detected` flag.

### Step 2 — Assess current state

```bash
# Check git history depth
git log --oneline | wc -l 2>/dev/null || echo "0"

# Check existing test setup
ls tests/ test/ spec/ __tests__/ 2>/dev/null | head -5 || echo "NO_TESTS_DIR"

# Check existing CI
ls .github/workflows/ .gitlab-ci.yml Jenkinsfile 2>/dev/null || echo "NO_CI"
```

Record: repository age (commit count), test coverage presence, CI/CD presence.

### Step 3 — Create artifact structure

```bash
mkdir -p ai-docs/.squad-log
```

**Security: protect squad logs from git exposure.** SEP logs may contain security findings, CVEs, and internal vulnerability details. Ensure `.squad-log/` is never committed:

```bash
# Check if .gitignore exists and already covers squad-log
grep -q "\.squad-log" .gitignore 2>/dev/null || echo "NEEDS_GITIGNORE_ENTRY"
```

If `.gitignore` does not already contain `ai-docs/.squad-log/`, append:

```
# Squad execution logs — may contain security findings
ai-docs/.squad-log/
```

Emit: `[Security] ai-docs/.squad-log/ added to .gitignore — prevents CVE/finding exposure`

Create `ai-docs/README.md`:

```markdown
# Squad Artifacts

This directory contains outputs from `claude-tech-squad` skill runs.

## Structure

- `.squad-log/` — SEP execution logs (auto-generated, one file per skill run)
- `security-remediation-*.md` — open security findings with checkboxes
- `dependency-remediation-*.md` — open dependency findings with checkboxes
- `{feature}/blueprint.md` — discovery & blueprint documents
- `factory-retrospective-*.md` — process retrospective reports

Generated by `/claude-tech-squad:onboarding` on {{date}}.
```

### Step 4 — Generate CLAUDE.md template

If `CLAUDE.md` does not already exist, create it with the detected stack:

```markdown
# CLAUDE.md

## Project Overview

{{project_name}} — {{one_line_description_from_readme}}

**Stack:** {{detected_stack}}
**CI/CD:** {{detected_ci}}
**Container:** {{yes/no}}

## Essential Commands

```bash
# Development
{{start_command}}

# Testing
{{test_command}}

# Lint
{{lint_command}}

# Build
{{build_command}}

# Database migrations (if applicable)
{{migrate_command}}
```

## Architecture

{{brief_architecture_from_readme_or_inferred}}

## Key Conventions

- [Add project-specific conventions here]

## Workflow Rules

- Bug fixes (1–2 files): fix directly or use `/claude-tech-squad:bug-fix`
- Features (3+ files): use `/claude-tech-squad:squad`
- Production emergency: use `/claude-tech-squad:hotfix`
- Never commit or push without explicit authorization
```

**If `llm_detected=true`, append the following section to the generated `CLAUDE.md`:**

```markdown
## AI / LLM Workflow Rules

This project uses LLM/AI libraries: {{detected_llm_libraries}}.

### Mandatory gates before release

- **Before any release that includes AI changes:** run `/claude-tech-squad:llm-eval`
  This runs the eval suite (RAGAS, DeepEval, PromptFoo), compares against baseline, and blocks release if quality regresses.

- **Before merging any PR that changes a prompt file:** run `/claude-tech-squad:prompt-review`
  This validates regression on golden examples, scans for prompt injection, and estimates token cost delta.

### Recommended workflow for AI features

1. `/claude-tech-squad:discovery` — shape the AI feature with AI-aware specialists (ai-engineer, rag-engineer, llm-eval-specialist)
2. `/claude-tech-squad:implement` — TDD-first implementation
3. `/claude-tech-squad:prompt-review` — before merging prompt changes
4. `/claude-tech-squad:llm-eval` — before release
5. `/claude-tech-squad:release` — cut the release

### Detected AI dependencies

{{detected_llm_libraries_baseline}}
```

Emit: `[AI Detected] LLM libraries found — AI workflow rules added to CLAUDE.md`

If `CLAUDE.md` already exists, read it and emit:
```
[Onboarding] CLAUDE.md already exists — skipping template generation.
Review and update it manually if needed.
```

### Step 5 — Run initial security audit

Use TeamCreate to create a team named "onboarding-team". Then spawn the agent using the Agent tool with `team_name="onboarding-team"` and a descriptive `name`.

Invoke `/security-audit` inline:

```
Agent(
  subagent_type = "claude-tech-squad:security-reviewer",
  team_name = "onboarding-team",
  name = "security-reviewer",
  prompt = """
Run a quick security baseline scan on this project.
Focus on: hardcoded secrets, known CVEs in dependencies, obvious injection risks.
Return findings categorized by severity. Keep it brief — this is a baseline, not a full audit.
Do NOT write remediation files yet. Return findings only.
"""
)
```

### Step 6 — Run initial dependency check and generate baseline

```bash
pip-audit --format=text 2>/dev/null || echo "PYTHON_AUDIT_NOT_AVAILABLE"
npm audit 2>/dev/null || echo "JS_AUDIT_NOT_AVAILABLE"
```

**Generate a dependency baseline listing all detected packages with known outdating flags:**

```bash
# Python: list installed packages with versions
pip list --format=columns 2>/dev/null | head -30 || echo "PIP_NOT_AVAILABLE"

# Node: list top-level dependencies with versions
npm list --depth=0 2>/dev/null | head -30 || echo "NPM_NOT_AVAILABLE"
```

**If `llm_detected=true`, additionally flag known LLM library versioning risks:**

- `openai` < 1.0: breaking API changes in v1.0 — upgrade required
- `langchain` < 0.2: frequent breaking changes — pin exact version and review changelog before upgrading
- `anthropic` < 0.20: streaming API changes — verify SDK version matches model API version
- `transformers` without pinned version: model loading behavior changes across minor versions — pin to tested version

Record: critical CVEs count, major updates count, LLM dependency flags.

### Step 7 — Generate project health baseline

Produce a structured baseline report:

```markdown
# Project Health Baseline — {{date}}

## Stack
- Languages: {{list}}
- Frameworks: {{list}}
- Databases: {{list}}
- CI/CD: {{platform or none}}
- Containerized: yes/no

## Repository State
- Commits: {{count}}
- Test setup: {{present/absent}}
- CLAUDE.md: {{created/existing/skipped}}
- ai-docs/: {{created}}

## Security Baseline
- Critical findings: N
- High findings: N
- Tools available: {{list}}

## Dependency Baseline
- Critical CVEs: N
- Major updates pending: N
- LLM libraries detected: {{llm_detected}} — {{detected_llm_libraries or "none"}}
- LLM version flags: {{llm_version_flags or "none"}}

## Recommended First Steps
1. {{top priority — e.g. "Fix N critical CVEs before first sprint"}}
2. {{e.g. "Add test suite — no tests directory found"}}
3. {{e.g. "Configure CI/CD — no pipeline detected"}}
```

### Step 8 — Write SEP log (SEP Contrato 1)

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-onboarding-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: onboarding
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: {{architecture_style}}
checkpoints: [preflight-passed, claude-md-generated, onboarding-complete]
fallbacks_invoked: []
stack: {{primary_stack}}
claude_md_created: true | false
security_findings_critical: N
dependency_cves_critical: N
---

## Baseline Summary
{{one_paragraph}}
```

Write the health baseline to `ai-docs/project-baseline-{{date}}.md`.

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
Emit: `[Onboarding Complete] ai-docs/ structure created, CLAUDE.md ready`

### Step 9 — Report to user

Tell the user:
- Stack detected
- Whether CLAUDE.md was created or already existed
- Critical security findings (if any) — recommend running `/security-audit` for full report
- Critical CVEs (if any) — recommend running `/dependency-check` for full report
- Path to the health baseline
- Suggested next command (`/squad` or `/discovery`)
