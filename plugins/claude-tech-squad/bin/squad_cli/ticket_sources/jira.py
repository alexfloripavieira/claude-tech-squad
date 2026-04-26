from __future__ import annotations

from typing import Any

from squad_cli.ticket import TicketContext, detect_ticket_source
from squad_cli.ticket_sources.base import TicketSourceAdapter


class JiraAdapter(TicketSourceAdapter):
    source = "jira"

    def from_mapping(self, data: dict[str, Any], raw: str) -> TicketContext:
        fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
        detected = detect_ticket_source(str(data.get("key") or data.get("ticket_id") or raw))
        return TicketContext(
            source=str(data.get("source") or detected["source"]),
            ticket_id=str(data.get("ticket_id") or data.get("key") or detected["ticket_id"]),
            title=str(data.get("title") or data.get("summary") or fields.get("summary") or ""),
            description=str(data.get("description") or fields.get("description") or ""),
            issue_type=_name(data.get("issue_type") or data.get("type") or fields.get("issuetype"), "Task"),
            priority=_name(data.get("priority") or fields.get("priority"), "Medium"),
            acceptance_criteria=self._coerce_list(data.get("acceptance_criteria")),
            subtasks=self._coerce_list(data.get("subtasks") or fields.get("subtasks")),
            labels=self._coerce_list(data.get("labels") or fields.get("labels")),
            linked_issues=self._coerce_list(data.get("linked_issues") or fields.get("issuelinks")),
            comments=self._coerce_comments(data.get("comments") or fields.get("comment")),
        )

    @staticmethod
    def _coerce_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [_name(item, "") for item in value if _name(item, "")]
        return [_name(value, "")]

    @staticmethod
    def _coerce_comments(value: Any) -> list[str]:
        if isinstance(value, dict) and isinstance(value.get("comments"), list):
            return [_name(item.get("body") if isinstance(item, dict) else item, "") for item in value["comments"]]
        return JiraAdapter._coerce_list(value)


def _name(value: Any, default: str) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or value.get("key") or default)
    return str(value or default)
