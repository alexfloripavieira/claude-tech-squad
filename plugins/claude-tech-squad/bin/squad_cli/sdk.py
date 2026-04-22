from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from squad_cli.dashboard import DashboardReport, build_dashboard_report
from squad_cli.onboarding import OnboardingPlan, build_onboarding_plan
from squad_cli.ticket import TicketPlan, build_ticket_plan, load_ticket_context


@dataclass
class SquadSDK:
    project_root: Path = Path(".")
    plugin_root: Path = Path("plugins/claude-tech-squad")

    @property
    def onboarding_catalog(self) -> Path:
        return self.plugin_root / "skills/onboarding/catalog.json"

    @property
    def sep_log_dir(self) -> Path:
        return self.project_root / "ai-docs/.squad-log"

    def onboarding_plan(self) -> OnboardingPlan:
        return build_onboarding_plan(self.project_root, self.onboarding_catalog)

    def dashboard_report(self, limit: int = 30) -> DashboardReport:
        return build_dashboard_report(self.sep_log_dir, limit)

    def ticket_plan(
        self,
        raw: str,
        ticket_json: Path | None = None,
        text_file: Path | None = None,
    ) -> TicketPlan:
        context = load_ticket_context(raw, ticket_json, text_file)
        return build_ticket_plan(context)


def create_client(
    project_root: str | Path = ".",
    plugin_root: str | Path = "plugins/claude-tech-squad",
) -> SquadSDK:
    return SquadSDK(project_root=Path(project_root), plugin_root=Path(plugin_root))
