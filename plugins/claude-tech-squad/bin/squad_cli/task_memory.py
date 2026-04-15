from __future__ import annotations

from squad_cli.models import RunState

SHARED_MAX_LINES = 200
SHARED_MAX_BYTES = 16384
TEAMMATE_MAX_LINES = 100
TEAMMATE_MAX_BYTES = 8192

PRESERVE_MARKERS = {"blockers:", "key decisions:", "blocking:", "critical:"}


def save_memory(state: RunState, key: str, content: str, append: bool = False) -> None:
    if key == "shared":
        existing = state.task_memory.get("shared", {}).get("content", "")
        if append and existing:
            content = existing + "\n" + content
        content = _compact(content, SHARED_MAX_LINES, SHARED_MAX_BYTES)
        state.task_memory["shared"] = {
            "content": content,
            "tokens": _estimate_tokens(content),
        }
    else:
        teammates = state.task_memory.setdefault("teammates", {})
        existing = teammates.get(key, {}).get("content", "")
        if append and existing:
            content = existing + "\n" + content
        content = _compact(content, TEAMMATE_MAX_LINES, TEAMMATE_MAX_BYTES)
        teammates[key] = {
            "content": content,
            "tokens": _estimate_tokens(content),
        }


def get_memory(state: RunState, key: str | None = None) -> str:
    if key is None or key == "shared":
        return state.task_memory.get("shared", {}).get("content", "")

    teammates = state.task_memory.get("teammates", {})
    return teammates.get(key, {}).get("content", "")


def get_all_memory(state: RunState) -> dict:
    result = {}
    shared = state.task_memory.get("shared", {})
    if shared.get("content"):
        result["shared"] = shared["content"]

    teammates = state.task_memory.get("teammates", {})
    for k, v in teammates.items():
        if v.get("content"):
            result[k] = v["content"]

    return result


def _compact(content: str, max_lines: int, max_bytes: int) -> str:
    lines = content.splitlines()

    if len(lines) <= max_lines and len(content.encode()) <= max_bytes:
        return content

    preserved = []
    regular = []

    for line in lines:
        lower = line.lower().strip()
        is_preserved = any(marker in lower for marker in PRESERVE_MARKERS)
        if is_preserved or line.startswith("##") or line.startswith("**"):
            preserved.append(line)
        else:
            regular.append(line)

    seen = set()
    deduped = []
    for line in regular:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            deduped.append(line)
        elif not stripped:
            deduped.append(line)

    combined = preserved + ["", "---", ""] + deduped

    while len(combined) > max_lines and deduped:
        deduped.pop()
        combined = preserved + ["", "---", ""] + deduped

    result = "\n".join(combined)

    if len(result.encode()) > max_bytes:
        while len(result.encode()) > max_bytes and deduped:
            deduped.pop()
            combined = preserved + ["", "---", ""] + deduped
            result = "\n".join(combined)

    return result


def _estimate_tokens(content: str) -> int:
    return len(content) // 4
