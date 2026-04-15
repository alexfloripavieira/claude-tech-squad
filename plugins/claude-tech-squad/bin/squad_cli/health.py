from __future__ import annotations

from squad_cli.models import HealthCheckResult, RunState, TeammateState
from squad_cli.policy import RuntimePolicy


def check_health(
    state: RunState,
    teammate_name: str,
    policy: RuntimePolicy,
) -> HealthCheckResult:
    result = HealthCheckResult(teammate=teammate_name)
    tm = state.teammates.get(teammate_name)
    if tm is None:
        return result

    _check_retry_detected(tm, result)
    _check_fallback_used(tm, result)
    _check_doom_loop_short_circuit(state, tm, result)
    _check_token_budget_pressure(state, policy, result)
    _check_low_confidence_chain(state, teammate_name, result)
    _check_blocking_findings_accumulating(state, result)

    result.context_enrichment = _build_enrichment(state, teammate_name, result)
    return result


def _check_retry_detected(tm: TeammateState, result: HealthCheckResult) -> None:
    if tm.retries >= 1:
        result.signals_triggered.append(f"retry_detected:{tm.name}:{tm.retries}")


def _check_fallback_used(tm: TeammateState, result: HealthCheckResult) -> None:
    if tm.fallback_used:
        result.signals_triggered.append(f"fallback_used:{tm.name}")


def _check_doom_loop_short_circuit(state: RunState, tm: TeammateState, result: HealthCheckResult) -> None:
    if state.doom_loops > 0 and tm.retries > 0:
        result.signals_triggered.append(f"doom_loop_short_circuit:{tm.name}")
        result.is_critical = True


def _check_token_budget_pressure(state: RunState, policy: RuntimePolicy, result: HealthCheckResult) -> None:
    budget = state.token_budget
    result.budget_percent = budget.percent_used
    warn_pct = policy.circuit_breaker_warn_percent()
    halt_pct = policy.circuit_breaker_halt_percent()

    if budget.percent_used >= halt_pct:
        result.signals_triggered.append(f"token_budget_halt:{budget.percent_used:.0f}%")
        result.budget_halt = True
        result.is_critical = True
    elif budget.percent_used >= warn_pct:
        result.signals_triggered.append(f"token_budget_pressure:{budget.percent_used:.0f}%")
        result.budget_warning = True


def _check_low_confidence_chain(state: RunState, current: str, result: HealthCheckResult) -> None:
    ordered = list(state.teammates.keys())
    idx = ordered.index(current) if current in ordered else -1
    if idx < 1:
        return

    low_count = 0
    for name in ordered[max(0, idx - 1) : idx + 1]:
        tm = state.teammates.get(name)
        if tm and tm.confidence == "low":
            low_count += 1

    if low_count >= 2:
        result.signals_triggered.append(f"low_confidence_chain:{low_count}")
        result.is_critical = True


def _check_blocking_findings_accumulating(state: RunState, result: HealthCheckResult) -> None:
    total = sum(tm.findings_blocking for tm in state.teammates.values())
    if total > 3:
        result.signals_triggered.append(f"blocking_findings_accumulating:{total}")
        result.is_critical = True


def _build_enrichment(state: RunState, current: str, result: HealthCheckResult) -> str:
    if not result.signals_triggered:
        return ""

    lines = ["## Health Context from Prior Teammates"]
    tm = state.teammates.get(current)
    if tm:
        retry_note = f" ({tm.retries} retries)" if tm.retries else ""
        lines.append(f"- {current} completed with confidence={tm.confidence}{retry_note}")

    pct = state.token_budget.percent_used
    if pct > 0:
        lines.append(f"- token budget at {pct:.0f}%")

    for sig in result.signals_triggered:
        if "token_budget_pressure" in sig:
            lines.append("- Produce concise output. Skip optional analysis. Focus on required deliverables only.")
        elif "low_confidence_chain" in sig:
            lines.append("- Multiple teammates are uncertain — validate your assumptions carefully")
        elif "doom_loop" in sig:
            lines.append("- A doom loop was detected earlier — do not repeat the same approach")
        elif "retry_detected" in sig:
            lines.append("- Previous teammate required retries — avoid the same pattern")

    return "\n".join(lines)
