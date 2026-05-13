#!/usr/bin/env python3
"""Render public skill surface documentation from plugins/claude-tech-squad/public-surface.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins" / "claude-tech-squad" / "public-surface.json"


def load_surface() -> dict:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def render_table() -> str:
    surface = load_surface()
    lines = [
        "| Tier | Skills | Use when |",
        "|---|---|---|",
    ]
    descriptions = {
        "Core setup": "Prepare a repo, route incoming work, estimate cost, or inspect run health.",
        "Core delivery": "Fix contained defects, deliver small features, plan, refine, build, or run the full pipeline.",
        "Core operations": "Handle production pressure, release work, incidents, and long-running session handoff.",
        "Advanced review and audit": "Run specialist reviews, audits, dependency checks, and structured remediation planning.",
        "Advanced AI, infra, and scale": "Work on AI quality, database or infrastructure risk, distributed changes, repo automation, and process improvement.",
    }
    for tier in surface["tiers"]:
        skills = ", ".join(tier["skills"])
        lines.append(f"| {tier['name']} | {skills} | {descriptions.get(tier['name'], '')} |")
    return "\n".join(lines) + "\n"


def render_daily_flow() -> str:
    surface = load_surface()
    lines = ["If you only remember a short path:", ""]
    for idx, item in enumerate(surface["daily_flow"], start=1):
        lines.append(f"{idx}. {item['when']}: {item['skill']}")
    return "\n".join(lines) + "\n"


def render_quick_reference() -> str:
    surface = load_surface()
    tiers = surface["tiers"]
    core_setup = tiers[0]["skills"]
    core_delivery = tiers[1]["skills"]
    core_operations = tiers[2]["skills"]
    advanced_review = tiers[3]["skills"]
    advanced_ai = tiers[4]["skills"]
    lines = [
        "# Core setup",
        *core_setup,
        "",
        "# Core delivery",
        *core_delivery,
        "",
        "# Core operations",
        *core_operations,
        "",
        "# Advanced review and audit",
        *advanced_review,
        "",
        "# Advanced AI, infrastructure, and scale",
        *advanced_ai,
        "",
    ]
    return "\n".join(lines)


def render_full_doc() -> str:
    surface = load_surface()
    daily_flow_lines = [
        "If you only remember a short path:",
        "",
    ]
    for idx, item in enumerate(surface["daily_flow"], start=1):
        daily_flow_lines.append(f"{idx}. {item['when']}: {item['skill']}")
    lines = [
        "# Public Skill Surface",
        "",
        "This document is generated from `plugins/claude-tech-squad/public-surface.json`.",
        "",
        "## Tier Map",
        "",
        render_table().rstrip(),
        "",
        "## Daily Flow",
        "",
        "\n".join(daily_flow_lines),
        "",
        "## Quick Reference",
        "",
        render_quick_reference().rstrip(),
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write(
            "usage: render-public-surface-docs.py <table|daily-flow|quick-reference|full-doc|--write>\n"
        )
        return 2
    mode = sys.argv[1]
    if mode == "table":
        sys.stdout.write(render_table())
    elif mode == "daily-flow":
        sys.stdout.write(render_daily_flow())
    elif mode == "quick-reference":
        sys.stdout.write(render_quick_reference())
    elif mode == "full-doc":
        sys.stdout.write(render_full_doc())
    elif mode == "--write":
        target = ROOT / "docs" / "PUBLIC-SURFACE.md"
        target.write_text(render_full_doc(), encoding="utf-8")
        sys.stdout.write(f"wrote {target.relative_to(ROOT)}\n")
    else:
        sys.stderr.write(f"unknown mode: {mode}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
