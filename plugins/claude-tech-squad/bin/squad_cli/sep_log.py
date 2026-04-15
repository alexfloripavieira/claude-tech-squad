from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from squad_cli.models import RunState


def generate_sep_log(state: RunState, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{timestamp}-{state.skill}-{state.run_id}.md"
    path = output_dir / filename

    total_in = sum(tm.tokens_in for tm in state.teammates.values())
    total_out = sum(tm.tokens_out for tm in state.teammates.values())
    cost_usd = round((total_in * 15 + total_out * 75) / 1_000_000, 4)
    total_duration = sum(tm.duration_ms for tm in state.teammates.values())

    final_status = _determine_final_status(state)

    teammate_names = list(state.teammates.keys())
    reliability = {}
    for name, tm in state.teammates.items():
        reliability[name] = tm.reliability_state

    fallback_list = state.fallbacks if state.fallbacks else []

    frontmatter_lines = [
        "---",
        f"run_id: {state.run_id}",
        "parent_run_id: null",
        f"skill: {state.skill}",
        f"timestamp: {now.isoformat()}",
        f"status: {final_status}",
        f"final_status: {final_status}",
        "execution_mode: inline",
        "architecture_style: existing-repo-pattern",
        f"checkpoints: {state.completed_checkpoints}",
        f"fallbacks_invoked: {fallback_list}",
        f"runtime_policy_version: {state.policy_version}",
        f"feature_slug: {state.run_id}",
        f"checkpoint_cursor: {state.checkpoint_cursor}",
        f"completed_checkpoints: {state.completed_checkpoints}",
        "resume_from: null",
        f"gates_cleared: {state.gates_cleared}",
        f"gates_blocked: {state.gates_blocked}",
        f"retry_count: {sum(tm.retries for tm in state.teammates.values())}",
        f"fallback_invocations: {fallback_list}",
        "teammates:",
    ]
    for name in teammate_names:
        frontmatter_lines.append(f"  - {name}")

    frontmatter_lines.append("teammate_reliability:")
    for name, rel in reliability.items():
        frontmatter_lines.append(f"  {name}: {rel}")

    frontmatter_lines.extend(
        [
            f"tokens_input: {total_in}",
            f"tokens_output: {total_out}",
            f"estimated_cost_usd: {cost_usd}",
            f"total_duration_ms: {total_duration}",
            f"doom_loops_detected: {state.doom_loops}",
        ]
    )

    if state.escape_hatch_used:
        frontmatter_lines.append("escape_hatch_used: true")
        frontmatter_lines.append(f"skipped_phases: {state.skipped_phases}")

    frontmatter_lines.append("---")

    body_lines = [
        "",
        "## Output Digest",
        _generate_digest(state),
        "",
    ]

    if state.health_signals:
        body_lines.extend(
            [
                "## Health Signals",
                "",
            ]
        )
        for sig in state.health_signals:
            body_lines.append(f"- {sig}")

    content = "\n".join(frontmatter_lines + body_lines) + "\n"
    path.write_text(content)
    return path


def _determine_final_status(state: RunState) -> str:
    statuses = [tm.status for tm in state.teammates.values()]
    if all(s == "completed" for s in statuses):
        return "completed"
    if any(s == "failed" for s in statuses):
        return "failed"
    return "partial"


def _generate_digest(state: RunState) -> str:
    total_teammates = len(state.teammates)
    completed = sum(1 for tm in state.teammates.values() if tm.status == "completed")
    retries = sum(tm.retries for tm in state.teammates.values())

    parts = [f"{completed}/{total_teammates} teammates completed"]
    if retries:
        parts.append(f"{retries} retries")
    if state.doom_loops:
        parts.append(f"{state.doom_loops} doom loops detected")
    if state.fallbacks:
        parts.append(f"{len(state.fallbacks)} fallbacks invoked")

    return ". ".join(parts) + "."
