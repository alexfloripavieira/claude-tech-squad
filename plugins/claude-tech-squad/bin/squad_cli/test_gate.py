from __future__ import annotations

import re
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


def _glob_to_regex(pattern: str) -> re.Pattern:
    parts: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                parts.append(".*")
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    i += 1
            else:
                parts.append("[^/]*")
                i += 1
        elif c == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(parts) + "$")


def _matches_any_glob(path: str, patterns: Iterable[str]) -> bool:
    basename = Path(path).name
    for pat in patterns:
        regex = _glob_to_regex(pat)
        if regex.match(path):
            return True
        if "/" not in pat and regex.match(basename):
            return True
    return False


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
    auto_generated_paths: Iterable[str] | None = None,
) -> list[UnpairedFile]:
    auto_globs = list(auto_generated_paths or [])
    unpaired: list[UnpairedFile] = []
    for f in diff_files:
        if _is_non_code(f) or _is_test_file(f, stack.language):
            continue
        if auto_globs and _matches_any_glob(f, auto_globs):
            continue
        if stack.language == "python" and Path(f).name == "__init__.py":
            full = repo_root / f
            if not full.exists() or full.read_text().strip() == "":
                continue
        candidates = _candidate_test_paths(f, stack.language)
        if not any((repo_root / c).exists() for c in candidates):
            unpaired.append(UnpairedFile(path=f))
    return unpaired


def detect_test_infra(repo_root: Path, stack: StackFingerprint) -> TestInfraStatus:
    if stack.language == "python":
        has_dir = (repo_root / "tests").is_dir() or any(
            (repo_root / d).is_dir() for d in stack.test_dirs
        )
        has_runner = any(
            (repo_root / cfg).exists()
            for cfg in ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini")
        )
        if has_dir and has_runner:
            test_files = list((repo_root / "tests").rglob("test_*.py")) if has_dir else []
            return (
                TestInfraStatus.PRESENT_AND_CONFIGURED
                if test_files
                else TestInfraStatus.PARTIAL
            )
        if has_dir or has_runner:
            return TestInfraStatus.PARTIAL
        return TestInfraStatus.ABSENT
    if stack.language in {"typescript", "javascript"}:
        pkg = repo_root / "package.json"
        if pkg.exists():
            content = pkg.read_text()
            if "jest" in content or "vitest" in content or "mocha" in content:
                return TestInfraStatus.PRESENT_AND_CONFIGURED
        return TestInfraStatus.ABSENT
    return TestInfraStatus.UNKNOWN


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
