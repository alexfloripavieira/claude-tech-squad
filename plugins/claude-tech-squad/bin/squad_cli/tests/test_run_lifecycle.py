import json
from pathlib import Path

from click.testing import CliRunner

from squad_cli.cli import main


def invoke(args):
    runner = CliRunner()
    result = runner.invoke(main, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_run_lifecycle_records_complete_governance_flow(tmp_path):
    state_dir = tmp_path / "state"
    log_dir = tmp_path / "logs"

    started = invoke(
        [
            "run",
            "start",
            "--skill",
            "implement",
            "--task",
            "entregar governança automática",
            "--state-dir",
            str(state_dir),
            "--log-dir",
            str(log_dir),
            "--policy-version",
            "5.70.0",
        ]
    )

    run_id = started["run_id"]
    assert started["status"] == "started"
    assert started["language_policy_applied"] == "pt-BR"
    assert started["execution_mode"] == "inline"
    assert started["resolved_team_mode"] == "inline"
    assert started["helper_executions"][0]["name"] == "detect-team-mode"
    assert Path(started["state_file"]).exists()

    event = invoke(
        [
            "run",
            "event",
            "--run-id",
            run_id,
            "--type",
            "command",
            "--value",
            "bash scripts/validate.sh",
            "--state-dir",
            str(state_dir),
        ]
    )
    assert event["status"] == "recorded"

    gate = invoke(
        [
            "run",
            "gate",
            "--run-id",
            run_id,
            "--name",
            "reviewer-bypass",
            "--status",
            "blocked",
            "--reason",
            "reviewer não respondeu",
            "--state-dir",
            str(state_dir),
        ]
    )
    assert gate["status"] == "recorded"

    checkpoint = invoke(
        [
            "run",
            "checkpoint",
            "--run-id",
            run_id,
            "--step",
            "preflight-passed",
            "--artifact",
            "ai-docs/example.md",
            "--state-dir",
            str(state_dir),
        ]
    )
    assert checkpoint["status"] == "recorded"

    spawn = invoke(
        [
            "run",
            "spawn",
            "--run-id",
            run_id,
            "--agent",
            "reviewer",
            "--subagent-type",
            "claude-tech-squad:reviewer",
            "--worktree-path",
            "/tmp/cts-reviewer",
            "--branch",
            "cts/implement/reviewer-1",
            "--base-commit",
            "abc123",
            "--state-dir",
            str(state_dir),
        ]
    )
    assert spawn["status"] == "recorded"
    assert "language_policy.spawn_prompt_preamble" in spawn["prompt_requirements"]

    done = invoke(
        [
            "run",
            "agent-done",
            "--run-id",
            run_id,
            "--agent",
            "reviewer",
            "--status",
            "completed",
            "--confidence",
            "high",
            "--tokens-in",
            "10",
            "--tokens-out",
            "20",
            "--merged",
            "true",
            "--commits-ahead",
            "1",
            "--state-dir",
            str(state_dir),
        ]
    )
    assert done["status"] == "recorded"

    finished = invoke(
        [
            "run",
            "finish",
            "--run-id",
            run_id,
            "--status",
            "passed",
            "--state-dir",
            str(state_dir),
            "--log-dir",
            str(log_dir),
        ]
    )
    assert finished["status"] == "finished"
    assert Path(finished["sep_log"]).exists()
    assert finished["sep_validation"]["status"] == "passed"

    report = invoke(
        [
            "run",
            "report",
            "--run-id",
            run_id,
            "--state-dir",
            str(state_dir),
        ]
    )
    assert report["run_id"] == run_id
    assert report["status"] == "passed"
    assert report["events_count"] == 1
    assert report["gates_count"] == 1
    assert report["checkpoints"] == ["preflight-passed"]
    assert report["worktrees"][0]["agent"] == "reviewer"
    assert report["resolved_team_mode"] == "inline"
    assert report["sep_validation"]["status"] == "passed"

    sep_text = Path(finished["sep_log"]).read_text()
    assert "language_policy_applied: pt-BR" in sep_text
    assert "cts_phases_completed:" in sep_text
    assert "worktrees:" in sep_text


def test_run_start_can_emit_helper_commands_for_full_runtime(tmp_path):
    state_dir = tmp_path / "state"
    output = invoke(
        [
            "run",
            "start",
            "--skill",
            "squad",
            "--task",
            "feature completa",
            "--state-dir",
            str(state_dir),
        ]
    )

    assert output["helper_commands"]["skill_init"].endswith("init-skill-branch.sh squad")
    assert output["helper_commands"]["detect_mode"].endswith("detect-team-mode.sh")
