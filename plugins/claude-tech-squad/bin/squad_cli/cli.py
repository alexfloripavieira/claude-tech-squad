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


@main.command("onboarding-plan")
@click.option("--project-root", default=".", type=click.Path(exists=True))
@click.option(
    "--catalog",
    default="plugins/claude-tech-squad/skills/onboarding/catalog.json",
    type=click.Path(exists=True),
)
def onboarding_plan_cmd(project_root: str, catalog: str):
    from squad_cli.onboarding import build_onboarding_plan

    plan = build_onboarding_plan(Path(project_root), Path(catalog))
    _output(plan.to_dict())


@main.command("dashboard")
@click.option("--log-dir", default="ai-docs/.squad-log", type=click.Path())
@click.option("--output-md", default="ai-docs/dashboard-snapshot.md", type=click.Path())
@click.option("--output-html", default="ai-docs/dashboard.html", type=click.Path())
@click.option("--limit", default=30, type=int)
@click.option("--write-sep-log/--no-write-sep-log", default=True)
def dashboard_cmd(
    log_dir: str,
    output_md: str,
    output_html: str,
    limit: int,
    write_sep_log: bool,
):
    from squad_cli.dashboard import build_dashboard_report, write_dashboard_outputs

    report = build_dashboard_report(Path(log_dir), limit)
    outputs = write_dashboard_outputs(
        report,
        Path(output_md),
        Path(output_html) if output_html else None,
        Path(log_dir) if write_sep_log else None,
    )
    _output({"status": "written", "outputs": outputs, "report": report.to_dict()})


@main.command("ticket-plan")
@click.argument("ticket", required=False, default="")
@click.option("--ticket-json", default=None, type=click.Path(exists=True))
@click.option("--text-file", default=None, type=click.Path(exists=True))
@click.option("--write-sep-log/--no-write-sep-log", default=False)
@click.option("--fallback-used/--no-fallback-used", default=False)
@click.option("--log-dir", default="ai-docs/.squad-log", type=click.Path())
def ticket_plan_cmd(
    ticket: str,
    ticket_json: str | None,
    text_file: str | None,
    write_sep_log: bool,
    fallback_used: bool,
    log_dir: str,
):
    from squad_cli.ticket import (
        build_ticket_plans,
        load_ticket_contexts,
        write_from_ticket_sep_log,
    )

    contexts = load_ticket_contexts(
        ticket,
        Path(ticket_json) if ticket_json else None,
        Path(text_file) if text_file else None,
    )
    plans = build_ticket_plans(contexts)
    sep_logs = []
    if write_sep_log:
        sep_logs = [
            str(write_from_ticket_sep_log(plan, Path(log_dir), fallback_used=fallback_used))
            for plan in plans
        ]

    if len(plans) == 1:
        output = plans[0].to_dict()
        output["fallback_used"] = fallback_used
        if sep_logs:
            output["sep_log"] = sep_logs[0]
        _output(output)
        return

    _output(
        {
            "status": "planned",
            "count": len(plans),
            "fallback_used": fallback_used,
            "plans": [plan.to_dict() for plan in plans],
            "sep_logs": sep_logs,
        }
    )


@main.command("sdk-smoke")
@click.option("--project-root", default=".", type=click.Path(exists=True))
@click.option(
    "--plugin-root",
    default="plugins/claude-tech-squad",
    type=click.Path(exists=True),
)
def sdk_smoke_cmd(project_root: str, plugin_root: str):
    from squad_cli.sdk import create_client

    client = create_client(project_root=project_root, plugin_root=plugin_root)
    onboarding = client.onboarding_plan()
    dashboard = client.dashboard_report(limit=5)
    ticket = client.ticket_plan("PROJ-123")
    from_context = client.ticket_plan_from_context(ticket.extracted_context)
    _output(
        {
            "status": "ok",
            "onboarding_stack": onboarding.stack,
            "dashboard_logs_analyzed": dashboard.logs_analyzed,
            "ticket_source": ticket.source,
            "ticket_recommended_skill": ticket.recommended_skill,
            "ticket_context_skill": from_context.recommended_skill,
        }
    )


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


@main.group("test-gate")
def test_gate_group():
    """Mandatory test gate operations."""


@test_gate_group.command("evaluate")
@click.option("--skill", required=True)
@click.option("--run-id", required=True)
@click.option("--repo-root", default=".", type=click.Path(exists=True))
def test_gate_evaluate(skill: str, run_id: str, repo_root: str):
    import subprocess
    import yaml

    from squad_cli.test_gate import (
        GatePolicy,
        GateVerdict,
        StackFingerprint,
        check_paired_tests,
        evaluate_gate,
    )

    repo = Path(repo_root).resolve()
    try:
        diff = subprocess.check_output(
            ["git", "-C", str(repo), "diff", "--name-only", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().splitlines()
    except subprocess.CalledProcessError:
        diff = []

    policy_path = repo / "plugins/claude-tech-squad/runtime-policy.yaml"
    if not policy_path.exists():
        click.echo(f"test-gate: runtime-policy not found at {policy_path}", err=True)
        raise SystemExit(1)
    policy_yaml = yaml.safe_load(policy_path.read_text()) or {}
    mtg = policy_yaml.get("mandatory_test_gate", {})
    if skill not in mtg.get("skills_in_scope", []):
        click.echo(f"test-gate: {skill} not in scope; skip")
        raise SystemExit(0)

    stack = StackFingerprint(language="python")
    try:
        from squad_cli.stack_detect import detect_stack
        result = detect_stack(repo)
        stack_name = (result.stack or "").lower()
        if "django" in stack_name or "python" in stack_name or "rag" in stack_name:
            stack = StackFingerprint(language="python")
        elif "react" in stack_name or "vue" in stack_name or "next" in stack_name or "node" in stack_name:
            stack = StackFingerprint(language="typescript")
        elif "go" in stack_name:
            stack = StackFingerprint(language="go")
    except Exception:
        pass

    auto_generated_paths = mtg.get("auto_generated_paths", []) or []
    unpaired = check_paired_tests(diff, stack, repo, auto_generated_paths=auto_generated_paths)
    policy = GatePolicy(
        enforce_level=mtg.get("enforce_level", "warning"),
        coverage_warning_threshold=float(mtg.get("coverage_warning_threshold", 0.02)),
    )
    verdict = evaluate_gate(unpaired, 0.0, policy)
    click.echo(
        f"test-gate run_id={run_id} skill={skill} verdict={verdict.value} "
        f"unpaired={[u.path for u in unpaired]}"
    )
    if verdict == GateVerdict.BLOCKING:
        raise SystemExit(2)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
