from pathlib import Path

import pytest

from squad_cli.test_gate import (
    GatePolicy,
    GateVerdict,
    StackFingerprint,
    UnpairedFile,
    check_paired_tests,
    evaluate_gate,
)


def make_stack(language="python"):
    return StackFingerprint(
        language=language,
        framework=None,
        test_framework="pytest",
        test_dirs=["tests"],
    )


def test_python_unpaired_when_no_test_file(tmp_path: Path):
    (tmp_path / "src" / "foo").mkdir(parents=True)
    (tmp_path / "src" / "foo" / "bar.py").write_text("def x(): ...\n")
    diff = ["src/foo/bar.py"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert len(result) == 1
    assert result[0].path == "src/foo/bar.py"


def test_python_paired_when_test_exists(tmp_path: Path):
    (tmp_path / "src" / "foo").mkdir(parents=True)
    (tmp_path / "src" / "foo" / "bar.py").write_text("def x(): ...\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_bar.py").write_text("def test_x(): ...\n")
    diff = ["src/foo/bar.py"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert result == []


def test_non_code_extension_ignored(tmp_path: Path):
    diff = ["README.md", "config.yaml"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert result == []


def test_test_file_itself_ignored(tmp_path: Path):
    diff = ["tests/test_bar.py"]
    result = check_paired_tests(diff, make_stack(), repo_root=tmp_path)
    assert result == []


def make_policy(level="blocking", coverage_threshold=0.02):
    return GatePolicy(enforce_level=level, coverage_warning_threshold=coverage_threshold)


def test_pass_when_no_unpaired_no_drop():
    verdict = evaluate_gate(unpaired=[], coverage_delta=0.0, policy=make_policy())
    assert verdict == GateVerdict.PASS


def test_blocking_when_unpaired_and_blocking_level():
    verdict = evaluate_gate(
        unpaired=[UnpairedFile(path="src/x.py")],
        coverage_delta=0.0,
        policy=make_policy("blocking"),
    )
    assert verdict == GateVerdict.BLOCKING


def test_warning_when_unpaired_in_shadow_mode():
    verdict = evaluate_gate(
        unpaired=[UnpairedFile(path="src/x.py")],
        coverage_delta=0.0,
        policy=make_policy("warning"),
    )
    assert verdict == GateVerdict.WARNING


def test_warning_on_coverage_drop_above_threshold():
    verdict = evaluate_gate(unpaired=[], coverage_delta=-0.05, policy=make_policy())
    assert verdict == GateVerdict.WARNING


def test_pass_on_small_coverage_drop():
    verdict = evaluate_gate(unpaired=[], coverage_delta=-0.01, policy=make_policy())
    assert verdict == GateVerdict.PASS
