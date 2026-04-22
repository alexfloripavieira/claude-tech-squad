from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from squad_cli.stack_detect import detect_stack


@dataclass
class OnboardingPlan:
    stack: str
    label: str
    template: str
    base_template: str
    ai_llm_section: str
    ai_feature: bool
    specialists: list[str]
    recommended_first_command: str
    required_health_checks: list[str]
    detected_commands: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def load_onboarding_catalog(path: Path) -> dict:
    with path.open() as fh:
        catalog = json.load(fh)

    if catalog.get("schema_version") != "1.0":
        raise ValueError("Unsupported onboarding catalog schema_version")
    if "profiles" not in catalog or "generic" not in catalog["profiles"]:
        raise ValueError("Onboarding catalog must define profiles.generic")

    return catalog


def build_onboarding_plan(project_root: Path, catalog_path: Path) -> OnboardingPlan:
    catalog = load_onboarding_catalog(catalog_path)
    stack_result = detect_stack(project_root)
    profiles = catalog["profiles"]
    profile = profiles.get(stack_result.stack, profiles["generic"])

    detected_commands = {
        "test": stack_result.test_command,
        "lint": stack_result.lint_command,
        "build": stack_result.build_command,
    }

    return OnboardingPlan(
        stack=stack_result.stack,
        label=profile["label"],
        template=profile["template"],
        base_template=catalog["default_template"],
        ai_llm_section=catalog["ai_llm_section"],
        ai_feature=stack_result.ai_feature,
        specialists=profile["specialists"],
        recommended_first_command=profile["recommended_first_command"],
        required_health_checks=profile["required_health_checks"],
        detected_commands=detected_commands,
    )
