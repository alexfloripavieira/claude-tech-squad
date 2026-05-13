import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "plugins/claude-tech-squad/bin"))

from squad_cli.run_lifecycle import _parse_team_mode


def test_parse_team_mode_teammate_single_line():
    output = "mode=teammate tmux=1 inside_tmux=1 flag=1 version=2.1.140"
    assert _parse_team_mode(output) == "teammate"


def test_parse_team_mode_inline_single_line():
    output = "mode=inline tmux=0 inside_tmux=0 flag=0 version=2.1.140"
    assert _parse_team_mode(output) == "inline"


def test_parse_team_mode_missing_mode_key_returns_empty():
    output = "tmux=1 inside_tmux=1"
    assert _parse_team_mode(output) == ""


def test_parse_team_mode_invalid_value_returns_empty():
    output = "mode=invalid_value tmux=1"
    assert _parse_team_mode(output) == ""


def test_parse_team_mode_empty_string_returns_empty():
    assert _parse_team_mode("") == ""
