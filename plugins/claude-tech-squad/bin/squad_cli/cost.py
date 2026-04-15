from __future__ import annotations

from dataclasses import dataclass, asdict

from squad_cli.models import RunState
from squad_cli.policy import RuntimePolicy


@dataclass
class CostReport:
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_total: int = 0
    estimated_cost_usd: float = 0.0
    budget_max: int = 0
    budget_percent: float = 0.0
    budget_warning: bool = False
    budget_halt: bool = False
    per_teammate: dict[str, dict] = None

    def __post_init__(self):
        if self.per_teammate is None:
            self.per_teammate = {}

    def to_dict(self) -> dict:
        return asdict(self)


def compute_cost(state: RunState, policy: RuntimePolicy) -> CostReport:
    report = CostReport()
    report.budget_max = state.token_budget.max_tokens

    for name, tm in state.teammates.items():
        report.tokens_in += tm.tokens_in
        report.tokens_out += tm.tokens_out
        tm_cost = (tm.tokens_in * 15 + tm.tokens_out * 75) / 1_000_000
        report.per_teammate[name] = {
            "tokens_in": tm.tokens_in,
            "tokens_out": tm.tokens_out,
            "cost_usd": round(tm_cost, 4),
            "duration_ms": tm.duration_ms,
        }

    report.tokens_total = report.tokens_in + report.tokens_out
    report.estimated_cost_usd = round((report.tokens_in * 15 + report.tokens_out * 75) / 1_000_000, 4)

    if report.budget_max > 0:
        report.budget_percent = (report.tokens_total / report.budget_max) * 100
    report.budget_warning = report.budget_percent >= policy.circuit_breaker_warn_percent()
    report.budget_halt = report.budget_percent >= policy.circuit_breaker_halt_percent()

    return report
