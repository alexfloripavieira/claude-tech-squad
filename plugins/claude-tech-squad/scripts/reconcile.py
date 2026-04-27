#!/usr/bin/env python3
"""
Agent profile reconciler for claude-tech-squad.

Reads .claude-tech-squad.yml from the user's project root, computes the set of
enabled agents (profile + overrides), and physically moves agent files between
agents/ (active) and agents/.disabled/ (inert) inside the plugin directory.

Idempotent: safe to run on every SessionStart hook.

Exit codes:
    0  reconciliation done (or no config — backward-compat no-op)
    0  config file missing (treated as "full profile" — all agents active)
    1  malformed config or profile not found

Env vars:
    CLAUDE_PLUGIN_ROOT   plugin root (auto-set by Claude Code)
    CLAUDE_PROJECT_DIR   user project root (auto-set by Claude Code)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def find_plugin_root() -> Path:
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


def find_project_root() -> Path | None:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def parse_yaml_subset(text: str) -> dict:
    """Parse a constrained YAML subset (scalars, nested dicts, string lists).

    Supported patterns:
        key: value
        key:
          nested: value
          nested_list:
            - item
            - item
          - item   # list directly under key
    """
    root: dict = {}
    stack: list = [(-1, root, None)]

    def unwind(indent: int) -> None:
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

    def parent_dict_for(indent: int):
        unwind(indent)
        level, container, key = stack[-1]
        if key is not None and isinstance(container, dict):
            child = container.get(key)
            if isinstance(child, dict):
                return child, level
        if isinstance(container, dict):
            return container, level
        return root, -1

    def strip_quotes(value: str) -> str:
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]
        return value

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.lstrip()
        indent = len(raw) - len(stripped)

        if stripped.startswith("- "):
            value = strip_quotes(stripped[2:].strip())
            unwind(indent)
            top_level, top_container, top_key = stack[-1]
            if isinstance(top_container, dict) and top_key is not None:
                existing = top_container.get(top_key)
                if not isinstance(existing, list):
                    existing = []
                    top_container[top_key] = existing
                existing.append(value)
            elif isinstance(top_container, list):
                top_container.append(value)
            continue

        if ":" in stripped:
            key, _, raw_value = stripped.partition(":")
            key = key.strip()
            raw_value = raw_value.strip()
            container, _ = parent_dict_for(indent)

            if raw_value == "":
                container[key] = {}
                stack.append((indent, container, key))
            elif raw_value == "[]":
                container[key] = []
                stack.append((indent, container, key))
            elif raw_value == "{}":
                container[key] = {}
                stack.append((indent, container, key))
            else:
                container[key] = strip_quotes(raw_value)

    _normalize_empty_dicts_to_lists(root)
    return root


def _normalize_empty_dicts_to_lists(obj) -> None:
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            _normalize_empty_dicts_to_lists(v)


def load_yaml(path: Path) -> dict:
    return parse_yaml_subset(path.read_text(encoding="utf-8"))


def list_all_agents(agents_dir: Path) -> set[str]:
    active = {p.stem for p in agents_dir.glob("*.md")}
    disabled_dir = agents_dir / ".disabled"
    if disabled_dir.exists():
        active |= {p.stem for p in disabled_dir.glob("*.md")}
    return active


def resolve_enabled_set(
    config: dict, profiles_dir: Path, all_agents: set[str]
) -> tuple[set[str], str]:
    profile_name = config.get("profile", "full")
    profile_path = profiles_dir / f"{profile_name}.yml"
    if not profile_path.exists():
        raise SystemExit(
            f"[reconcile] profile '{profile_name}' not found in {profiles_dir}"
        )

    profile = load_yaml(profile_path)
    profile_agents = profile.get("agents", [])

    if profile_agents == "ALL" or profile_agents == ["ALL"]:
        enabled = set(all_agents)
    elif isinstance(profile_agents, list):
        enabled = set(profile_agents)
    else:
        raise SystemExit(
            f"[reconcile] profile '{profile_name}' has invalid 'agents' field"
        )

    overrides = config.get("overrides") or {}
    enable_extra = overrides.get("enable") or []
    disable_extra = overrides.get("disable") or []
    enabled |= set(enable_extra)
    enabled -= set(disable_extra)

    return enabled, profile_name


def find_user_config(project_root: Path | None) -> Path | None:
    if project_root is None:
        return None
    for candidate in (
        project_root / ".claude-tech-squad.yml",
        project_root / ".claude-tech-squad.yaml",
    ):
        if candidate.exists():
            return candidate
    return None


def reconcile(
    plugin_root: Path, project_root: Path | None, verbose: bool = False
) -> int:
    agents_dir = plugin_root / "agents"
    disabled_dir = agents_dir / ".disabled"
    profiles_dir = plugin_root / "profiles"

    if not agents_dir.is_dir():
        print(f"[reconcile] agents dir missing: {agents_dir}", file=sys.stderr)
        return 1
    if not profiles_dir.is_dir():
        if verbose:
            print("[reconcile] profiles dir missing — skipping (no-op)")
        return 0

    config_path = find_user_config(project_root)
    if config_path is None:
        if verbose:
            print(
                "[reconcile] no .claude-tech-squad.yml found — keeping all agents active"
            )
        promote_all_agents(agents_dir, disabled_dir, verbose=verbose)
        return 0

    config = load_yaml(config_path)
    all_agents = list_all_agents(agents_dir)
    enabled, profile_name = resolve_enabled_set(config, profiles_dir, all_agents)

    disabled_dir.mkdir(exist_ok=True)
    moved_to_disabled = 0
    moved_to_active = 0

    for path in agents_dir.glob("*.md"):
        if path.stem not in enabled:
            target = disabled_dir / path.name
            path.replace(target)
            moved_to_disabled += 1

    for path in disabled_dir.glob("*.md"):
        if path.stem in enabled:
            target = agents_dir / path.name
            path.replace(target)
            moved_to_active += 1

    active_count = len(list(agents_dir.glob("*.md")))
    disabled_count = len(list(disabled_dir.glob("*.md")))

    write_state(plugin_root, profile_name, active_count, disabled_count)

    if verbose:
        print(
            f"[reconcile] profile={profile_name} "
            f"active={active_count} disabled={disabled_count} "
            f"moved_disabled={moved_to_disabled} moved_active={moved_to_active}"
        )
    return 0


def promote_all_agents(agents_dir: Path, disabled_dir: Path, verbose: bool) -> None:
    if not disabled_dir.exists():
        return
    moved = 0
    for path in disabled_dir.glob("*.md"):
        path.replace(agents_dir / path.name)
        moved += 1
    if verbose and moved:
        print(f"[reconcile] restored {moved} agents to active (full mode)")


def write_state(plugin_root: Path, profile: str, active: int, disabled: int) -> None:
    state_dir = plugin_root / ".state"
    state_dir.mkdir(exist_ok=True)
    state_file = state_dir / "reconcile.json"
    import json
    import time

    payload = {
        "profile": profile,
        "active_agents": active,
        "disabled_agents": disabled,
        "reconciled_at": int(time.time()),
    }
    state_file.write_text(json.dumps(payload, indent=2))


def main(argv: list[str]) -> int:
    verbose = "-v" in argv or "--verbose" in argv
    plugin_root = find_plugin_root()
    project_root = find_project_root()
    return reconcile(plugin_root, project_root, verbose=verbose)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
