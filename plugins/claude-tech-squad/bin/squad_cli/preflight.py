from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from squad_cli.models import PreflightResult, RunState
from squad_cli.policy import RuntimePolicy
from squad_cli.stack_detect import detect_stack


def run_preflight(
    skill: str,
    policy: RuntimePolicy,
    project_root: Path,
    state_dir: Path | None = None,
) -> PreflightResult:
    result = PreflightResult()
    result.policy_version = policy.version
    result.token_budget_max = policy.token_budget(skill)

    stack_result = detect_stack(project_root)
    result.stack = stack_result.stack
    result.ai_feature = stack_result.ai_feature
    result.routing = stack_result.routing
    result.lint_profile = stack_result.lint_profile

    _check_docs_lookup(result)
    _check_orphans(policy, project_root, result)
    _check_retro_counter(policy, project_root, result)
    _check_resume(skill, project_root, state_dir, result)

    return result


def _check_docs_lookup(result: PreflightResult) -> None:
    try:
        import importlib

        importlib.import_module("mcp_plugin_context7")
        result.docs_lookup_mode = "context7"
    except (ImportError, ModuleNotFoundError):
        result.docs_lookup_mode = "repo-fallback"
        result.warnings.append("Context7 unavailable — using repository evidence and explicit assumptions")


def _check_orphans(policy: RuntimePolicy, project_root: Path, result: PreflightResult) -> None:
    if not policy.orphan_detection_enabled():
        return

    log_dir = project_root / "ai-docs" / ".squad-log"
    if not log_dir.exists():
        return

    stale_days = policy.orphan_stale_days()
    cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
    count = 0

    for log_file in sorted(log_dir.glob("*-discovery-*.md")):
        frontmatter = _parse_frontmatter(log_file)
        if not frontmatter:
            continue

        if frontmatter.get("implement_triggered") is False:
            timestamp_str = frontmatter.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(timestamp_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    count += 1
            except (ValueError, TypeError):
                count += 1

    result.orphaned_discoveries = count
    if count > 0:
        result.warnings.append(f"{count} orphaned discovery(ies) found older than {stale_days} days")


def _check_retro_counter(policy: RuntimePolicy, project_root: Path, result: PreflightResult) -> None:
    counter_path = project_root / policy.retro_counter_file()
    threshold = policy.retro_trigger_after_runs()
    result.retro_threshold = threshold

    if not counter_path.exists():
        result.retro_counter = 0
        return

    try:
        value = int(counter_path.read_text().strip())
        result.retro_counter = value
        if value >= threshold:
            result.warnings.append(f"{value} runs since last retrospective — recommend running /factory-retrospective")
    except (ValueError, OSError):
        result.retro_counter = 0


def _check_resume(
    skill: str,
    project_root: Path,
    state_dir: Path | None,
    result: PreflightResult,
) -> None:
    if state_dir is None:
        state_dir = project_root / ".squad-state"

    if not state_dir.exists():
        return

    candidates = []
    for state_file in state_dir.glob("*.json"):
        try:
            state = RunState.load(state_file)
            if state.skill == skill and state.checkpoint_cursor:
                candidates.append((state_file, state))
        except (Exception,):
            continue

    if not candidates:
        return

    candidates.sort(key=lambda x: x[1].started_at, reverse=True)
    _, latest = candidates[0]

    valid_checkpoints = {"preflight-passed", "discovery-confirmed", "implementation-complete"}
    if latest.checkpoint_cursor in valid_checkpoints:
        result.resume_from = latest.checkpoint_cursor
        result.resume_run_id = latest.run_id


def _parse_frontmatter(path: Path) -> dict | None:
    try:
        content = path.read_text()
    except OSError:
        return None

    match = re.match(r"^---\s*\n(.+?)\n---", content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


from dataclasses import dataclass
from pathlib import Path

from squad_cli.test_gate import StackFingerprint, TestInfraStatus, detect_test_infra


@dataclass
class TestInfraDecision:
    action: str
    proposal: dict | None = None


def check_test_infra(
    repo_root: Path,
    stack: StackFingerprint,
    bootstrapped: bool,
    debt_acknowledged: bool,
) -> TestInfraDecision:
    status = detect_test_infra(repo_root, stack)
    if status == TestInfraStatus.UNKNOWN:
        return TestInfraDecision(action="human_gate_unknown")
    if status == TestInfraStatus.PRESENT_AND_CONFIGURED:
        return TestInfraDecision(action="proceed")
    if not bootstrapped and not debt_acknowledged:
        return TestInfraDecision(
            action="human_gate",
            proposal={
                "stack": stack.language,
                "framework_recommended": stack.test_framework or "pytest",
                "structure": ["tests/unit/", "tests/integration/"],
                "ci_step_required": True,
            },
        )
    return TestInfraDecision(action="incremental_automatic")
