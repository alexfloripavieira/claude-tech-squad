from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from squad_cli.preflight import run_preflight
from squad_cli.policy import RuntimePolicy


@dataclass
class TeammateSlot:
    name: str
    subagent_type: str
    mode: str = "sequential"
    gate: str = ""
    max_cycles: int = 0


@dataclass
class Phase:
    name: str
    teammates: list[TeammateSlot] = field(default_factory=list)

    @property
    def gate_count(self) -> int:
        return sum(1 for t in self.teammates if t.gate)


def _resolve_agent(template: str, routing: dict[str, str]) -> str:
    if template.startswith("{{") and template.endswith("}}"):
        key = template[2:-2]
        return routing.get(key, template)
    return template


SKILL_PLANS: dict[str, list[dict]] = {
    "squad": [
        {
            "name": "discovery",
            "teammates": [
                {"name": "pm", "agent": "{{pm_agent}}", "gate": "Gate 1: Product Definition"},
                {"name": "business-analyst", "agent": "business-analyst"},
                {"name": "po", "agent": "po", "gate": "Gate 2: Scope Validation"},
                {"name": "planner", "agent": "planner", "gate": "Gate 3: Technical Tradeoffs"},
                {"name": "architect", "agent": "architect"},
                {"name": "techlead", "agent": "{{techlead_agent}}", "gate": "Gate 4: Architecture Direction"},
                {"name": "specialist-bench", "agent": "varies", "mode": "parallel"},
                {"name": "quality-baseline", "agent": "varies", "mode": "parallel"},
                {"name": "design-principles", "agent": "design-principles-specialist"},
                {"name": "test-planner", "agent": "test-planner"},
                {"name": "tdd-specialist", "agent": "tdd-specialist", "gate": "Gate 5: Blueprint Confirmation"},
            ],
        },
        {
            "name": "implementation",
            "teammates": [
                {"name": "tdd-impl", "agent": "tdd-specialist"},
                {"name": "impl-batch", "agent": "varies", "mode": "parallel"},
                {"name": "reviewer", "agent": "{{reviewer_agent}}", "max_cycles": 3},
                {"name": "qa", "agent": "{{qa_agent}}", "max_cycles": 2},
                {"name": "techlead-audit", "agent": "{{techlead_agent}}", "gate": "Conformance Gate"},
                {"name": "quality-bench", "agent": "varies", "mode": "parallel"},
                {"name": "docs-writer", "agent": "docs-writer"},
                {"name": "jira-confluence", "agent": "jira-confluence-specialist"},
                {"name": "pm-uat", "agent": "{{pm_agent}}", "gate": "Gate 6: UAT"},
            ],
        },
        {
            "name": "release",
            "teammates": [
                {"name": "release", "agent": "release"},
                {"name": "sre", "agent": "sre"},
            ],
        },
    ],
    "implement": [
        {
            "name": "implementation",
            "teammates": [
                {"name": "tdd-specialist", "agent": "tdd-specialist"},
                {"name": "impl-batch", "agent": "varies", "mode": "parallel"},
                {"name": "reviewer", "agent": "{{reviewer_agent}}", "max_cycles": 3},
                {"name": "qa", "agent": "{{qa_agent}}", "max_cycles": 2},
                {"name": "techlead-audit", "agent": "{{techlead_agent}}", "gate": "Conformance Gate"},
                {"name": "quality-bench", "agent": "varies", "mode": "parallel"},
                {"name": "docs-writer", "agent": "docs-writer"},
                {"name": "jira-confluence", "agent": "jira-confluence-specialist"},
                {"name": "pm-uat", "agent": "{{pm_agent}}", "gate": "UAT"},
            ],
        },
    ],
    "discovery": [
        {
            "name": "discovery",
            "teammates": [
                {"name": "pm", "agent": "{{pm_agent}}", "gate": "Gate 1: Product Definition"},
                {"name": "business-analyst", "agent": "business-analyst"},
                {"name": "po", "agent": "po", "gate": "Gate 2: Scope Validation"},
                {"name": "planner", "agent": "planner", "gate": "Gate 3: Technical Tradeoffs"},
                {"name": "architect", "agent": "architect"},
                {"name": "techlead", "agent": "{{techlead_agent}}", "gate": "Gate 4: Architecture Direction"},
                {"name": "specialist-bench", "agent": "varies", "mode": "parallel"},
                {"name": "quality-baseline", "agent": "varies", "mode": "parallel"},
                {"name": "design-principles", "agent": "design-principles-specialist"},
                {"name": "test-planner", "agent": "test-planner"},
                {"name": "tdd-specialist", "agent": "tdd-specialist", "gate": "Gate 5: Blueprint Confirmation"},
            ],
        },
    ],
    "hotfix": [
        {
            "name": "hotfix",
            "teammates": [
                {"name": "techlead", "agent": "techlead", "gate": "Root Cause Confirmation"},
                {"name": "hotfix-impl", "agent": "{{backend_agent}}"},
                {"name": "reviewer", "agent": "{{reviewer_agent}}"},
                {"name": "security-reviewer", "agent": "security-reviewer"},
            ],
        },
    ],
    "bug-fix": [
        {
            "name": "bug-fix",
            "teammates": [
                {"name": "techlead", "agent": "techlead"},
                {"name": "tdd-specialist", "agent": "tdd-specialist"},
                {"name": "impl", "agent": "{{backend_agent}}"},
                {"name": "qa", "agent": "{{qa_agent}}"},
                {"name": "code-quality", "agent": "code-quality"},
                {"name": "reviewer", "agent": "{{reviewer_agent}}"},
            ],
        },
    ],
}

PARALLEL_BATCH_DETAILS = {
    "specialist-bench": ["backend-arch", "frontend-arch", "api-designer", "data-arch", "dba", "devops"],
    "quality-baseline": [
        "security-reviewer",
        "privacy-reviewer",
        "compliance-reviewer",
        "performance-engineer",
        "observability-engineer",
    ],
    "quality-bench": ["security-rev", "privacy-rev", "perf-eng", "access-rev", "integ-qa", "code-quality"],
    "impl-batch": ["backend-dev", "frontend-dev"],
}


def dry_run(
    skill: str,
    policy: RuntimePolicy,
    project_root: Path,
) -> str:
    preflight = run_preflight(skill, policy, project_root)
    routing = preflight.routing
    plan_templates = SKILL_PLANS.get(skill)

    if not plan_templates:
        return f"No plan available for skill: {skill}"

    lines = [
        f"Dry Run: /{skill}",
        f"Stack: {preflight.stack} | ai_feature: {preflight.ai_feature}",
        f"Budget: {preflight.token_budget_max:,} tokens (~${preflight.token_budget_max * 45 / 1_000_000:.0f} max)",
        "",
    ]

    if preflight.resume_from:
        lines.append(f"Resume: from checkpoint '{preflight.resume_from}' (run: {preflight.resume_run_id})")
    else:
        lines.append("Resume: no prior run found")

    if preflight.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in preflight.warnings:
            lines.append(f"  - {w}")

    total_teammates = 0
    total_gates = 0

    for phase_tmpl in plan_templates:
        phase_name = phase_tmpl["name"]
        teammates_tmpl = phase_tmpl["teammates"]
        lines.append("")
        lines.append(f"Phase: {phase_name} ({len(teammates_tmpl)} steps)")

        for i, tm_tmpl in enumerate(teammates_tmpl, 1):
            name = tm_tmpl["name"]
            agent_raw = tm_tmpl["agent"]
            mode = tm_tmpl.get("mode", "sequential")
            gate = tm_tmpl.get("gate", "")
            max_cycles = tm_tmpl.get("max_cycles", 0)

            agent = _resolve_agent(agent_raw, routing) if agent_raw != "varies" else "varies"

            mode_tag = f"[{mode}]" if mode == "parallel" else "[sequential]"
            agent_display = f"({agent})" if agent != "varies" else ""

            if name in PARALLEL_BATCH_DETAILS:
                members = PARALLEL_BATCH_DETAILS[name]
                agent_display = f"[{', '.join(members)}]"
                total_teammates += len(members)
            else:
                total_teammates += 1

            cycle_note = f" -- max {max_cycles} cycles" if max_cycles else ""
            gate_note = f" -> {gate}" if gate else ""
            if gate:
                total_gates += 1

            lines.append(f"  {i:2d}. {mode_tag:14s} {name} {agent_display}{cycle_note}{gate_note}")

    lines.extend(
        [
            "",
            f"Estimated teammates: ~{total_teammates}",
            f"Estimated gates: {total_gates}",
        ]
    )

    return "\n".join(lines)
