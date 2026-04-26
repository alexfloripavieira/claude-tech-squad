from __future__ import annotations

from typing import Any

from squad_cli.ticket import TicketContext, detect_ticket_source
from squad_cli.ticket_sources.base import TicketSourceAdapter


class LinearAdapter(TicketSourceAdapter):
    source = "linear"

    def from_mapping(self, data: dict[str, Any], raw: str) -> TicketContext:
        detected = detect_ticket_source(str(data.get("identifier") or data.get("ticket_id") or raw))
        return TicketContext(
            source=str(data.get("source") or "linear"),
            ticket_id=str(data.get("ticket_id") or data.get("identifier") or detected["ticket_id"]),
            title=str(data.get("title") or ""),
            description=str(data.get("description") or ""),
            issue_type=str(data.get("issue_type") or data.get("type") or "Task"),
            priority=_priority(data.get("priority") or data.get("priorityLabel")),
            acceptance_criteria=self._coerce_list(data.get("acceptance_criteria")),
            subtasks=self._coerce_list(data.get("subtasks") or data.get("children")),
            labels=self._coerce_labels(data.get("labels")),
            linked_issues=self._coerce_list(data.get("linked_issues") or data.get("relations")),
            comments=self._coerce_list(data.get("comments")),
        )

    @staticmethod
    def _coerce_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [_title(item) for item in value if _title(item)]
        return [str(value)]

    @staticmethod
    def _coerce_labels(value: Any) -> list[str]:
        if isinstance(value, dict) and isinstance(value.get("nodes"), list):
            return [_title(item) for item in value["nodes"] if _title(item)]
        return LinearAdapter._coerce_list(value)


def _priority(value: Any) -> str:
    mapping = {0: "Low", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}
    if isinstance(value, int):
        return mapping.get(value, "Medium")
    return str(value or "Medium")


def _title(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("title") or value.get("name") or value.get("identifier") or "")
    return str(value)
