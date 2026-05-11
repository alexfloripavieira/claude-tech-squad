#!/usr/bin/env python3
"""validate-sep-log.py — validate a SEP log YAML frontmatter against schema.

Exit 0: valid. Exit 5: schema violation (prints [SEP Schema Violation] to stderr).
Exit 2: file unreadable / parse error.
"""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED = {
    "schema_version": (int,),
    "run_id": (str,),
    "skill": (str,),
    "status": (str,),
    "tokens_input": (int, type(None)),
    "tokens_output": (int, type(None)),
    "estimated_cost_usd": (int, float, type(None)),
    "total_duration_ms": (int, type(None)),
    "worktrees": (list,),
    "language_policy_applied": (str,),
}


def violation(msg: str) -> None:
    sys.stderr.write(f"[SEP Schema Violation] {msg}\n")


def extract_frontmatter(text: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    out: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return "\n".join(out)
        out.append(line)
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: validate-sep-log.py <path>\n")
        return 2
    path = Path(argv[1])
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"cannot read {path}: {e}\n")
        return 2

    fm = extract_frontmatter(text)
    if fm is None:
        violation(f"missing YAML frontmatter in {path}")
        return 5

    try:
        import yaml  # type: ignore
    except ImportError:
        sys.stderr.write("PyYAML not installed; skipping schema validation\n")
        return 0

    try:
        data = yaml.safe_load(fm)
    except yaml.YAMLError as e:
        violation(f"invalid YAML frontmatter: {e}")
        return 5

    if not isinstance(data, dict):
        violation("frontmatter is not a mapping")
        return 5

    errors: list[str] = []
    for key, types in REQUIRED.items():
        if key not in data:
            errors.append(f"missing required field: {key}")
            continue
        if not isinstance(data[key], types):
            type_names = "|".join(t.__name__ if t is not type(None) else "null" for t in types)
            errors.append(
                f"field {key} has wrong type: expected {type_names}, got {type(data[key]).__name__}"
            )

    if errors:
        for err in errors:
            violation(err)
        return 5

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
