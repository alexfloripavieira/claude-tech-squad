#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_BIN = ROOT / "plugins/claude-tech-squad/bin"
FIXTURE_DIR = ROOT / "ai-docs/claude-tech-squad-console/fixtures/tickets"

sys.path.insert(0, str(PLUGIN_BIN))

from squad_cli.ticket import TicketContext, build_ticket_plan, load_ticket_contexts  # noqa: E402
from squad_cli.ticket_sources import fetch_context_with_fallback  # noqa: E402
from squad_cli.ticket_sources.base import TicketSourceAdapter, TicketSourceError  # noqa: E402
from squad_cli.ticket_sources.github import GitHubIssueAdapter  # noqa: E402
from squad_cli.ticket_sources.jira import JiraAdapter  # noqa: E402
from squad_cli.ticket_sources.linear import LinearAdapter  # noqa: E402
from squad_cli.ticket_sources.pasted import PastedTicketAdapter  # noqa: E402


class OfflineGitHubClient(GitHubIssueAdapter):
    def fetch_ticket(self, identifier: str) -> dict[str, Any]:
        raise TicketSourceError(f"github credentials unavailable for {identifier}")


class SandboxGitHubClient(GitHubIssueAdapter):
    def fetch_ticket(self, identifier: str) -> dict[str, Any]:
        payload = json.loads((FIXTURE_DIR / "sandbox/github-issue-api.json").read_text())
        payload["repository"] = "sandbox/api"
        return payload


def main() -> int:
    assert_adapter_context(
        "github-issue.json",
        GitHubIssueAdapter(),
        source="github",
        ticket_id="acme/checkout#42",
        skill="hotfix",
    )
    assert_adapter_context(
        "jira-issue.json",
        JiraAdapter(),
        source="jira",
        ticket_id="OPS-7",
        skill="iac-review",
    )
    assert_adapter_context(
        "linear-issue.json",
        LinearAdapter(),
        source="linear",
        ticket_id="LIN-123",
        skill="prompt-review",
    )
    assert_adapter_context(
        "pasted-ticket.json",
        PastedTicketAdapter(),
        source="pasted",
        ticket_id="pasted",
        skill="implement",
    )

    for path in sorted((FIXTURE_DIR / "sandbox").glob("*.json")):
        contexts = load_ticket_contexts("", ticket_json=path)
        if len(contexts) != 1:
            raise AssertionError(f"{path.name}: expected one context")
        if not contexts[0].title:
            raise AssertionError(f"{path.name}: missing normalized title")
        build_ticket_plan(contexts[0])

    fetched = fetch_context_with_fallback(SandboxGitHubClient(), "sandbox/api#314")
    assert not fetched.fallback_used
    assert fetched.context.source == "github"
    assert fetched.context.ticket_id == "sandbox/api#314"

    fallback = fetch_context_with_fallback(OfflineGitHubClient(), "sandbox/api#314")
    assert fallback.fallback_used
    assert fallback.source == "pasted"
    assert fallback.context.source == "pasted"
    assert fallback.context.ticket_id == "sandbox/api#314"
    assert "github credentials unavailable" in fallback.error
    assert build_ticket_plan(fallback.context).recommended_skill in {"implement", "discovery"}

    print("ticket source adapter tests passed")
    return 0


def assert_adapter_context(
    fixture_name: str,
    adapter: TicketSourceAdapter,
    *,
    source: str,
    ticket_id: str,
    skill: str,
) -> None:
    payload = json.loads((FIXTURE_DIR / fixture_name).read_text())
    context = adapter.to_context(payload)
    assert isinstance(context, TicketContext)
    assert context.source == source, context
    assert context.ticket_id == ticket_id, context
    assert context.title, context
    assert build_ticket_plan(context).recommended_skill == skill


if __name__ == "__main__":
    raise SystemExit(main())
