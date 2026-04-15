from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import click

from squad_cli.models import RunState, TokenBudget
from squad_cli.policy import RuntimePolicy


def _output(data: dict) -> None:
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


@click.group()
@click.version_option(version="0.1.0", prog_name="squad-cli")
def main():
    pass


@main.command()
@click.option(
    "--skill",
    required=True,
    help="Skill name (squad, implement, discovery, hotfix, bug-fix)",
)
@click.option(
    "--policy",
    required=True,
    type=click.Path(exists=True),
    help="Path to runtime-policy.yaml",
)
@click.option(
    "--project-root",
    default=".",
    type=click.Path(exists=True),
    help="Project root directory",
)
@click.option(
    "--state-dir", default=None, type=click.Path(), help="State directory override"
)
def preflight(skill: str, policy: str, project_root: str, state_dir: str | None):
    from squad_cli.preflight import run_preflight

    pol = RuntimePolicy.load(Path(policy))
    sd = Path(state_dir) if state_dir else None
    result = run_preflight(skill, pol, Path(project_root), sd)
    _output(result.to_dict())


@main.command()
@click.option("--run-id", required=True, help="Run ID")
@click.option("--skill", required=True, help="Skill name")
@click.option(
    "--policy",
    required=True,
    type=click.Path(exists=True),
    help="Path to runtime-policy.yaml",
)
@click.option(
    "--state-dir", default=".squad-state", type=click.Path(), help="State directory"
)
def init(run_id: str, skill: str, policy: str, state_dir: str):
    from squad_cli.preflight import run_preflight

    pol = RuntimePolicy.load(Path(policy))
    pf = run_preflight(skill, pol, Path("."))

    state = RunState(
        run_id=run_id,
        skill=skill,
        started_at=datetime.now(timezone.utc).isoformat(),
        policy_version=pol.version,
        stack=pf.stack,
        ai_feature=pf.ai_feature,
        routing=pf.routing,
        token_budget=TokenBudget(max_tokens=pf.token_budget_max),
    )

    sd = Path(state_dir)
    path = state.save(sd)
    _output(
        {"status": "initialized", "state_file": str(path), "preflight": pf.to_dict()}
    )


@main.command()
@click.option("--run-id", required=True)
@click.option("--teammate", required=True)
@click.option("--tokens-in", type=int, default=0)
@click.option("--tokens-out", type=int, default=0)
@click.option("--status", default="completed")
@click.option("--confidence", default="high")
@click.option("--retries", type=int, default=0)
@click.option("--fallback-used", is_flag=True, default=False)
@click.option("--findings-blocking", type=int, default=0)
@click.option("--duration-ms", type=int, default=0)
@click.option("--policy", required=True, type=click.Path(exists=True))
@click.option("--state-dir", default=".squad-state", type=click.Path())
def health(
    run_id: str,
    teammate: str,
    tokens_in: int,
    tokens_out: int,
    status: str,
    confidence: str,
    retries: int,
    fallback_used: bool,
    findings_blocking: int,
    duration_ms: int,
    policy: str,
    state_dir: str,
):
    from squad_cli.health import check_health

    sd = Path(state_dir)
    state_path = sd / f"{run_id}.json"
    if not state_path.exists():
        click.echo(json.dumps({"error": f"No state file for run {run_id}"}), err=True)
        sys.exit(1)

    state = RunState.load(state_path)
    state.record_teammate(
        teammate,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        status=status,
        confidence=confidence,
        retries=retries,
        fallback_used=fallback_used,
        findings_blocking=findings_blocking,
        duration_ms=duration_ms,
    )

    pol = RuntimePolicy.load(Path(policy))
    result = check_health(state, teammate, pol)

    if result.signals_triggered:
        state.health_signals.extend(result.signals_triggered)

    state.save(sd)
    _output(result.to_dict())


@main.command("doom-check")
@click.option("--prev-output", required=True, type=click.Path(exists=True))
@click.option("--curr-output", required=True, type=click.Path(exists=True))
@click.option("--prev-prev-output", default=None, type=click.Path(exists=True))
def doom_check(prev_output: str, curr_output: str, prev_prev_output: str | None):
    from squad_cli.doom_loop import check_doom_loop

    prev = Path(prev_output).read_text()
    curr = Path(curr_output).read_text()
    pp = Path(prev_prev_output).read_text() if prev_prev_output else None

    result = check_doom_loop(prev, curr, pp)
    _output(result.to_dict())


@main.command("checkpoint")
@click.argument("action", type=click.Choice(["save", "load", "resume", "list"]))
@click.option("--run-id", default=None)
@click.option("--cursor", default=None)
@click.option("--skill", default=None)
@click.option("--state-dir", default=".squad-state", type=click.Path())
def checkpoint_cmd(
    action: str,
    run_id: str | None,
    cursor: str | None,
    skill: str | None,
    state_dir: str,
):
    from squad_cli.checkpoint import (
        save_checkpoint,
        load_checkpoint,
        find_resumable,
        list_runs,
    )

    sd = Path(state_dir)

    if action == "save":
        if not run_id or not cursor:
            click.echo(
                json.dumps({"error": "--run-id and --cursor required for save"}),
                err=True,
            )
            sys.exit(1)
        state = RunState.load(sd / f"{run_id}.json")
        path = save_checkpoint(state, cursor, sd)
        _output({"status": "saved", "cursor": cursor, "path": str(path)})

    elif action == "load":
        if not run_id:
            click.echo(json.dumps({"error": "--run-id required for load"}), err=True)
            sys.exit(1)
        state = load_checkpoint(run_id, sd)
        if state:
            _output(state.to_dict())
        else:
            _output({"error": f"No state found for {run_id}"})

    elif action == "resume":
        if not skill:
            click.echo(json.dumps({"error": "--skill required for resume"}), err=True)
            sys.exit(1)
        state = find_resumable(skill, sd)
        if state:
            _output(
                {
                    "resumable": True,
                    "run_id": state.run_id,
                    "checkpoint_cursor": state.checkpoint_cursor,
                    "completed_checkpoints": state.completed_checkpoints,
                }
            )
        else:
            _output({"resumable": False})

    elif action == "list":
        runs = list_runs(sd)
        _output({"runs": runs})


@main.command("sep-log")
@click.option("--run-id", required=True)
@click.option("--output-dir", default="ai-docs/.squad-log", type=click.Path())
@click.option("--state-dir", default=".squad-state", type=click.Path())
def sep_log_cmd(run_id: str, output_dir: str, state_dir: str):
    from squad_cli.sep_log import generate_sep_log

    sd = Path(state_dir)
    state_path = sd / f"{run_id}.json"
    if not state_path.exists():
        click.echo(json.dumps({"error": f"No state file for run {run_id}"}), err=True)
        sys.exit(1)

    state = RunState.load(state_path)
    path = generate_sep_log(state, Path(output_dir))
    _output({"status": "written", "path": str(path)})


@main.command()
@click.option("--run-id", required=True)
@click.option("--policy", required=True, type=click.Path(exists=True))
@click.option("--state-dir", default=".squad-state", type=click.Path())
def cost(run_id: str, policy: str, state_dir: str):
    from squad_cli.cost import compute_cost

    sd = Path(state_dir)
    state_path = sd / f"{run_id}.json"
    if not state_path.exists():
        click.echo(json.dumps({"error": f"No state file for run {run_id}"}), err=True)
        sys.exit(1)

    state = RunState.load(state_path)
    pol = RuntimePolicy.load(Path(policy))
    report = compute_cost(state, pol)
    _output(report.to_dict())


@main.command("dry-run")
@click.option("--skill", required=True)
@click.option("--policy", required=True, type=click.Path(exists=True))
@click.option("--project-root", default=".", type=click.Path(exists=True))
def dry_run_cmd(skill: str, policy: str, project_root: str):
    from squad_cli.dry_run import dry_run

    pol = RuntimePolicy.load(Path(policy))
    output = dry_run(skill, pol, Path(project_root))
    click.echo(output)


@main.command()
@click.option("--run-id", required=True)
@click.option("--key", required=True, help="Memory key: 'shared' or teammate name")
@click.option("--content", default=None, help="Content to save (or use stdin)")
@click.option("--append", is_flag=True, default=False)
@click.option("--state-dir", default=".squad-state", type=click.Path())
def memory(run_id: str, key: str, content: str | None, append: bool, state_dir: str):
    from squad_cli.task_memory import save_memory, get_memory

    sd = Path(state_dir)
    state_path = sd / f"{run_id}.json"
    if not state_path.exists():
        click.echo(json.dumps({"error": f"No state file for run {run_id}"}), err=True)
        sys.exit(1)

    state = RunState.load(state_path)

    if content is not None:
        save_memory(state, key, content, append)
        state.save(sd)
        _output({"status": "saved", "key": key})
    else:
        if not sys.stdin.isatty():
            stdin_content = sys.stdin.read()
            save_memory(state, key, stdin_content, append)
            state.save(sd)
            _output({"status": "saved", "key": key})
        else:
            mem = get_memory(state, key)
            _output({"key": key, "content": mem})


if __name__ == "__main__":
    main()
