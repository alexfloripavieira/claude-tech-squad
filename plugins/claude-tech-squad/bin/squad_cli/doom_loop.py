from __future__ import annotations

import difflib
import re

from squad_cli.models import DoomLoopResult


def check_doom_loop(
    prev_output: str,
    curr_output: str,
    prev_prev_output: str | None = None,
) -> DoomLoopResult:
    result = DoomLoopResult()

    if _check_same_error(prev_output, curr_output, result):
        return result

    if _check_oscillating_fix(prev_output, curr_output, result):
        return result

    if prev_prev_output is not None:
        if _check_growing_diff(prev_prev_output, prev_output, curr_output, result):
            return result

    return result


def _extract_error_signatures(text: str) -> set[str]:
    patterns = [
        r"(?:Error|Exception|FAIL|FAILED)[:]\s*(.+)",
        r"(?:assert|AssertionError)[:]\s*(.+)",
        r"(?:TypeError|ValueError|KeyError|AttributeError|ImportError)[:]\s*(.+)",
        r"E\s+(\w+Error:.+)",
    ]
    signatures = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            sig = match.group(1).strip()[:200]
            sig = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", sig)
            sig = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", sig)
            signatures.add(sig)
    return signatures


def _check_same_error(prev: str, curr: str, result: DoomLoopResult) -> bool:
    prev_errors = _extract_error_signatures(prev)
    curr_errors = _extract_error_signatures(curr)

    if prev_errors and curr_errors:
        overlap = prev_errors & curr_errors
        if overlap:
            result.is_doom_loop = True
            result.pattern = "same_error"
            result.evidence = f"Same error in consecutive retries: {list(overlap)[:3]}"
            return True
    return False


def _check_oscillating_fix(prev: str, curr: str, result: DoomLoopResult) -> bool:
    prev_lines = prev.splitlines()
    curr_lines = curr.splitlines()

    diff = list(difflib.unified_diff(prev_lines, curr_lines, lineterm=""))
    if len(diff) < 4:
        return False

    added_in_prev: set[str] = set()
    removed_in_prev: set[str] = set()
    added_in_curr: set[str] = set()
    removed_in_curr: set[str] = set()

    for line in diff:
        stripped = line[1:].strip()
        if not stripped:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added_in_curr.add(stripped)
        elif line.startswith("-") and not line.startswith("---"):
            removed_in_curr.add(stripped)

    restored = removed_in_curr & set(l.strip() for l in prev_lines if l.strip())
    reverted = added_in_curr & set(l.strip() for l in prev_lines if l.strip())

    oscillation_score = len(removed_in_curr & added_in_curr)
    if oscillation_score > 2:
        result.is_doom_loop = True
        result.pattern = "oscillating_fix"
        result.evidence = f"Agent is oscillating: {oscillation_score} lines both added and removed"
        return True

    return False


def _check_growing_diff(prev_prev: str, prev: str, curr: str, result: DoomLoopResult) -> bool:
    base_lines = prev_prev.splitlines()
    diff1 = list(difflib.unified_diff(base_lines, prev.splitlines(), lineterm=""))
    diff2 = list(difflib.unified_diff(base_lines, curr.splitlines(), lineterm=""))

    size1 = len([l for l in diff1 if l.startswith("+") or l.startswith("-")])
    size2 = len([l for l in diff2 if l.startswith("+") or l.startswith("-")])

    if size2 > size1 > 0:
        result.is_doom_loop = True
        result.pattern = "growing_diff"
        result.evidence = f"Diff grew from {size1} to {size2} changed lines across retries"
        return True

    return False
