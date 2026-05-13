import json
import os
import re
import subprocess
from pathlib import Path

from click.testing import CliRunner

from squad_cli.cli import main
from squad_cli.run_lifecycle import build_spawn_prompt, record_spawn, start_run


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
    assert "POLITICA DE IDIOMA:" in spawn["spawn_prompt"]
    assert "worktree_path: /tmp/cts-reviewer" in spawn["spawn_prompt"]
    assert "branch: cts/implement/reviewer-1" in spawn["spawn_prompt"]
    assert "base_commit: abc123" in spawn["spawn_prompt"]
    assert "Use portugues do Brasil" in spawn["spawn_prompt"]

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
    assert re.match(r"^\d{8}T\d{6}Z-implement-implement-[0-9a-f]{8}\.md$", Path(finished["sep_log"]).name)
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

    finished_again = invoke(
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
    assert finished_again["sep_log"] == finished["sep_log"]
    assert len(list(log_dir.glob("*-implement-*.md"))) == 1


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


def test_run_spawn_can_auto_create_worktree(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()

    def fake_run_helper(*, name, command, cwd, allow_failure):
        if name == "detect-team-mode":
            return {
                "name": name,
                "command": command,
                "exit_code": 0,
                "stdout": "mode=teammate tmux=1 inside_tmux=1 flag=1 version=2.1.32\n",
                "stderr": "",
            }
        if name == "spawn-agent-worktree":
            return {
                "name": name,
                "command": command,
                "exit_code": 0,
                "stdout": "path=/tmp/cts-reviewer branch=cts/implement/reviewer-1 base=abc123 spawned_at=1\n",
                "stderr": "",
            }
        raise AssertionError(f"unexpected helper: {name}")

    monkeypatch.setattr("squad_cli.run_lifecycle.run_helper", fake_run_helper)

    started, _ = start_run(
        skill="implement",
        task="auto worktree",
        state_dir=state_dir,
        plugin_root=plugin_root,
        policy_version="5.70.0",
    )

    run = record_spawn(
        state_dir=state_dir,
        run_id=started.run_id,
        agent="reviewer",
        subagent_type="claude-tech-squad:reviewer",
        worktree_path="",
        branch="",
        base_commit="",
        skill_branch="cts/skill/implement-1",
        peers=["tdd-specialist"],
        auto_create_worktree=True,
        plugin_root=plugin_root,
    )

    assert run.worktrees[0].worktree_path == "/tmp/cts-reviewer"
    assert run.worktrees[0].branch == "cts/implement/reviewer-1"
    assert run.worktrees[0].base_commit == "abc123"
    assert run.worktrees[0].skill_branch == "cts/skill/implement-1"
    assert run.worktrees[0].peers == ["tdd-specialist"]
    assert "skill_branch: cts/skill/implement-1" in run.worktrees[0].spawn_prompt
    assert "- tdd-specialist" in run.worktrees[0].spawn_prompt
    assert any(item["name"] == "spawn-agent-worktree" for item in run.helper_executions)


def test_dev_flow_tmux_gate_is_non_blocking_for_core_flows():
    hook = Path("plugins/claude-tech-squad/hooks/dev-flow-tmux-gate.sh")
    prompts = [
        "/claude-tech-squad:mini-squad entregar feature pequena",
        "/claude-tech-squad:discovery planejar feature",
        "/claude-tech-squad:implement",
        "/claude-tech-squad:squad entregar feature completa",
    ]

    for prompt in prompts:
        result = subprocess.run(
            ["bash", str(hook)],
            input=json.dumps({"prompt": prompt}),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "Reinicializar" not in result.stderr
        assert "Continuar inline" not in result.stderr


def test_detect_team_mode_stays_inline_outside_tmux(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "claude").write_text("#!/usr/bin/env bash\nprintf '2.1.32\\n'\n")
    (bin_dir / "tmux").write_text("#!/usr/bin/env bash\nexit 0\n")
    (bin_dir / "claude").chmod(0o755)
    (bin_dir / "tmux").chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
            "CLAUDE_CODE_TEAMMATE_MODE": "tmux",
        }
    )
    env.pop("TMUX", None)
    hook = Path("plugins/claude-tech-squad/bin/detect-team-mode.sh")
    result = subprocess.run(
        ["/usr/bin/bash", str(hook)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("mode=inline ")
    assert "tmux=1" in result.stdout
    assert "inside_tmux=0" in result.stdout


def test_mini_squad_smoke_stays_inline_with_tmux_installed_outside_session(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "claude").write_text("#!/usr/bin/env bash\nprintf '2.1.140\\n'\n")
    (bin_dir / "tmux").write_text("#!/usr/bin/env bash\nexit 0\n")
    (bin_dir / "claude").chmod(0o755)
    (bin_dir / "tmux").chmod(0o755)

    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_TEAMMATE_MODE", raising=False)

    hook = Path("plugins/claude-tech-squad/hooks/dev-flow-tmux-gate.sh")
    hook_result = subprocess.run(
        ["bash", str(hook)],
        input=json.dumps({"prompt": "/claude-tech-squad:mini-squad smoke"}),
        capture_output=True,
        text=True,
        check=False,
    )
    assert hook_result.returncode == 0, hook_result.stderr
    assert "Reinicializar" not in hook_result.stderr
    assert "Continuar inline" not in hook_result.stderr

    started = invoke(
        [
            "run",
            "start",
            "--skill",
            "mini-squad",
            "--task",
            "smoke inline sem tmux",
            "--run-id",
            "mini-smoke",
            "--state-dir",
            str(tmp_path / "state"),
            "--log-dir",
            str(tmp_path / "logs"),
            "--execution-mode",
            "auto",
        ]
    )

    assert started["execution_mode"] == "inline"
    assert started["resolved_team_mode"] == "inline"
    assert started["sep_log_path"].endswith("Z-mini-squad-mini-smoke.md")
    mode_helper = started["helper_executions"][0]["stdout"]
    assert "mode=inline" in mode_helper
    assert "tmux=1" in mode_helper
    assert "inside_tmux=0" in mode_helper


def test_run_mode_reports_inline_reason():
    output = invoke(["run", "mode"])

    assert output["status"] == "resolved"
    assert output["mode"] in {"inline", "teammate"}
    assert "reason" in output
    assert output["checks"]["tmux_binary"] in {True, False}
    assert output["checks"]["inside_tmux"] in {True, False}


def test_spawn_prompt_is_role_specific(tmp_path):
    run, _ = start_run(
        skill="mini-squad",
        task="entregar feature pequena",
        state_dir=tmp_path / "state",
        plugin_root=Path("plugins/claude-tech-squad"),
        run_id="role-test",
    )

    tdd_prompt = build_spawn_prompt(
        run=run,
        agent="tdd-specialist",
        subagent_type="claude-tech-squad:tdd-specialist",
        skill_branch="cts/skill/mini",
        worktree_path="/tmp/cts-tdd",
        branch="cts/mini/tdd",
        base_commit="abc123",
        peers=["dev"],
    )
    reviewer_prompt = build_spawn_prompt(
        run=run,
        agent="reviewer",
        subagent_type="claude-tech-squad:reviewer",
        skill_branch="cts/skill/mini",
        worktree_path="/tmp/cts-reviewer",
        branch="cts/mini/reviewer",
        base_commit="abc123",
        peers=[],
    )

    assert "Escreva o teste falhando antes" in tdd_prompt
    assert "Envie ao dev" in tdd_prompt
    assert "Revise o diff" in reviewer_prompt
    assert "Nao implemente novas funcionalidades" in reviewer_prompt


def test_mini_squad_e2e_governance_flow_without_agents(tmp_path):
    state_dir = tmp_path / "state"
    log_dir = tmp_path / "logs"

    started = invoke(
        [
            "run",
            "start",
            "--skill",
            "mini-squad",
            "--task",
            "feature pequena",
            "--run-id",
            "mini-e2e",
            "--state-dir",
            str(state_dir),
            "--log-dir",
            str(log_dir),
        ]
    )
    assert started["execution_mode"] == "inline"

    spawn = invoke(
        [
            "run",
            "spawn",
            "--run-id",
            "mini-e2e",
            "--agent",
            "tdd-specialist",
            "--subagent-type",
            "claude-tech-squad:tdd-specialist",
            "--manual-worktree",
            "--worktree-path",
            "/tmp/cts-tdd",
            "--branch",
            "cts/mini-squad/tdd",
            "--base-commit",
            "abc123",
            "--skill-branch",
            "cts/skill/mini-squad",
            "--peer",
            "dev",
            "--state-dir",
            str(state_dir),
        ]
    )
    assert "spawn_prompt" in spawn
    assert "PEERS:\n- dev" in spawn["spawn_prompt"]

    finished = invoke(
        [
            "run",
            "finish",
            "--run-id",
            "mini-e2e",
            "--status",
            "passed",
            "--state-dir",
            str(state_dir),
            "--log-dir",
            str(log_dir),
        ]
    )
    assert finished["sep_validation"]["status"] == "passed"
    assert re.match(r"^\d{8}T\d{6}Z-mini-squad-mini-e2e\.md$", Path(finished["sep_log"]).name)
    sep_text = Path(finished["sep_log"]).read_text()
    assert "skill: mini-squad" in sep_text
    assert "mode=inline" not in sep_text
