#!/usr/bin/env python3
"""Check that docs/PUBLIC-SURFACE.md matches the generated public surface."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / "scripts" / "render-public-surface-docs.py"
TARGET = ROOT / "docs" / "PUBLIC-SURFACE.md"


def main() -> int:
    expected = subprocess.run(
        ["python3", str(RENDER), "full-doc"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    actual = TARGET.read_text(encoding="utf-8").strip()
    if actual != expected:
        sys.stderr.write(
            "docs/PUBLIC-SURFACE.md is out of sync with plugins/claude-tech-squad/public-surface.json\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
