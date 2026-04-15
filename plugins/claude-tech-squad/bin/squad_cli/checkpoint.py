from __future__ import annotations

from pathlib import Path

from squad_cli.models import RunState


DEFAULT_STATE_DIR = ".squad-state"


def save_checkpoint(state: RunState, cursor: str, state_dir: Path) -> Path:
    state.checkpoint_cursor = cursor
    if cursor not in state.completed_checkpoints:
        state.completed_checkpoints.append(cursor)
    return state.save(state_dir)


def load_checkpoint(run_id: str, state_dir: Path) -> RunState | None:
    path = state_dir / f"{run_id}.json"
    if not path.exists():
        return None
    return RunState.load(path)


def find_resumable(skill: str, state_dir: Path) -> RunState | None:
    if not state_dir.exists():
        return None

    candidates = []
    for path in state_dir.glob("*.json"):
        try:
            state = RunState.load(path)
            if state.skill == skill and state.checkpoint_cursor:
                candidates.append(state)
        except Exception:
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda s: s.started_at, reverse=True)
    return candidates[0]


def list_runs(state_dir: Path) -> list[dict]:
    if not state_dir.exists():
        return []

    runs = []
    for path in state_dir.glob("*.json"):
        try:
            state = RunState.load(path)
            runs.append(
                {
                    "run_id": state.run_id,
                    "skill": state.skill,
                    "started_at": state.started_at,
                    "checkpoint_cursor": state.checkpoint_cursor,
                    "teammates_count": len(state.teammates),
                }
            )
        except Exception:
            continue

    runs.sort(key=lambda r: r["started_at"], reverse=True)
    return runs
