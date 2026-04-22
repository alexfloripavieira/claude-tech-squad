from __future__ import annotations

import html
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml


@dataclass
class SepRun:
    path: str
    run_id: str
    skill: str
    timestamp: str
    final_status: str
    checkpoints: list[str]
    fallbacks_invoked: list
    gates_blocked: list[str]
    findings_critical: int
    findings_high: int
    postmortem_recommended: bool
    parent_run_id: str
    summary: str


@dataclass
class SkillSummary:
    skill: str
    runs: int
    completed: int
    failed_or_aborted: int
    success_rate: float
    last_run: str
    blocked_gates: int
    fallbacks: int
    flags: list[str]


@dataclass
class DashboardReport:
    generated_at: str
    logs_analyzed: int
    skills_covered: int
    overall_success_rate: float
    skill_summaries: list[SkillSummary]
    pending_hotfixes: list[SepRun]
    recent_runs: list[SepRun]
    source_log_dir: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_dashboard_report(log_dir: Path, limit: int = 30) -> DashboardReport:
    runs = read_sep_runs(log_dir, limit)
    generated_at = datetime.now(timezone.utc).isoformat()

    by_skill: dict[str, list[SepRun]] = {}
    for run in runs:
        by_skill.setdefault(run.skill, []).append(run)

    summaries = [_summarize_skill(skill, skill_runs) for skill, skill_runs in sorted(by_skill.items())]
    completed_total = sum(1 for run in runs if run.final_status == "completed")
    overall_success_rate = _pct(completed_total, len(runs))

    hotfixes = [run for run in runs if run.skill == "hotfix" and run.postmortem_recommended]
    postmortem_parent_ids = {
        run.parent_run_id
        for run in runs
        if run.skill == "incident-postmortem" and run.parent_run_id
    }
    pending_hotfixes = [run for run in hotfixes if run.run_id not in postmortem_parent_ids]

    return DashboardReport(
        generated_at=generated_at,
        logs_analyzed=len(runs),
        skills_covered=len(by_skill),
        overall_success_rate=overall_success_rate,
        skill_summaries=summaries,
        pending_hotfixes=pending_hotfixes,
        recent_runs=sorted(runs, key=lambda run: run.timestamp, reverse=True)[:5],
        source_log_dir=str(log_dir),
    )


def read_sep_runs(log_dir: Path, limit: int = 30) -> list[SepRun]:
    if not log_dir.is_dir():
        return []

    paths = sorted(
        [path for path in log_dir.glob("*.md") if path.name != ".gitkeep"],
        key=lambda path: path.name,
        reverse=True,
    )[:limit]

    runs = []
    for path in paths:
        run = parse_sep_log(path)
        if run:
            runs.append(run)
    return runs


def parse_sep_log(path: Path) -> SepRun | None:
    content = _read_text(path)
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    data = _parse_frontmatter(match.group(1))
    body = content[match.end() :].strip()
    summary = _extract_summary(body)

    checkpoints = _as_string_list(data.get("checkpoints", []))
    gates_blocked = _as_string_list(data.get("gates_blocked", []))
    blocked_from_checkpoints = [
        item for item in checkpoints if "gate" in item.lower() or "blocked" in item.lower()
    ]

    return SepRun(
        path=str(path),
        run_id=str(data.get("run_id") or path.stem),
        skill=str(data.get("skill") or "unknown"),
        timestamp=str(data.get("timestamp") or ""),
        final_status=str(data.get("final_status") or data.get("status") or "unknown"),
        checkpoints=checkpoints,
        fallbacks_invoked=_as_list(data.get("fallbacks_invoked", [])),
        gates_blocked=gates_blocked or blocked_from_checkpoints,
        findings_critical=_as_int(data.get("findings_critical", 0)),
        findings_high=_as_int(data.get("findings_high", 0)),
        postmortem_recommended=_as_bool(data.get("postmortem_recommended", False)),
        parent_run_id=str(data.get("parent_run_id") or ""),
        summary=summary,
    )


def write_dashboard_outputs(
    report: DashboardReport,
    markdown_path: Path,
    html_path: Path | None = None,
    sep_log_dir: Path | None = None,
) -> dict[str, str]:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(report))

    outputs = {"markdown": str(markdown_path)}
    if html_path:
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_html(report))
        outputs["html"] = str(html_path)

    if sep_log_dir:
        sep_log_dir.mkdir(parents=True, exist_ok=True)
        sep_path = _write_dashboard_sep_log(report, sep_log_dir)
        outputs["sep_log"] = str(sep_path)

    return outputs


def render_markdown(report: DashboardReport) -> str:
    lines = [
        f"## Squad Pipeline Dashboard - {report.generated_at}",
        "",
        "### Run Health by Skill",
        "| Skill | Runs | Completed | Failed/Aborted | Success% | Last run | Flags |",
        "|---|---:|---:|---:|---:|---|---|",
    ]

    if report.skill_summaries:
        for summary in report.skill_summaries:
            flags = ", ".join(summary.flags) if summary.flags else ""
            lines.append(
                f"| /{summary.skill} | {summary.runs} | {summary.completed} | "
                f"{summary.failed_or_aborted} | {summary.success_rate:.0f}% | "
                f"{_date_only(summary.last_run)} | {flags} |"
            )
    else:
        lines.append("| n/a | 0 | 0 | 0 | 0% | n/a | No SEP logs found |")

    lines.extend(["", "### Hotfixes Awaiting Post-Mortem"])
    if report.pending_hotfixes:
        for run in report.pending_hotfixes:
            lines.append(f"- `{run.run_id}` ({_date_only(run.timestamp)}) - {run.summary or 'No summary'}")
    else:
        lines.append("None - all hotfixes have associated post-mortems.")

    lines.extend(
        [
            "",
            "### Recent Activity",
            "| Timestamp | Skill | Status | Notes |",
            "|---|---|---|---|",
        ]
    )
    if report.recent_runs:
        for run in report.recent_runs:
            note = run.summary or _risk_note(run)
            lines.append(f"| {run.timestamp or 'n/a'} | /{run.skill} | {run.final_status} | {note} |")
    else:
        lines.append("| n/a | n/a | n/a | No SEP logs found |")

    low_success = [s.skill for s in report.skill_summaries if s.success_rate < 70]
    lines.extend(
        [
            "",
            "### Summary",
            f"- Total runs analyzed: {report.logs_analyzed}",
            f"- Overall success rate: {report.overall_success_rate:.0f}%",
            f"- Skills with low success rate (<70%): {', '.join(low_success) if low_success else 'None'}",
            f"- Hotfixes awaiting post-mortem: {len(report.pending_hotfixes)}",
            "- Snapshot saved: ai-docs/dashboard-snapshot.md",
            "- HTML report saved: ai-docs/dashboard.html",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(report: DashboardReport) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>/{html.escape(summary.skill)}</td>"
        f"<td>{summary.runs}</td>"
        f"<td>{summary.completed}</td>"
        f"<td>{summary.failed_or_aborted}</td>"
        f"<td>{summary.success_rate:.0f}%</td>"
        f"<td>{html.escape(_date_only(summary.last_run))}</td>"
        f"<td>{html.escape(', '.join(summary.flags))}</td>"
        "</tr>"
        for summary in report.skill_summaries
    )
    if not rows:
        rows = "<tr><td colspan=\"7\">No SEP logs found.</td></tr>"

    recent = "\n".join(
        "<tr>"
        f"<td>{html.escape(run.timestamp or 'n/a')}</td>"
        f"<td>/{html.escape(run.skill)}</td>"
        f"<td>{html.escape(run.final_status)}</td>"
        f"<td>{html.escape(run.summary or _risk_note(run))}</td>"
        "</tr>"
        for run in report.recent_runs
    )
    if not recent:
        recent = "<tr><td colspan=\"4\">No recent activity.</td></tr>"

    pending = "".join(
        f"<li><code>{html.escape(run.run_id)}</code> ({html.escape(_date_only(run.timestamp))}) - "
        f"{html.escape(run.summary or 'No summary')}</li>"
        for run in report.pending_hotfixes
    )
    if not pending:
        pending = "<li>None - all hotfixes have associated post-mortems.</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Squad Pipeline Dashboard</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 32px; color: #1f2937; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .summary {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }}
    .metric {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 12px 14px; min-width: 150px; }}
    .metric strong {{ display: block; font-size: 24px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Squad Pipeline Dashboard</h1>
  <p>Generated at {html.escape(report.generated_at)} from <code>{html.escape(report.source_log_dir)}</code>.</p>
  <section class="summary">
    <div class="metric"><span>Runs analyzed</span><strong>{report.logs_analyzed}</strong></div>
    <div class="metric"><span>Skills covered</span><strong>{report.skills_covered}</strong></div>
    <div class="metric"><span>Success rate</span><strong>{report.overall_success_rate:.0f}%</strong></div>
    <div class="metric"><span>Pending post-mortems</span><strong>{len(report.pending_hotfixes)}</strong></div>
  </section>
  <h2>Run Health by Skill</h2>
  <table>
    <thead><tr><th>Skill</th><th>Runs</th><th>Completed</th><th>Failed/Aborted</th><th>Success</th><th>Last run</th><th>Flags</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <h2>Hotfixes Awaiting Post-Mortem</h2>
  <ul>{pending}</ul>
  <h2>Recent Activity</h2>
  <table>
    <thead><tr><th>Timestamp</th><th>Skill</th><th>Status</th><th>Notes</th></tr></thead>
    <tbody>{recent}</tbody>
  </table>
</body>
</html>
"""


def _summarize_skill(skill: str, runs: list[SepRun]) -> SkillSummary:
    completed = sum(1 for run in runs if run.final_status == "completed")
    failed_or_aborted = sum(1 for run in runs if run.final_status in {"failed", "aborted", "partial"})
    blocked_gates = sum(len(run.gates_blocked) for run in runs)
    fallbacks = sum(len(run.fallbacks_invoked) for run in runs)
    success_rate = _pct(completed, len(runs))
    last_run = max((run.timestamp for run in runs), default="")

    flags = []
    if success_rate < 70:
        flags.append("LOW")
    if blocked_gates > 2:
        flags.append("FREQUENT_GATES")
    if any(run.findings_critical or run.findings_high for run in runs):
        flags.append("RISK_FINDINGS")

    return SkillSummary(
        skill=skill,
        runs=len(runs),
        completed=completed,
        failed_or_aborted=failed_or_aborted,
        success_rate=success_rate,
        last_run=last_run,
        blocked_gates=blocked_gates,
        fallbacks=fallbacks,
        flags=flags,
    )


def _parse_frontmatter(text: str) -> dict:
    try:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict):
            return parsed
    except yaml.YAMLError:
        pass

    data = {}
    for line in text.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _write_dashboard_sep_log(report: DashboardReport, sep_log_dir: Path) -> Path:
    now = datetime.now(timezone.utc)
    run_id = uuid4().hex[:8]
    path = sep_log_dir / f"{now.strftime('%Y-%m-%dT%H-%M-%S')}-dashboard-{run_id}.md"
    content = "\n".join(
        [
            "---",
            f"run_id: {run_id}",
            "skill: dashboard",
            f"timestamp: {now.isoformat()}",
            "status: completed",
            "final_status: completed",
            "execution_mode: inline",
            "architecture_style: n/a",
            "checkpoints: [logs-read, aggregation-complete, snapshot-written, html-written]",
            "fallbacks_invoked: []",
            f"logs_analyzed: {report.logs_analyzed}",
            f"skills_covered: {report.skills_covered}",
            f"hotfixes_pending_postmortem: {len(report.pending_hotfixes)}",
            "tokens_input: 0",
            "tokens_output: 0",
            "estimated_cost_usd: 0",
            "total_duration_ms: 0",
            "---",
            "",
            "## Dashboard Summary",
            f"Analyzed {report.logs_analyzed} SEP logs. Overall success rate: {report.overall_success_rate:.0f}%. "
            f"{len(report.pending_hotfixes)} hotfixes awaiting post-mortem.",
            "",
        ]
    )
    path.write_text(content)
    return path


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in {"", "[]", "null", "None"}:
            return []
        return [stripped]
    return [value]


def _as_string_list(value) -> list[str]:
    return [str(item) for item in _as_list(value)]


def _as_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "1"}


def _pct(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return (part / whole) * 100


def _date_only(value: str) -> str:
    if not value:
        return "n/a"
    return value[:10]


def _risk_note(run: SepRun) -> str:
    notes = []
    if run.gates_blocked:
        notes.append(f"{len(run.gates_blocked)} blocked gate(s)")
    if run.fallbacks_invoked:
        notes.append(f"{len(run.fallbacks_invoked)} fallback(s)")
    if run.findings_critical or run.findings_high:
        notes.append(f"{run.findings_critical} critical / {run.findings_high} high findings")
    return ", ".join(notes) if notes else ""


def _extract_summary(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:160]
    return ""


def _read_text(path: Path) -> str:
    try:
        return path.read_text()
    except OSError:
        return ""
