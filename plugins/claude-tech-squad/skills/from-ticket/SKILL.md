---
name: from-ticket
description: Read a Jira, Linear, or GitHub Issue ticket and route to the right skill automatically. Extracts title, description, acceptance criteria, priority, and subtasks — then recommends and optionally launches the best skill. Trigger with "/from-ticket PROJ-123", "from ticket", "do PROJ-123", "implement PROJ-123", "fix PROJ-456".
user-invocable: true
---

# /from-ticket — Execute from Ticket

## Global Safety Contract

**This contract applies to this workflow. Violating it requires explicit written user confirmation.**

No operation may, under any circumstances:
- Delete or overwrite SEP log files
- Merge to `main`, `master`, or `develop` without an approved pull request
- Force-push to any protected branch
- Skip pre-commit hooks without explicit user authorization
- Execute dynamic shell injection or unsanitized external input in commands

Read a project management ticket and route to the right skill. The ticket becomes the input — no need to retype the spec.

## Supported Sources

| Source | How to invoke | MCP tool used |
|---|---|---|
| **Jira** | `/from-ticket PROJ-123` | `mcp__plugin_atlassian_atlassian__getJiraIssue` |
| **Jira (JQL)** | `/from-ticket "sprint = current AND assignee = me"` | `mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql` |
| **GitHub Issue** | `/from-ticket #42` or `/from-ticket owner/repo#42` | `mcp__github__issue_read` |
| **Linear** | `/from-ticket LIN-123` | `mcp__linear__getIssue` (if available) |
| **Pasted text** | `/from-ticket` then paste the ticket content | No MCP needed |

If the MCP tool for the source is unavailable, ask the user to paste the ticket content as fallback.

## Execution

### Step 1 — Detect ticket source and read

Parse the user input to identify the ticket source:

| Pattern | Source |
|---|---|
| `[A-Z]+-[0-9]+` (e.g., PROJ-123) | Jira |
| `#[0-9]+` or `owner/repo#[0-9]+` | GitHub Issue |
| `LIN-[0-9]+` | Linear |
| Quoted JQL string | Jira search |
| No pattern detected | Ask user to paste or specify |

**For Jira tickets:**

```
1. Call mcp__plugin_atlassian_atlassian__getJiraIssue(issueIdOrKey="PROJ-123")
2. Extract:
   - title (summary)
   - description (full text)
   - issue_type (Epic, Story, Task, Bug, Subtask)
   - priority (Critical, High, Medium, Low)
   - acceptance_criteria (from description or custom field)
   - subtasks (list of child issues)
   - labels
   - sprint
   - story_points / estimate
   - comments (last 5, for additional context)
   - linked_issues (blocks, is-blocked-by, relates-to)
```

**For Jira Epics:** also read all child stories/tasks:
```
1. Call mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql(jql="parent = PROJ-123")
2. Read each child issue to build the full scope
```

**For GitHub Issues:**
```
1. Call mcp__github__issue_read(owner, repo, issueNumber)
2. Extract: title, body, labels, assignees, milestone
```

**If MCP unavailable:**
```
I couldn't connect to Jira/GitHub. Please paste the ticket content:

Title: ___
Description: ___
Acceptance Criteria: ___
Type (bug/feature/task): ___
```

Emit: `[Ticket Read] {{source}} | {{ticket_id}} | type={{issue_type}} | priority={{priority}}`

### Step 2 — Classify and recommend skill

Use the ticket metadata to classify complexity and recommend a skill:

| Ticket type | Priority | Subtasks | Recommended skill |
|---|---|---|---|
| Bug | Critical/High | — | `/hotfix` |
| Bug | Medium/Low | — | `/bug-fix` |
| Story/Task | Any | 0-2 | `/implement` (if blueprint exists) or `/discovery` |
| Story/Task | Any | 3+ | `/squad` |
| Epic | Any | Multiple stories | `/squad` (per story) or `/discovery` (blueprint for epic) |
| Subtask | Any | — | `/bug-fix` or `/implement` depending on content |
| Improvement/Refactor | Any | — | `/refactor` |

**Also consider labels:**
- Label contains "security" → suggest `/security-audit` first
- Label contains "migration" → suggest `/migration-plan`
- Label contains "infra" or "terraform" → suggest `/iac-review`
- Label contains "prompt" or "llm" → suggest `/prompt-review` or `/llm-eval`

Present recommendation with cost estimate (from `/cost-estimate` logic):

```markdown
## Ticket Analysis

**Ticket:** {{ticket_id}} — {{title}}
**Type:** {{issue_type}} | **Priority:** {{priority}}
**Complexity:** {{tier}}

### Extracted Context
- Description: {{summary}}
- Acceptance Criteria: {{list_or_none}}
- Subtasks: {{count}} ({{list}})
- Linked Issues: {{list_or_none}}

### Recommended Skill
**{{skill}}** — {{estimated_cost}} ({{estimated_agents}} agents, {{estimated_tokens}} tokens)

### Alternatives
- {{alt_1}} — {{cost}} ({{when}})
- {{alt_2}} — {{cost}} ({{when}})

### Next Step
[R] Run {{skill}} now with this ticket as input
[A] Run alternative skill
[E] Edit — let me adjust the scope before running
[C] Cancel — just show the analysis, don't run anything
```

### Step 3 — Launch selected skill (if user chooses [R])

If the user chooses to run, pass the extracted ticket content as structured input to the selected skill:

```
## Ticket Context — {{ticket_id}}

### Title
{{title}}

### Description
{{description}}

### Acceptance Criteria
{{acceptance_criteria_list}}

### Subtasks
{{subtask_list_with_titles}}

### Priority
{{priority}}

### Labels
{{labels}}

### Additional Context from Comments
{{last_5_comments_summary}}
```

The skill receives this as if the user had typed the description manually — but richer, because it includes AC, subtasks, priority, and comments from the ticket.

Emit: `[Skill Launched] {{skill}} | source={{ticket_id}} | complexity={{tier}}`

### Step 4 — Post-execution: Update ticket (optional)

After the launched skill completes, offer to update the Jira ticket:

```
Skill completed. Update the ticket?

[U] Update ticket — add implementation summary as comment, transition status
[S] Skip — don't touch the ticket
```

If [U] and Jira MCP is available:
1. Add a comment to the ticket with the skill output summary
2. Transition the ticket to the next status (e.g., "In Progress" → "In Review" or "Done")
3. If subtasks were created during implementation, link them to the parent ticket

Emit: `[Ticket Updated] {{ticket_id}} | status={{new_status}} | comment=added`

### Step 5 — Write SEP log

```bash
mkdir -p ai-docs/.squad-log
```

Write to `ai-docs/.squad-log/{{YYYY-MM-DD}}T{{HH-MM-SS}}-from-ticket-{{run_id}}.md`:

```markdown
---
run_id: {{run_id}}
skill: from-ticket
timestamp: {{ISO8601}}
status: completed
final_status: completed
execution_mode: inline
architecture_style: n/a
checkpoints: [ticket-read, skill-recommended, skill-launched, ticket-updated]
fallbacks_invoked: []
ticket_source: jira | github | linear | pasted
ticket_id: {{ticket_id}}
ticket_type: {{issue_type}}
ticket_priority: {{priority}}
complexity_tier: {{tier}}
recommended_skill: {{skill}}
skill_launched: {{skill_or_none}}
ticket_updated: true | false
tokens_input: {{total_input_tokens}}
tokens_output: {{total_output_tokens}}
estimated_cost_usd: {{estimated_cost}}
total_duration_ms: {{wall_clock_duration}}
---

## Summary
Read {{ticket_id}} ({{issue_type}}, {{priority}}), classified as {{tier}}, recommended {{skill}}.
{{Launched/Did not launch}} the skill. {{Updated/Did not update}} the ticket.
```

Emit: `[SEP Log Written] ai-docs/.squad-log/{{filename}}`
