from __future__ import annotations

from typing import Any

from squad_cli.ticket import TicketContext, detect_ticket_source
from squad_cli.ticket_sources.base import TicketSourceAdapter


class GitHubIssueAdapter(TicketSourceAdapter):
    source = "github"

    def from_mapping(self, data: dict[str, Any], raw: str) -> TicketContext:
        detected = detect_ticket_source(str(data.get("ticket_id") or raw))
        repo = data.get("repository") or data.get("repo") or ""
        number = data.get("number")
        ticket_id = str(data.get("ticket_id") or (f"{repo}#{number}" if repo and number else detected["ticket_id"]))
        return TicketContext(
            source=str(data.get("source") or "github"),
            ticket_id=ticket_id,
            title=str(data.get("title") or ""),
            description=str(data.get("description") or data.get("body") or ""),
            issue_type=str(data.get("issue_type") or data.get("type") or "Task"),
            priority=str(data.get("priority") or "Medium"),
            acceptance_criteria=self._coerce_list(data.get("acceptance_criteria")),
            subtasks=self._coerce_list(data.get("subtasks")),
            labels=self._coerce_labels(data.get("labels")),
            linked_issues=self._coerce_list(data.get("linked_issues")),
            comments=self._coerce_comments(data.get("comments")),
        )

    @staticmethod
    def _coerce_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @staticmethod
    def _coerce_labels(value: Any) -> list[str]:
        if isinstance(value, list):
            labels = []
            for item in value:
                labels.append(str(item.get("name") if isinstance(item, dict) else item))
            return labels
        return GitHubIssueAdapter._coerce_list(value)

    @staticmethod
    def _coerce_comments(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item.get("body") if isinstance(item, dict) else item) for item in value]
        return GitHubIssueAdapter._coerce_list(value)
