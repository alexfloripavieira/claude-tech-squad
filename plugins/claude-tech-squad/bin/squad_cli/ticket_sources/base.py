from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

from squad_cli.ticket import TicketContext, detect_ticket_source


class TicketSourceError(RuntimeError):
    """Raised when a ticket source cannot fetch or normalize a ticket."""


class TicketSourceClient(Protocol):
    source: str

    def fetch_ticket(self, identifier: str) -> dict[str, Any]:
        """Fetch a raw ticket payload from an external source."""

    def to_context(self, payload: dict[str, Any]) -> TicketContext:
        """Normalize a raw source payload into a TicketContext."""


@dataclass
class TicketFetchResult:
    context: TicketContext
    source: str
    fallback_used: bool = False
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "source": self.source,
            "fallback_used": self.fallback_used,
            "error": self.error,
        }


class TicketSourceAdapter:
    source = "pasted"

    def fetch_ticket(self, identifier: str) -> dict[str, Any]:
        raise TicketSourceError(f"{self.source} fetch is not configured for {identifier}")

    def to_context(self, payload: dict[str, Any]) -> TicketContext:
        return self.from_mapping(payload, str(payload.get("ticket_id") or ""))

    def from_mapping(self, data: dict[str, Any], raw: str) -> TicketContext:
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

    def from_text(self, raw: str, text: str) -> list[TicketContext]:
        detected = detect_ticket_source(raw or text)
        labels = _extract_list(text, "Labels")
        return [
            TicketContext(
                source=detected["source"],
                ticket_id=detected["ticket_id"],
                title=_extract_prefixed(text, "Title") or _first_nonempty_line(text),
                description=text.strip(),
                issue_type=_extract_prefixed(text, "Type") or _infer_issue_type(text, labels),
                priority=_extract_prefixed(text, "Priority") or _infer_priority(text),
                acceptance_criteria=_extract_acceptance_criteria(text),
                subtasks=_extract_list(text, "Subtasks"),
                labels=labels,
            )
        ]


def fetch_with_fallback(
    client: TicketSourceClient,
    identifier: str,
    fallback_client: TicketSourceClient,
    fallback_payload: dict[str, Any] | None = None,
) -> TicketFetchResult:
    try:
        payload = client.fetch_ticket(identifier)
        return TicketFetchResult(
            context=client.to_context(payload),
            source=client.source,
        )
    except Exception as exc:
        if fallback_payload is None:
            fallback_payload = {
                "source": "pasted",
                "ticket_id": identifier or "pasted",
                "title": identifier or "External ticket unavailable",
                "description": (
                    f"External source `{client.source}` was unavailable. "
                    "Paste the ticket body or provide captured JSON to continue."
                ),
                "issue_type": "Task",
                "priority": "Medium",
                "labels": ["fallback", client.source],
                "comments": [str(exc)],
            }
        return TicketFetchResult(
            context=fallback_client.to_context(fallback_payload),
            source=fallback_client.source,
            fallback_used=True,
            error=str(exc),
        )


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


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
