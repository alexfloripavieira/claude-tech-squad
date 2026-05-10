---
name: mini-squad
description: This skill should be used when a small-to-medium feature (3–10 files, 1 module, no schema/auth/billing changes) needs a safe but cheap delivery flow — TDD test, implementation, single-lens review. Trigger with "mini squad", "/mini-squad", "feature pequena", "entrega leve", "feature simples", "rodar mini squad". Three teammates: tdd-specialist + stack-dev + code-reviewer. Mode-aware (tmux teammate or inline fallback). NOT for: 1–2 file fixes (use /bug-fix), urgent prod (use /hotfix), schema/auth/billing/cross-service work (use /implement or /squad).
user-invocable: true
---

# /mini-squad — Light Delivery Pipeline (3 teammates)

## Global Safety Contract

**Applies to every teammate. Violation requires explicit written user confirmation.**

No teammate may:
- Execute `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, destructive SQL without verified rollback
- Delete cloud resources (S3, databases, clusters, queues) in any environment
- Merge to `main`, `master`, `develop` without an approved PR
- Force-push to a protected branch
- Skip pre-commit hooks without explicit user authorization
- Remove production secrets or env vars
- Run `terraform destroy` or equivalent
- Disable auth/authz as a "quick fix"
- Execute `eval()`, dynamic shell injection, or unsanitized external input
- Apply migrations to production without verified backup

If any operation requires one of these, STOP and surface to the user.

## When to Use

- Feature scope: 3–10 files, single module/feature, no cross-service contract change
- No schema migration, no auth/authz change, no billing/payment code, no public API new endpoint
- TDD-first delivery acceptable
- User wants speed without losing safety

**Escalate to `/implement` or `/squad` if any of:**
- Auth, RBAC, session, token, or login files changed
- Billing, payment, invoice, subscription paths changed
- DB schema migration or `*.sql` migration files
- New public REST/GraphQL endpoint
- Cross-service or cross-repo coordination
- Files changed > 10 or modules > 1

## Scope Guard (preflight)

Before spawning teammates, scan target files. If ANY of the patterns below match, BLOCK and emit `[Scope Too Risky] use /implement instead | reason: <pattern>`:

| Pattern | Reason |
|---|---|
| `auth/`, `authn/`, `authz/`, `login/`, `session/`, `oauth/`, `jwt` | auth surface |
| `billing/`, `payment/`, `invoice/`, `subscription/`, `checkout/` | money path |
| `migrations/`, `migrate/`, `*.sql`, `schema.rb`, `schema.prisma` | DB schema |
| `urls.py` add new path, `routes.ts` add new public route, OpenAPI add | new public endpoint |

Operator may override with explicit `--allow-risky` flag — record reason in SEP log.

## Operator Visibility Contract

Emit:
- `[Preflight Start] mini-squad`
- `[Team Mode Resolved] mode=<teammate|inline> | tmux=<bool> | inside_tmux=<bool> | flag=<bool> | version=<x.y.z>`
- `[Tmux Auto-Launch] session=<...> | host_terminal=<...>` (when applicable)
- `[Stack Detected] <stack> | dev=<agent> | reviewer=<agent>`
- `[Scope Guard] PASS | files=<count> | risky_patterns=0` or `[Scope Too Risky] reason=<...>`
- `[Team Created] mini-squad-team` (teammate mode only)
- `[Teammate Spawned|Done|Retry] <role> | ...`
- `[Cross-Talk Audit] tdd↔dev=<count> messages` (lead mailbox dump)
- `[Test Gate] tdd=<status> | test-automation=<status>`
- `[Reviewer Verdict] <PASS|FAIL|CONDITIONAL>`
- `[Team Deleted] mini-squad-team | cleanup complete`
- `[SEP Log Written] ai-docs/.squad-log/<filename>`

## Agent Result Contract (ARC)

Every teammate MUST return:

```yaml
result_contract:
  status: PASS | FAIL | NEEDS_HUMAN
  confidence: low | medium | high
  files_touched: [<paths>]
  evidence:
    test_command: "<exact command run>"
    test_output_path: "<artifact path or inline excerpt>"
  blockers: [<short list, empty if none>]
  next_action: "<one-line handoff>"
verification_checklist:
  - "[x|FAIL] Failing test written before implementation"
  - "[x|FAIL] Test passes after implementation"
  - "[x|FAIL] Reviewer ran on changed files"
  - "[x|FAIL] No production data destroyed"
  - "[x|FAIL] tool_allowlist respected"
```

Missing either block triggers Teammate Failure Protocol.

## Inter-Teammate Cross-Talk Protocol

Required by `runtime-policy.yaml::agent_teams.cross_talk_protocol`. Enforcement is **mode-aware**: `teammate` mode opens a blocking gate on missing pairs; `inline` mode (tmux unavailable) downgrades to warning-only and the pipeline continues. Mode is resolved at preflight by `${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh`.

**Required pairs (mini-squad) — minimal:**
- `tdd-specialist` ↔ `<stack>-dev` (test contract: tdd writes failing test, dev confirms shape before implementing)

**Spawn-prompt rule:** tdd-specialist and dev spawn prompts MUST include a `peers:` block listing each other.

**Audit:** lead dumps mailbox to `sep_log.mailbox[]`. Zero outbound `SendMessage` between tdd↔dev triggers Teammate Failure Protocol with `reason: cross-talk-missing` and opens `[Gate] Cross-Talk Missing | pair: tdd-specialist↔<dev> | [R]espawn / [A]ccept / [X]Abort`.

Reviewer is single-lens by design — no cross-talk required for `code-reviewer`.

## Runtime Resilience Contract

- Retry budget: 1 retry per teammate (silent failure → 1 re-spawn → fallback → operator gate)
- Fallback matrix: `runtime-policy.yaml::fallback_matrix.mini-squad`
- Cost guardrail: token budget per `runtime-policy.yaml::cost_guardrails.mini-squad` (warn at 75%, halt at 100%)
- Doom-loop check before each retry

## Teammate Failure Protocol

A teammate has **failed silently** if it returns empty, errors, or output missing the `result_contract` block.

For every teammate:
1. Wait for structured output.
2. If empty/error/invalid: emit `[Teammate Retry] <name>`, re-spawn once with identical prompt.
3. If second attempt also fails: consult `fallback_matrix.mini-squad.<name>`. If no fallback or fallback fails, emit `[Gate] Teammate Failure | <name> failed twice` and surface `[R]etry / [S]kip / [X]Abort`.
4. Skipping the dev: STOP — no implementation possible. Skipping reviewer: log risk, allow user to override.

## Visual Reporting Contract

After each teammate returns, pipe `result_contract.metrics` JSON to `${CLAUDE_PLUGIN_ROOT}/scripts/render-teammate-card.sh`. Skip pipeline-board (3 teammates → not worth the render). Renderer failure non-fatal.

## Orchestration Contract — Mandatory Phases (CTS hard requirement)

The lead orchestrator MUST execute the four phases below in order on every
run of this skill. Skipping any phase is a contract violation. The SEP log
MUST record `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`
plus `language_policy_applied: pt-BR`. `scripts/validate.sh` greps each
dev-flow SKILL.md for the phase tags `CTS-PHASE: skill-init`, `CTS-PHASE: agent-spawn`,
`CTS-PHASE: agent-cleanup`, and `CTS-PHASE: skill-finalize` to enforce wiring.

### Phase A — Skill Branch Init (CTS-PHASE: skill-init)

Run BEFORE any `Agent(...)` call:

```bash
INIT_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/init-skill-branch.sh mini-squad)
# parse: skill_branch=<...> base_branch=<...> base_commit=<...>
```

- Exit 3 → tree dirty → emit `[Preflight Failed] main worktree dirty` and STOP.
- On success emit `[Skill Branch Created] skill_branch=<...> base_branch=<...> base_commit=<...>`.
- Persist `skill_branch` value for Phases B and D.

### Phase B — Per-Agent Spawn Wrap (CTS-PHASE: agent-spawn)

For EVERY `Agent(...)` invocation in this skill (teammate or inline mode):

```bash
SPAWN_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/spawn-agent-worktree.sh mini-squad <agent_name> <agent_id>)
# parse: path=<...> branch=<...> base=<...>
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

Emit `[Worktree Spawned] agent=<...> | path=<...> | branch=<...>`.

### Phase C — Per-Agent Cleanup (CTS-PHASE: agent-cleanup)

Immediately after the Agent returns its `result_contract` (or after the
final retry budget is exhausted, or on skill abort):

```bash
CLEANUP_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/cleanup-agent-worktree.sh <worktree_path>)
```

- Exit 0 → emit `[Worktree Cleanup] agent=<...> | merged=<true|false> | commits_ahead=<n> | branch_deleted=<branch>`.
- Exit 4 → merge conflict → emit `[Worktree Cleanup Conflict]` and open `[Gate] Worktree Merge Conflict | [R]esolve / [A]bort`. Worktree and branch are preserved until the user resolves.

This phase runs ONCE PER AGENT SPAWN and is non-skippable, even on teammate failure.

### Phase D — Skill Finalize (CTS-PHASE: skill-finalize)

After the last agent finishes, after the SEP log is written, and before
returning control to the user:

```bash
FINAL_OUT=$(bash ${CLAUDE_PLUGIN_ROOT}/bin/finalize-skill.sh "$skill_branch")
```

- Exit 0 → emit `[Skill Finalized] skill_branch=<...> | orphan_worktrees=0 | orphan_branches=0`.
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
  - `cts_phases_completed: [skill-init, agent-spawn, agent-cleanup, skill-finalize]`
  - `worktrees: [...]` (one entry per agent spawn with `path`, `branch`, `commits_ahead`, `merged`, `final_status`)


## Execution

### Step 1 — Preflight & Mode Resolution

```bash
bash ${CLAUDE_PLUGIN_ROOT}/bin/detect-team-mode.sh
```

Parse output: `mode`, `tmux`, `inside_tmux`, `flag`, `version`. Emit `[Team Mode Resolved] ...`.

If `mode=teammate` and `inside_tmux=0`: auto-launch tmux session per `runtime-policy.yaml::agent_teams.auto_launch_tmux`.

### Step 2 — Scope Guard

Read changed/target files from user prompt or staged diff. Match against Scope Guard table. If risky pattern matches, BLOCK with `[Scope Too Risky] use /implement instead | reason: <pattern>` unless `--allow-risky` provided.

Emit `[Scope Guard] PASS | files=<count> | risky_patterns=0` on pass.

### Step 3 — Stack Detection

Detect stack (`django`, `react`, `vue`, `typescript`, `python`, `javascript`, `generic`). Resolve `{{dev_agent}}` and `{{reviewer_agent}}`:

| Stack | dev | reviewer |
|---|---|---|
| django | django-backend | code-reviewer |
| react | react-developer | reviewer |
| vue | vue-developer | reviewer |
| typescript | typescript-developer | reviewer |
| python | python-developer | reviewer |
| javascript | javascript-developer | reviewer |
| generic | backend-dev | reviewer |

Emit `[Stack Detected] <stack> | dev={{dev_agent}} | reviewer={{reviewer_agent}}`.

### Step 4 — Team Create (teammate mode) or Inline Setup

**teammate mode:**
```
TeamCreate(name="mini-squad", description="Light delivery: {{feature_one_line}}")
```
Emit `[Team Created] mini-squad-team`.

**inline mode:** skip TeamCreate; spawn agents inline in main session.

### Step 5 — Spawn tdd-specialist

```
Agent(
  team_name="mini-squad",     # omit team_name if inline mode
  name="tdd-specialist",
  subagent_type="claude-tech-squad:tdd-specialist",
  prompt="""
Write the failing test for: {{feature_request}}

Files in scope: {{file_list}}
peers: [{{dev_agent}}]

Coordinate with the {{dev_agent}} teammate via SendMessage:
1. Send the proposed test signature/assertions BEFORE finalizing the test file
2. Wait for the dev's contract acknowledgement (or counter-proposal) before committing the test
3. Lock the test only after agreement

Return result_contract + verification_checklist.
"""
)
```

### Step 6 — Spawn {{dev_agent}}

```
Agent(
  team_name="mini-squad",
  name="dev",
  subagent_type="claude-tech-squad:{{dev_agent}}",
  prompt="""
Implement to satisfy the failing test from tdd-specialist.

Test file path: {{test_file_path}}
Files in scope: {{file_list}}
peers: [tdd-specialist]

BEFORE implementing:
1. Read the test contract proposal from tdd-specialist (SendMessage inbox)
2. Acknowledge or propose adjustments via SendMessage
3. Implement only after the contract is locked

Return result_contract + verification_checklist.
"""
)
```

Wait for both tdd-specialist and dev to complete. Validate cross-talk in mailbox: if `messages(tdd-specialist↔dev) == 0` and mode=teammate, open `[Gate] Cross-Talk Missing`.

### Step 7 — Test Gate (Mandatory)

### Test Gate (Mandatory)

Spawn test-automation-engineer to confirm the green build:

```
Agent(
  team_name="mini-squad",
  name="test-automation",
  subagent_type="claude-tech-squad:test-automation-engineer",
  prompt="Run the test suite. Confirm the new test passes and no regressions. Return result_contract."
)
```

If status != PASS, open `[Gate] Test Gate Failed | [R]etry / [X]Abort`.

Emit `[Test Gate] tdd=PASS | test-automation=<status>`.

### Step 8 — Reviewer Verdict

```
Agent(
  team_name="mini-squad",
  name="reviewer",
  subagent_type="claude-tech-squad:{{reviewer_agent}}",
  prompt="""
Review the diff for correctness, readability, and obvious risks.

Changed files: {{files_touched}}
Diff: {{aggregated_diff}}

Return verdict: PASS | FAIL | CONDITIONAL with structured findings.
Do NOT chain. Do NOT use Agent tool.
"""
)
```

Emit `[Reviewer Verdict] <PASS|FAIL|CONDITIONAL>`.

If FAIL: surface findings, ask user `[R]efix / [O]verride / [X]Abort`.
If CONDITIONAL: surface conditions, ask user `[A]pply / [O]verride / [X]Abort`.

### Step 9 — Team Cleanup (teammate mode)

```
TeamDelete(name="mini-squad")
```
Emit `[Team Deleted] mini-squad-team | cleanup complete`.

### Step 10 — Write SEP Log

Append a new SEP log to `ai-docs/.squad-log/mini-squad-<timestamp>.md`:

```yaml
skill: mini-squad
timestamp: <iso8601>
mode: <teammate|inline>
tokens_input: <int>
tokens_output: <int>
estimated_cost_usd: <float>
total_duration_ms: <int>
teammates:
  - name: tdd-specialist
    status: <PASS|FAIL|NEEDS_HUMAN>
    confidence: <low|medium|high>
    duration_ms: <int>
  - name: dev
    status: ...
  - name: test-automation
    status: ...
  - name: reviewer
    status: ...
mailbox:
  - from: tdd-specialist
    to: dev
    timestamp: <iso8601>
    body_hash: <sha256[:8]>
  - from: dev
    to: tdd-specialist
    timestamp: <iso8601>
    body_hash: <sha256[:8]>
gates:
  scope_guard: <PASS|BLOCKED>
  test_gate: <PASS|FAIL>
  reviewer_verdict: <PASS|FAIL|CONDITIONAL>
checkpoints_completed: [scope-guard-passed, tdd-locked, dev-implemented, test-gate-passed, reviewer-verdict-recorded]
```

Increment `ai-docs/.squad-log/.retro-counter` by 1.

Emit `[SEP Log Written] ai-docs/.squad-log/mini-squad-<timestamp>.md`.

## Output

Print a 5-line summary:
- Feature delivered: <one-line>
- Files changed: <count>
- Test added: <path>
- Reviewer verdict: <PASS|FAIL|CONDITIONAL>
- Mode used: <teammate|inline>
