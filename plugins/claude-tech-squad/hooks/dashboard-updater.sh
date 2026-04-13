#!/usr/bin/env bash
# dashboard-updater.sh — Mechanical dashboard updater (best-effort, never blocks)
#
# PostToolUse hook that updates ai-docs/.live-status.json automatically
# whenever an Agent tool is called (teammate spawned/completed).
#
# IMPORTANT: This hook must NEVER return a non-zero exit code.
# A non-zero exit from a PostToolUse hook blocks the tool call.
# All errors are silently swallowed — the dashboard is best-effort.

# Never exit non-zero no matter what
trap 'exit 0' ERR EXIT

mkdir -p ai-docs 2>/dev/null || true

INPUT=$(cat 2>/dev/null || echo "{}")

python3 -c "
import sys, json, os
from datetime import datetime, timezone

try:
    hook_data = json.loads(sys.argv[1])
    status_file = 'ai-docs/.live-status.json'

    tool_name = hook_data.get('tool_name', '')
    if tool_name != 'Agent':
        sys.exit(0)

    tool_input = hook_data.get('tool_input', {})
    tool_result = hook_data.get('tool_result', '')

    agent_name = tool_input.get('name', tool_input.get('description', 'unknown'))
    subagent_type = tool_input.get('subagent_type', '')

    # Load existing status
    status = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
        except:
            status = {}

    if 'teammates' not in status:
        status['teammates'] = []
    if 'events' not in status:
        status['events'] = []
    if not status.get('skill'):
        status['skill'] = 'squad'
    if not status.get('started_at'):
        status['started_at'] = datetime.now(timezone.utc).isoformat()

    now = datetime.now(timezone.utc)
    time_str = now.strftime('%H:%M:%S')

    # Find existing teammate
    existing = None
    for tm in status['teammates']:
        if tm.get('name') == agent_name:
            existing = tm
            break

    if tool_result and str(tool_result).strip():
        # Agent completed
        if existing:
            existing['status'] = 'completed'
            try:
                started = datetime.fromisoformat(existing.get('started_at', now.isoformat()).replace('Z', '+00:00'))
                existing['duration_ms'] = int((now - started).total_seconds() * 1000)
            except:
                existing['duration_ms'] = 0
            result_str = str(tool_result)
            existing['output_summary'] = (result_str[:120] + '...') if len(result_str) > 120 else result_str
        status['events'].append({'time': time_str, 'line': f'[Teammate Done] {agent_name} | completed'})
    else:
        # Agent being spawned
        if not existing:
            status['teammates'].append({
                'name': agent_name,
                'subagent_type': subagent_type,
                'status': 'running',
                'started_at': now.isoformat(),
                'duration_ms': None,
                'output_summary': None,
                'health_signals': None
            })
        else:
            existing['status'] = 'running'
            existing['started_at'] = now.isoformat()
        status['events'].append({'time': time_str, 'line': f'[Teammate Spawned] {agent_name} | {subagent_type}'})

    running = [t for t in status['teammates'] if t['status'] == 'running']
    completed = [t for t in status['teammates'] if t['status'] == 'completed']
    status['phase'] = f'{len(completed)} done, {len(running)} running'
    status['events'] = status['events'][-50:]

    tmp_file = status_file + '.tmp'
    with open(tmp_file, 'w') as f:
        json.dump(status, f, indent=2, default=str)
    os.rename(tmp_file, status_file)

except Exception:
    pass
" "$INPUT" 2>/dev/null || true

exit 0
