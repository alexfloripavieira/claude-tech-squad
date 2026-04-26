from pathlib import Path

from squad_cli.preflight import check_test_infra
from squad_cli.test_gate import StackFingerprint


def make_stack():
    return StackFingerprint(
        language="python",
        test_framework="pytest",
        test_dirs=["tests"],
    )


def test_returns_proceed_when_infra_present(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x(): ...\n")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    decision = check_test_infra(tmp_path, make_stack(), bootstrapped=False, debt_acknowledged=False)
    assert decision.action == "proceed"


def test_returns_human_gate_on_first_contact(tmp_path: Path):
    decision = check_test_infra(tmp_path, make_stack(), bootstrapped=False, debt_acknowledged=False)
    assert decision.action == "human_gate"
    assert decision.proposal is not None


def test_returns_incremental_when_already_acknowledged(tmp_path: Path):
    decision = check_test_infra(tmp_path, make_stack(), bootstrapped=False, debt_acknowledged=True)
    assert decision.action == "incremental_automatic"


def test_returns_unknown_stack_gate(tmp_path: Path):
    decision = check_test_infra(
        tmp_path,
        StackFingerprint(language="ruby"),
        bootstrapped=False,
        debt_acknowledged=False,
    )
    assert decision.action == "human_gate_unknown"
