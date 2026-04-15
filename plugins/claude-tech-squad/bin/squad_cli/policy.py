from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class RuntimePolicy:
    def __init__(self, data: dict[str, Any]):
        self._data = data

    @classmethod
    def load(cls, path: Path) -> RuntimePolicy:
        text = path.read_text()
        data = yaml.safe_load(text) or {}
        return cls(data)

    @property
    def version(self) -> str:
        return str(self._data.get("version", "unknown"))

    def token_budget(self, skill: str) -> int:
        budgets = self._data.get("cost_guardrails", {}).get("token_budget", {})
        key = f"{skill}_max_tokens"
        return int(budgets.get(key, budgets.get("default_max_tokens", 1_500_000)))

    def retry_budget(self, key: str) -> int:
        budgets = self._data.get("retry_budgets", {})
        return int(budgets.get(key, 2))

    def fallback_for(self, phase: str, agent: str) -> list[str]:
        matrix = self._data.get("fallback_matrix", {})
        phase_matrix = matrix.get(phase, {})
        fallbacks = phase_matrix.get(agent, [])
        return [f.split(":")[-1] if ":" in f else f for f in fallbacks]

    def circuit_breaker_warn_percent(self) -> int:
        return int(self._data.get("cost_guardrails", {}).get("circuit_breaker", {}).get("warn_at_percent", 75))

    def circuit_breaker_halt_percent(self) -> int:
        return int(self._data.get("cost_guardrails", {}).get("circuit_breaker", {}).get("halt_at_percent", 100))

    def doom_loop_enabled(self) -> bool:
        return bool(self._data.get("doom_loop_detection", {}).get("enabled", True))

    def health_check_enabled(self) -> bool:
        return bool(self._data.get("inline_health_check", {}).get("enabled", True))

    def orphan_detection_enabled(self) -> bool:
        return bool(
            self._data.get("entropy_management", {}).get("orphan_detection", {}).get("check_at_preflight", True)
        )

    def orphan_stale_days(self) -> int:
        return int(self._data.get("entropy_management", {}).get("orphan_detection", {}).get("stale_threshold_days", 7))

    def retro_trigger_after_runs(self) -> int:
        return int(
            self._data.get("entropy_management", {})
            .get("factory_retrospective_auto_trigger", {})
            .get("trigger_after_runs", 5)
        )

    def retro_counter_file(self) -> str:
        return str(
            self._data.get("entropy_management", {})
            .get("factory_retrospective_auto_trigger", {})
            .get("counter_file", "ai-docs/.squad-log/.retro-counter")
        )

    def checkpoints_for(self, skill: str) -> list[str]:
        return list(self._data.get("checkpoint_resume", {}).get(skill, {}).get("checkpoints", []))

    def severity_blocking(self) -> list[str]:
        return list(self._data.get("severity_policy", {}).get("blocking", []))
