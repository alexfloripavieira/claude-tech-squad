from __future__ import annotations

import json
from pathlib import Path

from squad_cli.ticket import TicketContext, detect_ticket_source
from squad_cli.ticket_sources.github import GitHubIssueAdapter
from squad_cli.ticket_sources.jira import JiraAdapter
from squad_cli.ticket_sources.linear import LinearAdapter
from squad_cli.ticket_sources.pasted import PastedTicketAdapter


def load_contexts(
    raw: str,
    ticket_json: Path | None = None,
    text_file: Path | None = None,
) -> list[TicketContext]:
    if ticket_json:
        data = json.loads(ticket_json.read_text())
        if isinstance(data, list):
            return [_adapter_for_mapping(item, raw).from_mapping(item, raw) for item in data]
        if not isinstance(data, dict):
            raise ValueError("ticket_json must contain an object or list of objects")
        return [_adapter_for_mapping(data, raw).from_mapping(data, raw)]

    text = text_file.read_text() if text_file else raw
    detected = detect_ticket_source(raw or text)
    adapter = _adapter_for_source(detected["source"])
    return adapter.from_text(raw or text, text)


def _adapter_for_mapping(data: dict, raw: str):
    detected = detect_ticket_source(str(data.get("ticket_id") or raw))
    source = str(data.get("source") or detected["source"])
    return _adapter_for_source(source)


def _adapter_for_source(source: str):
    if source in {"jira", "jira-jql"}:
        return JiraAdapter()
    if source == "linear":
        return LinearAdapter()
    if source == "github":
        return GitHubIssueAdapter()
    return PastedTicketAdapter()
