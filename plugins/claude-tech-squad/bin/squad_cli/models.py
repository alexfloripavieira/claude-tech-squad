from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class TeammateState:
    name: str
    subagent_type: str = ""
    status: str = "pending"
    tokens_in: int = 0
    tokens_out: int = 0
    confidence: str = ""
    retries: int = 0
    fallback_used: bool = False
    duration_ms: int = 0
    findings_blocking: int = 0
    findings_warning: int = 0
    reliability_state: str = "primary"


@dataclass
class TokenBudget:
    max_tokens: int = 0
    used_in: int = 0
    used_out: int = 0

    @property
    def used_total(self) -> int:
        return self.used_in + self.used_out

    @property
    def percent_used(self) -> float:
        if self.max_tokens == 0:
            return 0.0
        return (self.used_total / self.max_tokens) * 100

    def estimate_cost_usd(self) -> float:
        return (self.used_in * 15 + self.used_out * 75) / 1_000_000


@dataclass
class RunState:
    run_id: str
    skill: str
    started_at: str = ""
    policy_version: str = ""
    stack: str = "generic"
    ai_feature: bool = False
    routing: dict[str, str] = field(default_factory=dict)
    checkpoint_cursor: str = ""
    completed_checkpoints: list[str] = field(default_factory=list)
    teammates: dict[str, TeammateState] = field(default_factory=dict)
    token_budget: TokenBudget = field(default_factory=TokenBudget)
    fallbacks: list[dict[str, str]] = field(default_factory=list)
    doom_loops: int = 0
    health_signals: list[str] = field(default_factory=list)
    task_memory: dict[str, Any] = field(default_factory=dict)
    gates_cleared: list[str] = field(default_factory=list)
    gates_blocked: list[str] = field(default_factory=list)
    escape_hatch_used: bool = False
    skipped_phases: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["teammates"] = {k: asdict(v) for k, v in self.teammates.items()}
        d["token_budget"] = asdict(self.token_budget)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> RunState:
        teammates = {}
        for k, v in data.pop("teammates", {}).items():
            teammates[k] = TeammateState(**v)
        budget_data = data.pop("token_budget", {})
        budget = TokenBudget(**budget_data)
        state = cls(**data)
        state.teammates = teammates
        state.token_budget = budget
        return state

    def save(self, state_dir: Path) -> Path:
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_dir / f"{self.run_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False))
        return path

    @classmethod
    def load(cls, path: Path) -> RunState:
        data = json.loads(path.read_text())
        return cls.from_dict(data)

    def record_teammate(self, name: str, **kwargs) -> TeammateState:
        if name not in self.teammates:
            self.teammates[name] = TeammateState(name=name)
        tm = self.teammates[name]
        for k, v in kwargs.items():
            if hasattr(tm, k):
                setattr(tm, k, v)
        self.token_budget.used_in += kwargs.get("tokens_in", 0)
        self.token_budget.used_out += kwargs.get("tokens_out", 0)
        return tm


@dataclass
class PreflightResult:
    execution_mode: str = "inline"
    stack: str = "generic"
    ai_feature: bool = False
    routing: dict[str, str] = field(default_factory=dict)
    architecture_style: str = "existing-repo-pattern"
    lint_profile: str = "none-detected"
    docs_lookup_mode: str = "repo-fallback"
    policy_version: str = ""
    resume_from: str | None = None
    resume_run_id: str | None = None
    token_budget_max: int = 0
    orphaned_discoveries: int = 0
    retro_counter: int = 0
    retro_threshold: int = 5
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class HealthCheckResult:
    teammate: str
    signals_triggered: list[str] = field(default_factory=list)
    context_enrichment: str = ""
    budget_percent: float = 0.0
    budget_warning: bool = False
    budget_halt: bool = False
    is_critical: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DoomLoopResult:
    is_doom_loop: bool = False
    pattern: str = ""
    evidence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
