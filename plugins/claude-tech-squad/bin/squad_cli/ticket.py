from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


JIRA_RE = re.compile(r"\b[A-Z][A-Z0-9]+-[0-9]+\b")
LINEAR_RE = re.compile(r"\bLIN-[0-9]+\b")
GITHUB_RE = re.compile(r"(?:(?P<repo>[\w.-]+/[\w.-]+))?#(?P<number>[0-9]+)\b")


@dataclass
class TicketContext:
    source: str
    ticket_id: str
    title: str = ""
    description: str = ""
    issue_type: str = "Task"
    priority: str = "Medium"
    acceptance_criteria: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    linked_issues: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass
class TicketPlan:
    source: str
    ticket_id: str
    issue_type: str
    priority: str
    complexity_tier: str
    recommended_skill: str
    estimated_agents: int
    estimated_tokens: int
    estimated_cost_usd: float
    alternatives: list[dict[str, str]]
    extracted_context: dict[str, Any]
    launch_context: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def detect_ticket_source(raw: str) -> dict[str, str]:
    text = raw.strip()
    if not text:
        return {"source": "pasted", "ticket_id": "pasted"}

    if _is_quoted(text):
        return {"source": "jira-jql", "ticket_id": text[1:-1]}

    linear = LINEAR_RE.search(text)
    if linear:
        return {"source": "linear", "ticket_id": linear.group(0)}

    github = GITHUB_RE.search(text)
    if github:
        repo = github.group("repo")
        number = github.group("number")
        return {
            "source": "github",
            "ticket_id": f"{repo}#{number}" if repo else f"#{number}",
        }

    jira = JIRA_RE.search(text)
    if jira:
        return {"source": "jira", "ticket_id": jira.group(0)}

    return {"source": "pasted", "ticket_id": "pasted"}


def load_ticket_context(
    raw: str,
    ticket_json: Path | None = None,
    text_file: Path | None = None,
) -> TicketContext:
    contexts = load_ticket_contexts(raw, ticket_json, text_file)
    return contexts[0]


def load_ticket_contexts(
    raw: str,
    ticket_json: Path | None = None,
    text_file: Path | None = None,
) -> list[TicketContext]:
    from squad_cli.ticket_sources import load_contexts

    return load_contexts(raw, ticket_json, text_file)


def build_ticket_plan(context: TicketContext) -> TicketPlan:
    issue_type = _normalize_issue_type(context.issue_type)
    priority = _normalize_priority(context.priority)
    labels = [label.lower() for label in context.labels]
    skill = _recommend_skill(issue_type, priority, len(context.subtasks), labels, context.description)
    complexity = _complexity_tier(issue_type, priority, len(context.subtasks), labels)
    agents, tokens = _estimate_effort(skill, complexity)

    return TicketPlan(
        source=context.source,
        ticket_id=context.ticket_id,
        issue_type=issue_type,
        priority=priority,
        complexity_tier=complexity,
        recommended_skill=skill,
        estimated_agents=agents,
        estimated_tokens=tokens,
        estimated_cost_usd=round(tokens * 45 / 1_000_000, 2),
        alternatives=_alternatives(skill),
        extracted_context=context.to_dict(),
        launch_context=render_launch_context(context),
    )


def build_ticket_plans(contexts: list[TicketContext]) -> list[TicketPlan]:
    return [build_ticket_plan(context) for context in contexts]


def write_from_ticket_sep_log(
    plan: TicketPlan,
    log_dir: Path,
    skill_launched: str = "",
    ticket_updated: bool = False,
    fallback_used: bool = False,
) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safe_ticket = re.sub(r"[^A-Za-z0-9_.-]+", "-", plan.ticket_id).strip("-") or "pasted"
    run_id = f"from-ticket-{uuid4().hex[:8]}"
    path = log_dir / f"{timestamp[:19].replace(':', '-')}-from-ticket-{safe_ticket}.md"
    fallback_values = ["ticket-source-unavailable"] if fallback_used else []
    body = "\n".join(
        [
            "---",
            f"run_id: {run_id}",
            "skill: from-ticket",
            f"timestamp: {timestamp}",
            "status: completed",
            "final_status: completed",
            "execution_mode: inline",
            f"ticket_source: {plan.source}",
            f"ticket_id: {plan.ticket_id}",
            f"recommended_skill: {plan.recommended_skill}",
            f"skill_launched: {skill_launched or 'none'}",
            f"ticket_updated: {str(ticket_updated).lower()}",
            f"fallback_used: {str(fallback_used).lower()}",
            f"fallbacks_invoked: {fallback_values}",
            "checkpoints: [ticket-context-loaded, ticket-plan-built]",
            "gates_blocked: []",
            "---",
            "",
            "## Output Digest",
            f"Planned `{plan.ticket_id}` from `{plan.source}` for `/{plan.recommended_skill}`.",
            "",
            "## Launch Context",
            plan.launch_context,
            "",
        ]
    )
    path.write_text(body)
    return path


def render_launch_context(context: TicketContext) -> str:
    ac = "\n".join(f"- {item}" for item in context.acceptance_criteria) or "- None found"
    subtasks = "\n".join(f"- {item}" for item in context.subtasks) or "- None"
    labels = ", ".join(context.labels) if context.labels else "None"
    comments = "\n".join(f"- {item}" for item in context.comments[:5]) or "- None"

    return "\n".join(
        [
            f"## Ticket Context - {context.ticket_id}",
            "",
            "### Title",
            context.title or "Untitled",
            "",
            "### Description",
            context.description or "No description provided.",
            "",
            "### Acceptance Criteria",
            ac,
            "",
            "### Subtasks",
            subtasks,
            "",
            "### Priority",
            context.priority,
            "",
            "### Labels",
            labels,
            "",
            "### Additional Context from Comments",
            comments,
        ]
    )


def _context_from_mapping(data: dict[str, Any], raw: str) -> TicketContext:
    detected = detect_ticket_source(str(data.get("ticket_id") or raw))
    return TicketContext(
        source=str(data.get("source") or detected["source"]),
        ticket_id=str(data.get("ticket_id") or detected["ticket_id"]),
        title=str(data.get("title") or data.get("summary") or ""),
        description=str(data.get("description") or data.get("body") or ""),
        issue_type=str(data.get("issue_type") or data.get("type") or "Task"),
        priority=str(data.get("priority") or "Medium"),
        acceptance_criteria=_coerce_list(data.get("acceptance_criteria")),
        subtasks=_coerce_list(data.get("subtasks")),
        labels=_coerce_list(data.get("labels")),
        linked_issues=_coerce_list(data.get("linked_issues")),
        comments=_coerce_list(data.get("comments")),
    )


def _recommend_skill(
    issue_type: str,
    priority: str,
    subtask_count: int,
    labels: list[str],
    description: str,
) -> str:
    haystack = " ".join(labels + [description.lower()])
    if "security" in haystack:
        return "security-audit"
    if "migration" in haystack:
        return "migration-plan"
    if "terraform" in haystack or "infra" in haystack or "iac" in haystack:
        return "iac-review"
    if "prompt" in haystack or "llm" in haystack:
        return "prompt-review"
    if issue_type == "Bug":
        return "hotfix" if priority in {"Critical", "High"} else "bug-fix"
    if issue_type == "Epic" or subtask_count >= 3:
        return "squad"
    if issue_type in {"Story", "Task", "Subtask", "Improvement"}:
        return "implement"
    return "discovery"


def _complexity_tier(
    issue_type: str,
    priority: str,
    subtask_count: int,
    labels: list[str],
) -> str:
    if issue_type == "Epic" or subtask_count >= 5:
        return "large"
    if subtask_count >= 3 or priority in {"Critical", "High"} or any(l in {"security", "migration"} for l in labels):
        return "medium"
    return "small"


def _estimate_effort(skill: str, complexity: str) -> tuple[int, int]:
    base = {
        "hotfix": (4, 60_000),
        "bug-fix": (6, 90_000),
        "implement": (9, 160_000),
        "squad": (18, 320_000),
        "discovery": (11, 180_000),
        "security-audit": (3, 70_000),
        "migration-plan": (4, 85_000),
        "iac-review": (3, 65_000),
        "prompt-review": (2, 40_000),
    }.get(skill, (3, 50_000))
    multiplier = {"small": 1.0, "medium": 1.35, "large": 1.8}[complexity]
    return base[0], int(base[1] * multiplier)


def _alternatives(skill: str) -> list[dict[str, str]]:
    options = {
        "hotfix": [
            {"skill": "bug-fix", "when": "production is not actively impaired"},
            {"skill": "incident-postmortem", "when": "after the patch is shipped"},
        ],
        "bug-fix": [
            {"skill": "hotfix", "when": "severity is production-critical"},
            {"skill": "refactor", "when": "the ticket is mostly technical debt"},
        ],
        "implement": [
            {"skill": "discovery", "when": "requirements or tradeoffs are unclear"},
            {"skill": "squad", "when": "work spans teams or several subsystems"},
        ],
        "squad": [
            {"skill": "discovery", "when": "only blueprinting is needed now"},
            {"skill": "implement", "when": "scope is already approved and narrow"},
        ],
    }
    return options.get(skill, [{"skill": "discovery", "when": "scope needs clarification"}])


def _normalize_issue_type(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "bug": "Bug",
        "defect": "Bug",
        "story": "Story",
        "user story": "Story",
        "epic": "Epic",
        "task": "Task",
        "subtask": "Subtask",
        "sub-task": "Subtask",
        "improvement": "Improvement",
        "refactor": "Improvement",
    }
    return mapping.get(normalized, value.strip().title() or "Task")


def _normalize_priority(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "p0": "Critical",
        "critical": "Critical",
        "highest": "Critical",
        "urgent": "High",
        "p1": "High",
        "high": "High",
        "p2": "Medium",
        "medium": "Medium",
        "normal": "Medium",
        "p3": "Low",
        "low": "Low",
    }
    return mapping.get(normalized, value.strip().title() or "Medium")


def _infer_issue_type(text: str, labels: list[str]) -> str:
    haystack = " ".join(labels + [text.lower()])
    if "bug" in haystack or "error" in haystack or "fix" in haystack:
        return "Bug"
    if "epic" in haystack:
        return "Epic"
    if "refactor" in haystack:
        return "Improvement"
    return "Task"


def _infer_priority(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("p0", "critical", "sev1", "production down")):
        return "Critical"
    if any(word in lowered for word in ("p1", "high", "urgent")):
        return "High"
    if any(word in lowered for word in ("p3", "low")):
        return "Low"
    return "Medium"


def _extract_prefixed(text: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _extract_list(text: str, key: str) -> list[str]:
    value = _extract_prefixed(text, key)
    if not value:
        return []
    return [item.strip(" -") for item in re.split(r",|;", value) if item.strip(" -")]


def _extract_acceptance_criteria(text: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(acceptance criteria|ac)\s*:?\s*$", stripped, re.IGNORECASE):
            in_section = True
            continue
        if in_section and re.match(r"^[A-Z][A-Za-z ]+:\s*$", stripped):
            break
        if in_section and stripped.startswith(("-", "*")):
            items.append(stripped[1:].strip())
    return items


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:120]
    return ""


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _is_quoted(text: str) -> bool:
    return len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}
