from __future__ import annotations

import json
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
LANGUAGE_POLICY = "pt-BR"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GovernanceEvent:
    event_type: str
    value: str
    timestamp: str = field(default_factory=now_iso)


@dataclass
class GovernanceGate:
    name: str
    status: str
    reason: str = ""
    timestamp: str = field(default_factory=now_iso)


@dataclass
class GovernanceCheckpoint:
    step: str
    artifact: str = ""
    timestamp: str = field(default_factory=now_iso)


@dataclass
class GovernanceWorktree:
    agent: str
    subagent_type: str
    worktree_path: str
    branch: str
    base_commit: str
    skill_branch: str = ""
    peers: list[str] = field(default_factory=list)
    spawn_prompt: str = ""
    status: str = "spawned"
    confidence: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    merged: bool = False
    commits_ahead: int = 0
    completed_at: str = ""


@dataclass
class GovernanceRun:
    run_id: str
    skill: str
    task: str
    status: str = "in_progress"
    schema_version: int = SCHEMA_VERSION
    started_at: str = field(default_factory=now_iso)
    ended_at: str = ""
    policy_version: str = ""
    execution_mode: str = "inline"
    language_policy_applied: str = LANGUAGE_POLICY
    cts_phases_completed: list[str] = field(default_factory=list)
    events: list[GovernanceEvent] = field(default_factory=list)
    gates: list[GovernanceGate] = field(default_factory=list)
    checkpoints: list[GovernanceCheckpoint] = field(default_factory=list)
    worktrees: list[GovernanceWorktree] = field(default_factory=list)
    helper_commands: dict[str, str] = field(default_factory=dict)
    quick_start: list[str] = field(default_factory=list)
    helper_executions: list[dict[str, Any]] = field(default_factory=list)
    resolved_team_mode: str = ""
    sep_validation: dict[str, Any] = field(default_factory=dict)
    sep_log_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GovernanceRun":
        data = dict(data)
        data["events"] = [GovernanceEvent(**item) for item in data.get("events", [])]
        data["gates"] = [GovernanceGate(**item) for item in data.get("gates", [])]
        data["checkpoints"] = [
            GovernanceCheckpoint(**item) for item in data.get("checkpoints", [])
        ]
        data["worktrees"] = [
            GovernanceWorktree(**item) for item in data.get("worktrees", [])
        ]
        return cls(**data)

    def save(self, state_dir: Path) -> Path:
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_file(state_dir, self.run_id)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))
        return path


def state_file(state_dir: Path, run_id: str) -> Path:
    return state_dir / f"{run_id}.run.json"


def load_run(state_dir: Path, run_id: str) -> GovernanceRun:
    return GovernanceRun.from_dict(json.loads(state_file(state_dir, run_id).read_text()))


def make_run_id(skill: str) -> str:
    return f"{skill}-{uuid.uuid4().hex[:8]}"


def helper_commands(plugin_root: Path, skill: str) -> dict[str, str]:
    bin_dir = plugin_root / "bin"
    return {
        "detect_mode": f"bash {bin_dir / 'detect-team-mode.sh'}",
        "skill_init": f"bash {bin_dir / 'init-skill-branch.sh'} {skill}",
        "spawn_template": (
            f"bash {bin_dir / 'spawn-agent-worktree.sh'} "
            f"{skill} <agent> <agent_id>"
        ),
        "cleanup_template": (
            f"CTS_LEAD_OK=1 bash {bin_dir / 'cleanup-agent-worktree.sh'} "
            "<worktree_path>"
        ),
        "finalize_template": f"bash {bin_dir / 'finalize-skill.sh'} <skill_branch>",
        "validate_sep_log_template": (
            f"python3 {bin_dir / 'validate-sep-log.py'} <sep_log_path>"
        ),
    }


def start_run(
    *,
    skill: str,
    task: str,
    state_dir: Path,
    plugin_root: Path,
    run_id: str | None = None,
    policy_version: str = "",
    execution_mode: str = "inline",
) -> tuple[GovernanceRun, Path]:
    plugin_root = plugin_root.resolve()
    quick_start = [
        f"Use `run spawn` for each agent you want to govern under `{skill}`.",
        "Use `run event` to record commands and evidence as they happen.",
        "Use `run checkpoint` at phase boundaries.",
        "Use `run agent-done` when an agent returns.",
        "Use `run finish` and then `run report` to close the loop.",
    ]
    run = GovernanceRun(
        run_id=run_id or make_run_id(skill),
        skill=skill,
        task=task,
        policy_version=policy_version,
        helper_commands=helper_commands(plugin_root, skill),
        quick_start=quick_start,
        cts_phases_completed=["run-start"],
    )
    resolved_mode = execution_mode if execution_mode != "auto" else "inline"
    detect_mode = plugin_root / "bin" / "detect-team-mode.sh"
    helper_result = run_helper(
        name="detect-team-mode",
        command=["bash", str(detect_mode)],
        cwd=plugin_root,
        allow_failure=True,
    )
    run.helper_executions.append(helper_result)
    parsed_mode = _parse_team_mode(helper_result.get("stdout", ""))
    if parsed_mode:
        resolved_mode = parsed_mode
    run.execution_mode = resolved_mode
    run.resolved_team_mode = resolved_mode
    return run, run.save(state_dir)


def resolve_team_mode(*, plugin_root: Path) -> dict[str, Any]:
    plugin_root = plugin_root.resolve()
    detect_mode = plugin_root / "bin" / "detect-team-mode.sh"
    helper_result = run_helper(
        name="detect-team-mode",
        command=["bash", str(detect_mode)],
        cwd=plugin_root,
        allow_failure=True,
    )
    parsed = _parse_key_values(helper_result.get("stdout", ""))
    mode = parsed.get("mode", "inline")
    checks = {
        "tmux_binary": parsed.get("tmux") == "1",
        "inside_tmux": parsed.get("inside_tmux") == "1",
        "agent_teams_env": parsed.get("flag") == "1",
        "claude_version": parsed.get("version", "unknown"),
    }
    reason = _mode_reason(mode, checks)
    return {
        "status": "resolved",
        "mode": mode,
        "reason": reason,
        "checks": checks,
        "raw": parsed,
        "helper_execution": helper_result,
    }


def record_event(
    *, state_dir: Path, run_id: str, event_type: str, value: str
) -> GovernanceRun:
    run = load_run(state_dir, run_id)
    run.events.append(GovernanceEvent(event_type=event_type, value=value))
    _add_phase(run, "event-recorded")
    run.save(state_dir)
    return run


def record_gate(
    *, state_dir: Path, run_id: str, name: str, status: str, reason: str
) -> GovernanceRun:
    run = load_run(state_dir, run_id)
    run.gates.append(GovernanceGate(name=name, status=status, reason=reason))
    _add_phase(run, "gate-recorded")
    run.save(state_dir)
    return run


def record_checkpoint(
    *, state_dir: Path, run_id: str, step: str, artifact: str
) -> GovernanceRun:
    run = load_run(state_dir, run_id)
    run.checkpoints.append(GovernanceCheckpoint(step=step, artifact=artifact))
    _add_phase(run, step)
    run.save(state_dir)
    return run


def record_spawn(
    *,
    state_dir: Path,
    run_id: str,
    agent: str,
    subagent_type: str,
    worktree_path: str,
    branch: str,
    base_commit: str,
    skill_branch: str = "",
    peers: list[str] | None = None,
    auto_create_worktree: bool = False,
    plugin_root: Path | None = None,
) -> GovernanceRun:
    run = load_run(state_dir, run_id)
    if plugin_root is not None:
        plugin_root = plugin_root.resolve()
    resolved_peers = peers or []
    if auto_create_worktree and (not worktree_path or not branch or not base_commit):
        if plugin_root is None:
            raise ValueError("plugin_root is required when auto_create_worktree is enabled")
        spawn_result = run_helper(
            name="spawn-agent-worktree",
            command=[
                "bash",
                str(plugin_root / "bin" / "spawn-agent-worktree.sh"),
                run.skill,
                agent,
                run_id,
            ],
            cwd=plugin_root,
            allow_failure=False,
        )
        parsed = _parse_key_values(spawn_result["stdout"])
        worktree_path = worktree_path or parsed.get("path", "")
        branch = branch or parsed.get("branch", "")
        base_commit = base_commit or parsed.get("base", "")
        run.helper_executions.append(spawn_result)
        run.helper_commands["spawn_auto"] = "bash plugins/claude-tech-squad/bin/spawn-agent-worktree.sh <skill> <agent> <run_id>"
    if not skill_branch and plugin_root is not None:
        branch_result = run_helper(
            name="current-skill-branch",
            command=["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=plugin_root,
            allow_failure=True,
        )
        if branch_result["exit_code"] == 0:
            skill_branch = branch_result["stdout"].strip()
        run.helper_executions.append(branch_result)
    existing = _find_worktree(run, agent)
    spawn_prompt = build_spawn_prompt(
        run=run,
        agent=agent,
        subagent_type=subagent_type,
        skill_branch=skill_branch,
        worktree_path=worktree_path,
        branch=branch,
        base_commit=base_commit,
        peers=resolved_peers,
    )
    worktree = GovernanceWorktree(
        agent=agent,
        subagent_type=subagent_type,
        worktree_path=worktree_path,
        branch=branch,
        base_commit=base_commit,
        skill_branch=skill_branch,
        peers=resolved_peers,
        spawn_prompt=spawn_prompt,
    )
    if existing is None:
        run.worktrees.append(worktree)
    else:
        run.worktrees[existing] = worktree
    _add_phase(run, "agent-spawned")
    run.save(state_dir)
    return run


def build_spawn_prompt(
    *,
    run: GovernanceRun,
    agent: str,
    subagent_type: str,
    skill_branch: str,
    worktree_path: str,
    branch: str,
    base_commit: str,
    peers: list[str],
) -> str:
    peer_lines = "\n".join(f"- {peer}" for peer in peers) if peers else "- none"
    role_guidance = _role_guidance(agent=agent, subagent_type=subagent_type, peers=peers)
    return "\n".join(
        [
            "POLITICA DE IDIOMA:",
            "Use portugues do Brasil (pt-BR) em toda comunicacao natural com o lead, com outros agentes e no result_contract.",
            "Mantenha codigo, comandos, caminhos, identificadores, chaves YAML/JSON e mensagens de commit em ingles quando fizer sentido tecnico.",
            "",
            "CONTEXTO DE GOVERNANCA:",
            f"run_id: {run.run_id}",
            f"skill: {run.skill}",
            f"task: {run.task}",
            f"agent: {agent}",
            f"subagent_type: {subagent_type}",
            f"execution_mode: {run.execution_mode}",
            "",
            "WORKTREE:",
            f"skill_branch: {skill_branch}",
            f"worktree_path: {worktree_path}",
            f"branch: {branch}",
            f"base_commit: {base_commit}",
            "instruction: cd into worktree_path before any Read/Edit/Write/Bash. Keep all file changes inside that worktree. Do not edit the lead checkout.",
            "",
            "PEERS:",
            peer_lines,
            "",
            "CROSS-TALK:",
            "Fale diretamente com os peers quando houver dependencia de entendimento, teste, contrato ou revisao. Use pt-BR nessas mensagens.",
            "Se precisar entregar arquivos entre worktrees, envie from_branch, commit_sha e file_paths para o peer.",
            "",
            "INSTRUCOES DO PAPEL:",
            role_guidance,
            "",
            "RESULTADO:",
            "Retorne result_contract e verification_checklist. Inclua evidencias objetivas de testes, arquivos tocados, bloqueios e proxima acao.",
        ]
    )


def record_agent_done(
    *,
    state_dir: Path,
    run_id: str,
    agent: str,
    status: str,
    confidence: str,
    tokens_in: int,
    tokens_out: int,
    merged: bool,
    commits_ahead: int,
) -> GovernanceRun:
    run = load_run(state_dir, run_id)
    index = _find_worktree(run, agent)
    if index is None:
        run.worktrees.append(
            GovernanceWorktree(
                agent=agent,
                subagent_type="",
                worktree_path="",
                branch="",
                base_commit="",
            )
        )
        index = len(run.worktrees) - 1
    worktree = run.worktrees[index]
    worktree.status = status
    worktree.confidence = confidence
    worktree.tokens_in = tokens_in
    worktree.tokens_out = tokens_out
    worktree.merged = merged
    worktree.commits_ahead = commits_ahead
    worktree.completed_at = now_iso()
    _add_phase(run, "agent-done")
    run.save(state_dir)
    return run


def finish_run(
    *, state_dir: Path, run_id: str, status: str, log_dir: Path
) -> tuple[GovernanceRun, Path]:
    run = load_run(state_dir, run_id)
    run.status = status
    run.ended_at = now_iso()
    _add_phase(run, "run-finish")
    run.save(state_dir)
    sep_path = write_sep_log(run, log_dir)
    run.sep_log_path = str(sep_path)
    validation_path = sep_path if sep_path.is_absolute() else Path.cwd() / sep_path
    validation = run_helper(
        name="validate-sep-log",
        command=["python3", str(Path(__file__).resolve().parents[1] / "validate-sep-log.py"), str(validation_path)],
        cwd=state_dir,
        allow_failure=False,
    )
    run.helper_executions.append(validation)
    run.sep_validation = {
        "status": "passed" if validation["exit_code"] == 0 else "failed",
        "command": validation["command"],
        "output": validation["stdout"].strip(),
    }
    run.save(state_dir)
    return run, sep_path


def generate_public_surface_docs() -> dict[str, str]:
    script = Path(__file__).resolve().parents[4] / "scripts" / "render-public-surface-docs.py"
    table = subprocess.run(
        ["python3", str(script), "table"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    daily = subprocess.run(
        ["python3", str(script), "daily-flow"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    quick = subprocess.run(
        ["python3", str(script), "quick-reference"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {"table": table, "daily_flow": daily, "quick_reference": quick}


def report_run(*, state_dir: Path, run_id: str) -> dict[str, Any]:
    run = load_run(state_dir, run_id)
    return {
        "run_id": run.run_id,
        "skill": run.skill,
        "task": run.task,
        "status": run.status,
        "schema_version": run.schema_version,
        "execution_mode": run.execution_mode,
        "language_policy_applied": run.language_policy_applied,
        "events_count": len(run.events),
        "gates_count": len(run.gates),
        "checkpoints": [checkpoint.step for checkpoint in run.checkpoints],
        "worktrees": [asdict(worktree) for worktree in run.worktrees],
        "cts_phases_completed": run.cts_phases_completed,
        "helper_commands": run.helper_commands,
        "quick_start": run.quick_start,
        "resolved_team_mode": run.resolved_team_mode,
        "sep_validation": run.sep_validation,
        "sep_log_path": run.sep_log_path,
        "helper_executions": run.helper_executions,
    }


def write_sep_log(run: GovernanceRun, log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = _sep_log_path(run, log_dir)
    tokens_in = sum(worktree.tokens_in for worktree in run.worktrees)
    tokens_out = sum(worktree.tokens_out for worktree in run.worktrees)
    cost_usd = round((tokens_in * 15 + tokens_out * 75) / 1_000_000, 4)
    duration_ms = _duration_ms(run.started_at, run.ended_at)
    passed_gates = [gate for gate in run.gates if gate.status == "passed"]
    blocked_gates = [gate for gate in run.gates if gate.status != "passed"]

    def yaml_list(header: str, values: list[str]) -> list[str]:
        if not values:
            return [f"{header}: []"]
        return [f"{header}:", *[f"  - {value}" for value in values]]

    def yaml_map(header: str, values: list[str]) -> list[str]:
        if not values:
            return [f"{header}: {{}}"]
        return [f"{header}:", *values]

    lines = [
        "---",
        f"schema_version: {run.schema_version}",
        f"run_id: {run.run_id}",
        "parent_run_id: null",
        f"skill: {run.skill}",
        f"timestamp: {run.started_at}",
        f"status: {run.status}",
        f"final_status: {run.status}",
        f"execution_mode: {run.execution_mode}",
        "architecture_style: existing-repo-pattern",
        f"runtime_policy_version: {run.policy_version}",
        f"language_policy_applied: {run.language_policy_applied}",
        f"feature_slug: {run.run_id}",
        "checkpoint_cursor: null",
    ]
    lines.extend(yaml_list("completed_checkpoints", [checkpoint.step for checkpoint in run.checkpoints]))
    lines.extend(
        [
            *yaml_list("cts_phases_completed", run.cts_phases_completed),
            *yaml_list("checkpoints", [checkpoint.step for checkpoint in run.checkpoints]),
            *yaml_list("gates_cleared", [gate.name for gate in passed_gates]),
            *yaml_list("gates_blocked", [f"{gate.name}: {gate.reason}" for gate in blocked_gates]),
            "bypasses_observed: []",
            "timeouts_observed: []",
            "fallbacks_invoked: []",
            "fallback_invocations: []",
            *yaml_list("teammates", [worktree.agent for worktree in run.worktrees]),
            *yaml_map("teammate_reliability", [f"  {worktree.agent}: primary" for worktree in run.worktrees]),
            *yaml_list(
                "worktrees",
                [
                    (
                        f"agent: {worktree.agent}\n"
                        f"    path: {worktree.worktree_path}\n"
                        f"    branch: {worktree.branch}\n"
                        f"    status: {worktree.status}\n"
                        f"    merged: {str(worktree.merged).lower()}\n"
                        f"    commits_ahead: {worktree.commits_ahead}"
                    )
                    for worktree in run.worktrees
                ],
            ),
            f"events_count: {len(run.events)}",
            f"gates_count: {len(run.gates)}",
            f"tokens_input: {tokens_in}",
            f"tokens_output: {tokens_out}",
            f"estimated_cost_usd: {cost_usd}",
            f"total_duration_ms: {duration_ms}",
            "doom_loops_detected: 0",
            "---",
            "",
            "## Output Digest",
            "",
            (
                f"Governança automática finalizada para `{run.skill}` com "
                f"{len(run.worktrees)} worktree(s), {len(run.gates)} gate(s) e "
                f"{len(run.checkpoints)} checkpoint(s)."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines))
    return path


def _sep_log_path(run: GovernanceRun, log_dir: Path) -> Path:
    if run.sep_log_path:
        return Path(run.sep_log_path)
    return log_dir / sep_log_filename(run)


def sep_log_filename(run: GovernanceRun) -> str:
    timestamp = _compact_utc_timestamp(run.started_at)
    return f"{timestamp}-{run.skill}-{run.run_id}.md"


def _compact_utc_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    parsed = parsed.astimezone(timezone.utc)
    return parsed.strftime("%Y%m%dT%H%M%SZ")


def prompt_requirements() -> list[str]:
    return [
        "language_policy.spawn_prompt_preamble",
        "agent_worktrees.spawn_prompt_inject",
        "cross_talk.pt_br_only",
        "sep_log.lifecycle_required",
    ]


def _role_guidance(*, agent: str, subagent_type: str, peers: list[str]) -> str:
    role = f"{agent} {subagent_type}".lower()
    peer_hint = ", ".join(peers) if peers else "nenhum peer obrigatorio"
    if "tdd" in role:
        return "\n".join(
            [
                "Escreva o teste falhando antes de qualquer implementacao.",
                f"Envie ao dev/peer ({peer_hint}) a assinatura do teste, asserts principais e arquivos afetados antes de finalizar.",
                "Comite o teste falhando no seu worktree quando fizer handoff de arquivo.",
            ]
        )
    if "review" in role or "reviewer" in role:
        return "\n".join(
            [
                "Revise o diff e as evidencias produzidas pelos agentes anteriores.",
                "Nao implemente novas funcionalidades. Foque em riscos, regressao, cobertura, seguranca e aderencia ao escopo.",
                "Classifique achados como BLOCKING, WARNING ou INFO.",
            ]
        )
    if any(token in role for token in ("dev", "developer", "backend", "frontend", "python", "typescript", "django", "react", "vue")):
        return "\n".join(
            [
                "Implemente apenas o minimo necessario para satisfazer o teste/contrato aprovado.",
                f"Converse com os peers ({peer_hint}) antes de alterar contratos compartilhados.",
                "Rode os testes relevantes e registre o comando exato no result_contract.",
            ]
        )
    return "\n".join(
        [
            "Execute somente o escopo do seu papel.",
            f"Use cross-talk direto com peers quando necessario ({peer_hint}).",
            "Registre evidencias objetivas no result_contract.",
        ]
    )


def _mode_reason(mode: str, checks: dict[str, Any]) -> str:
    if mode == "teammate":
        return "Claude Code is running inside tmux with Agent Teams enabled."
    if not checks["tmux_binary"]:
        return "tmux is not installed; inline mode is the default."
    if not checks["inside_tmux"]:
        return "Claude Code is not running inside tmux; inline mode is the default."
    if not checks["agent_teams_env"]:
        return "Agent Teams environment flags are not enabled; inline mode is the default."
    return "Claude Code version is unavailable or below the teammate-mode minimum; inline mode is the default."


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "sim"}


def run_helper(
    *,
    name: str,
    command: list[str],
    cwd: Path,
    allow_failure: bool,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    result = {
        "name": name,
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0 and not allow_failure:
        raise RuntimeError(
            f"helper {name} failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    return result


def _add_phase(run: GovernanceRun, phase: str) -> None:
    if phase not in run.cts_phases_completed:
        run.cts_phases_completed.append(phase)


def _find_worktree(run: GovernanceRun, agent: str) -> int | None:
    for index, worktree in enumerate(run.worktrees):
        if worktree.agent == agent:
            return index
    return None


def _duration_ms(started_at: str, ended_at: str) -> int:
    if not started_at or not ended_at:
        return 0
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at)
    except ValueError:
        return 0
    return max(0, int((end - start).total_seconds() * 1000))


def _parse_team_mode(output: str) -> str:
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("mode="):
            mode = line.split("=", 1)[1].strip()
            if mode in {"inline", "teammate"}:
                return mode
    return ""


def _parse_key_values(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for token in output.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        result[key.strip()] = value.strip()
    return result
