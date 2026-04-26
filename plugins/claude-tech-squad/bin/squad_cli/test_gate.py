from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class TestInfraStatus(str, Enum):
    PRESENT_AND_CONFIGURED = "present"
    PARTIAL = "partial"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class GateVerdict(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    BLOCKING = "blocking"


@dataclass
class StackFingerprint:
    language: str
    framework: str | None = None
    test_framework: str | None = None
    test_dirs: list[str] = field(default_factory=list)


@dataclass
class UnpairedFile:
    path: str
    reason: str = "no_paired_test_found"


@dataclass
class GatePolicy:
    enforce_level: str = "blocking"
    coverage_warning_threshold: float = 0.02


NON_CODE_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".lock"}


def _is_test_file(path: str, language: str) -> bool:
    name = Path(path).name
    if language == "python":
        return name.startswith("test_") or name.endswith("_test.py") or "/tests/" in path or path.startswith("tests/")
    if language in {"typescript", "javascript"}:
        return ".test." in name or ".spec." in name or "__tests__" in path
    if language == "go":
        return name.endswith("_test.go")
    return False


def _is_non_code(path: str) -> bool:
    return Path(path).suffix in NON_CODE_EXTENSIONS


def _candidate_test_paths(prod_path: str, language: str) -> list[str]:
    p = Path(prod_path)
    stem = p.stem
    parent = p.parent
    if language == "python":
        return [
            f"tests/test_{stem}.py",
            f"tests/{parent.name}/test_{stem}.py",
            f"{parent}/test_{stem}.py",
            f"{parent}/{stem}_test.py",
        ]
    if language in {"typescript", "javascript"}:
        ext = p.suffix
        return [
            f"{parent}/{stem}.test{ext}",
            f"{parent}/{stem}.spec{ext}",
            f"{parent}/__tests__/{stem}.test{ext}",
        ]
    if language == "go":
        return [f"{parent}/{stem}_test.go"]
    return []


def check_paired_tests(
    diff_files: Iterable[str],
    stack: StackFingerprint,
    repo_root: Path,
) -> list[UnpairedFile]:
    unpaired: list[UnpairedFile] = []
    for f in diff_files:
        if _is_non_code(f) or _is_test_file(f, stack.language):
            continue
        candidates = _candidate_test_paths(f, stack.language)
        if not any((repo_root / c).exists() for c in candidates):
            unpaired.append(UnpairedFile(path=f))
    return unpaired


def evaluate_gate(
    unpaired: list[UnpairedFile],
    coverage_delta: float,
    policy: GatePolicy,
) -> GateVerdict:
    if unpaired:
        if policy.enforce_level == "blocking":
            return GateVerdict.BLOCKING
        return GateVerdict.WARNING
    if coverage_delta < 0 and abs(coverage_delta) > policy.coverage_warning_threshold:
        return GateVerdict.WARNING
    return GateVerdict.PASS
