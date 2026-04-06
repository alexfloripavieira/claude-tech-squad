# Skill Contract

Every skill in `plugins/claude-tech-squad/skills/` must implement this contract. Skills that omit required blocks break preflight validation, SEP log output, or gate behavior.

---

## File location

Each skill lives in its own directory:

```
plugins/claude-tech-squad/skills/<skill-name>/SKILL.md
```

Examples:
```
plugins/claude-tech-squad/skills/discovery/SKILL.md
plugins/claude-tech-squad/skills/implement/SKILL.md
plugins/claude-tech-squad/skills/squad/SKILL.md
```

---

## Required frontmatter

```yaml
---
name: <skill-slug>
description: <one-line description visible in the Claude Code skill picker>
---
```

---

## Required blocks

### 1. Global Safety Contract

Placed at the top of every skill, before any phase definition. Applies to every teammate spawned by the workflow. Cannot be overridden by urgency or user instructions.

The contract prohibits all teammates from executing:
- Destructive SQL (`DROP TABLE`, `DROP DATABASE`, `TRUNCATE`) without rollback script and explicit user confirmation
- Cloud resource deletion in production
- Any application destruction command (`tsuru app-remove`, `heroku apps:destroy`, or equivalent)
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push to any protected branch
- Removal of secrets or environment variables from production
- Infrastructure destruction via `terraform destroy` or equivalent
- Disabling or bypassing authentication/authorization as a workaround
- Skipping pre-commit hooks without explicit user authorization
- Dynamic code execution with unsanitized external input
- Applying migrations to production without verifying a backup first

If any teammate believes a task requires one of these actions, it must STOP and surface the decision to the user.

### 2. Operator Visibility Contract

Every skill emits a standard set of trace lines. These lines are the observable proof that the pipeline executed correctly. A run without these lines is not a valid run.

Required trace lines:

```
[Preflight Start] <workflow-name>
[Preflight Warning] <summary>          ← only when a non-blocking issue is detected
[Preflight Passed] <workflow-name> | execution_mode=<mode> | architecture_style=<style> | lint_profile=<profile> | docs_lookup_mode=<mode> | runtime_policy=<version>
[Team Created] <team-name>
[Teammate Spawned] <role> | pane: <name>
[Teammate Done] <role> | Output: <one-line summary>
[Teammate Retry] <role> | Reason: <failure>
[Fallback Invoked] <failed-role> -> <fallback-subagent> | Reason: <summary>
[Resume From] <workflow-name> | checkpoint=<checkpoint>
[Checkpoint Saved] <workflow-name> | cursor=<checkpoint>
[Gate] <gate-name> | Waiting for user input
[Batch Spawned] <phase> | Teammates: <comma-separated names>
[AI Detected] <summary>                ← only when LLM/AI code is found in the repo
```

### 3. Preflight block

Executed before any agent is spawned. Detects execution context and emits `[Preflight Passed]`.

The preflight must detect and report:
- `execution_mode`: `inline` (default) or `tmux` (when `CLAUDE_CODE_TEAMMATE_MODE=tmux`)
- `architecture_style`: detected from the repository structure (`layered`, `hexagonal`, `microservices`, or `repo-native`)
- `lint_profile`: detected from config files present in the repo (e.g., `eslint,prettier`, `ruff,mypy`)
- `docs_lookup_mode`: `context7` if the MCP is available, `repo-fallback` otherwise
- `runtime_policy`: version from `plugins/claude-tech-squad/runtime-policy.yaml`

### 4. Teammate architecture block

Defines the tool sequence for spawning agents:

```markdown
## Teammate Architecture

1. `TeamCreate` — create the team for this workflow
2. `Agent` with `team_name` + `name` + `subagent_type` — spawn each specialist as a teammate
3. `SendMessage` — communicate with running teammates
4. `TaskCreate` + `TaskUpdate` — assign and track work per teammate

**Do NOT use Agent without team_name** — that runs an inline subagent, not a visible teammate pane.
```

### 5. Agent chain definition

The ordered list of agents invoked by the skill, with their phase, purpose, and any gate that precedes or follows them.

Format:

```markdown
## Phase: <phase-name>

Spawn in order:

1. `<agent-subagent-type>` — <one-line purpose>
2. `<agent-subagent-type>` — <one-line purpose>

[Gate] <gate-name> — <what the user decides here>

3. `<agent-subagent-type>` — <one-line purpose> (parallel with 4)
4. `<agent-subagent-type>` — <one-line purpose> (parallel with 3)
```

### 6. Gate definitions

Gates pause the workflow and require a user decision before continuing. Each gate must define:
- Its name (used in the `[Gate]` trace line)
- What the user is deciding
- What counts as approval vs. rejection
- What happens on each path

Gates exist only where human judgment is irreplaceable. Do not add gates for decisions that agents can resolve autonomously.

### 7. Checkpoint and resume block

Every skill must define checkpoints and the resume rule. Written to the SEP log via `checkpoint_resume.write_to_sep_log: true` in `runtime-policy.yaml`.

```markdown
## Checkpoints

Save a checkpoint after each of the following:
- `preflight-passed`
- `gate-<n>-approved` (one per gate)
- `<phase-name>-complete`

Resume rule: resume from the highest completed checkpoint unless inputs materially changed.
```

### 8. SEP log instruction

The skill must instruct the orchestrator to write a Squad Execution Protocol log to `ai-docs/.squad-log/` before the run ends.

Minimum fields required in the SEP log:
- `skill`
- `execution_mode`
- `architecture_style`
- `checkpoints` (array of cleared checkpoints)
- `fallbacks_invoked` (array, empty if none)
- `final_status`
- `timestamp`

---

## Failure handling

Skills rely on `runtime-policy.yaml` for retry and fallback behavior. A skill does not define its own retry limits — it inherits them from the central policy:

| Situation | Policy |
|---|---|
| Agent produces invalid output | Retry same agent, max 2 times |
| Agent fails after 2 retries | Invoke fallback from `fallback_matrix` |
| Fallback also fails | Present gate to user: R (retry) / S (skip with risk log) / X (abort) |
| Finding is BLOCKING | Pause pipeline, require resolution before continuing |

Skills reference the fallback matrix implicitly — they do not hardcode fallback agents.

---

## What makes a skill invalid

| Problem | Effect |
|---|---|
| Missing Global Safety Contract | Agents spawned without prohibitions contract |
| Missing Operator Visibility Contract | Run produces no trace lines — not verifiable |
| Missing preflight | No `[Preflight Passed]` — run fails smoke test |
| No checkpoints defined | Interrupted runs cannot be resumed |
| No SEP log instruction | `/factory-retrospective` has no data to analyze |
| Gates with no decision criteria | User cannot meaningfully approve or reject |
