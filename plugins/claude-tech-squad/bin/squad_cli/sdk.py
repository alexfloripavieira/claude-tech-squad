from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from squad_cli.dashboard import DashboardReport, build_dashboard_report
from squad_cli.onboarding import OnboardingPlan, build_onboarding_plan, load_onboarding_catalog
from squad_cli.ticket import TicketContext, TicketPlan, build_ticket_plan, load_ticket_context


SDK_API_VERSION = "1.0"


class SquadSDKError(Exception):
    """Base error for SDK consumers."""


class TicketSourceError(SquadSDKError):
    """Raised when ticket context cannot be normalized."""


class CatalogError(SquadSDKError):
    """Raised when the onboarding catalog cannot be read or validated."""


class ReportParseError(SquadSDKError):
    """Raised when dashboard inputs cannot be parsed."""


@dataclass
class SquadSDK:
    project_root: Path = Path(".")
    plugin_root: Path = Path("plugins/claude-tech-squad")
    api_version: str = SDK_API_VERSION

    @property
    def onboarding_catalog(self) -> Path:
        return self.plugin_root / "skills/onboarding/catalog.json"

    @property
    def sep_log_dir(self) -> Path:
        return self.project_root / "ai-docs/.squad-log"

    def onboarding_plan(self) -> OnboardingPlan:
        try:
            load_onboarding_catalog(self.onboarding_catalog)
            return build_onboarding_plan(self.project_root, self.onboarding_catalog)
        except Exception as exc:
            raise CatalogError(str(exc)) from exc

    def dashboard_report(self, limit: int = 30) -> DashboardReport:
        try:
            return build_dashboard_report(self.sep_log_dir, limit)
        except Exception as exc:
            raise ReportParseError(str(exc)) from exc

    def ticket_plan(
        self,
        raw: str,
        ticket_json: str | Path | None = None,
        text_file: str | Path | None = None,
    ) -> TicketPlan:
        try:
            ticket_path = Path(ticket_json) if ticket_json else None
            text_path = Path(text_file) if text_file else None
            context = load_ticket_context(raw, ticket_path, text_path)
            return build_ticket_plan(context)
        except Exception as exc:
            raise TicketSourceError(str(exc)) from exc

    def ticket_plan_from_context(self, context: TicketContext | dict[str, Any]) -> TicketPlan:
        try:
            if isinstance(context, TicketContext):
                ticket_context = context
            else:
                ticket_context = TicketContext(
                    source=str(context.get("source") or "pasted"),
                    ticket_id=str(context.get("ticket_id") or "pasted"),
                    title=str(context.get("title") or ""),
                    description=str(context.get("description") or ""),
                    issue_type=str(context.get("issue_type") or "Task"),
                    priority=str(context.get("priority") or "Medium"),
                    acceptance_criteria=_as_list(context.get("acceptance_criteria")),
                    subtasks=_as_list(context.get("subtasks")),
                    labels=_as_list(context.get("labels")),
                    linked_issues=_as_list(context.get("linked_issues")),
                    comments=_as_list(context.get("comments")),
                )
            return build_ticket_plan(ticket_context)
        except Exception as exc:
            raise TicketSourceError(str(exc)) from exc


def create_client(
    project_root: str | Path = ".",
    plugin_root: str | Path = "plugins/claude-tech-squad",
) -> SquadSDK:
    return SquadSDK(project_root=Path(project_root), plugin_root=Path(plugin_root))


def to_json(model: Any) -> str:
    if hasattr(model, "to_dict"):
        data = model.to_dict()
    elif isinstance(model, dict):
        data = model
    else:
        raise SquadSDKError(f"Object is not SDK-serializable: {type(model).__name__}")
    return json.dumps(data, indent=2, sort_keys=True)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
