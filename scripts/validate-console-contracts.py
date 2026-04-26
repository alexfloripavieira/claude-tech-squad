#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONSOLE_DIR = ROOT / "ai-docs/claude-tech-squad-console"
SCHEMA_DIR = CONSOLE_DIR / "schemas"
FIXTURE_DIR = CONSOLE_DIR / "fixtures/tickets"
PLUGIN_BIN = ROOT / "plugins/claude-tech-squad/bin"

sys.path.insert(0, str(PLUGIN_BIN))

from squad_cli.dashboard import build_dashboard_report, parse_sep_log  # noqa: E402
from squad_cli.ticket import build_ticket_plan, load_ticket_contexts  # noqa: E402


class SchemaError(AssertionError):
    pass


def main() -> int:
    schemas = {path.name: json.loads(path.read_text()) for path in SCHEMA_DIR.glob("*.schema.json")}

    required_schemas = {
        "ticket-context.schema.json",
        "ticket-plan.schema.json",
        "sep-run.schema.json",
        "dashboard-report.schema.json",
        "run-event.schema.json",
    }
    missing = sorted(required_schemas - set(schemas))
    if missing:
        raise SchemaError(f"Missing schema files: {', '.join(missing)}")

    fixture_paths = [
        FIXTURE_DIR / "github-issue.json",
        FIXTURE_DIR / "jira-issue.json",
        FIXTURE_DIR / "linear-issue.json",
        FIXTURE_DIR / "pasted-ticket.json",
        FIXTURE_DIR / "batch.json",
    ]
    for path in fixture_paths:
        if not path.is_file():
            raise SchemaError(f"Missing fixture: {path}")

    for path in fixture_paths[:4]:
        contexts = load_ticket_contexts("", ticket_json=path)
        if len(contexts) != 1:
            raise SchemaError(f"{path.name}: expected one context, got {len(contexts)}")
        validate(contexts[0].to_dict(), schemas["ticket-context.schema.json"], schemas, path.name)
        validate(build_ticket_plan(contexts[0]).to_dict(), schemas["ticket-plan.schema.json"], schemas, path.name)

    sandbox_paths = sorted((FIXTURE_DIR / "sandbox").glob("*.json"))
    if len(sandbox_paths) < 3:
        raise SchemaError("fixtures/tickets/sandbox must contain GitHub, Jira, and Linear payloads")
    for path in sandbox_paths:
        contexts = load_ticket_contexts("", ticket_json=path)
        if len(contexts) != 1:
            raise SchemaError(f"{path.name}: expected one context, got {len(contexts)}")
        validate(contexts[0].to_dict(), schemas["ticket-context.schema.json"], schemas, path.name)
        validate(build_ticket_plan(contexts[0]).to_dict(), schemas["ticket-plan.schema.json"], schemas, path.name)

    batch_contexts = load_ticket_contexts("", ticket_json=FIXTURE_DIR / "batch.json")
    if len(batch_contexts) < 2:
        raise SchemaError("batch.json must contain at least two tickets")
    for index, context in enumerate(batch_contexts):
        label = f"batch.json[{index}]"
        validate(context.to_dict(), schemas["ticket-context.schema.json"], schemas, label)
        validate(build_ticket_plan(context).to_dict(), schemas["ticket-plan.schema.json"], schemas, label)

    with tempfile.TemporaryDirectory() as tmp:
        log_dir = Path(tmp)
        sep_log = log_dir / "2026-04-22T10-00-00-hotfix-hotfix123.md"
        sep_log.write_text(
            "\n".join(
                [
                    "---",
                    "run_id: hotfix123",
                    "skill: hotfix",
                    "timestamp: 2026-04-22T10:00:00Z",
                    "status: completed",
                    "final_status: completed",
                    "checkpoints: [preflight-passed, patch-applied]",
                    "fallbacks_invoked: []",
                    "gates_blocked: []",
                    "findings_critical: 0",
                    "findings_high: 0",
                    "postmortem_recommended: true",
                    "---",
                    "",
                    "## Output Digest",
                    "Checkout hotfix completed.",
                    "",
                ]
            )
        )
        run = parse_sep_log(sep_log)
        if run is None:
            raise SchemaError("Synthetic SEP log did not parse")
        validate(run.__dict__, schemas["sep-run.schema.json"], schemas, "synthetic sep run")
        validate(build_dashboard_report(log_dir).to_dict(), schemas["dashboard-report.schema.json"], schemas, "dashboard")

    event = {
        "event_type": "ticket.plan.created",
        "ticket_id": "LIN-123",
        "ticket_source": "linear",
        "payload": {"recommended_skill": "prompt-review"},
        "created_at": "2026-04-22T12:00:00Z",
    }
    validate(event, schemas["run-event.schema.json"], schemas, "run event")

    print("console contract schemas validated")
    return 0


def validate(instance: Any, schema: dict[str, Any], schemas: dict[str, dict[str, Any]], label: str) -> None:
    _validate(instance, schema, schemas, label)


def _validate(instance: Any, schema: dict[str, Any], schemas: dict[str, dict[str, Any]], path: str) -> None:
    if "$ref" in schema:
        ref = schema["$ref"]
        try:
            schema = schemas[Path(ref).name]
        except KeyError as exc:
            raise SchemaError(f"{path}: unresolved schema ref {ref}") from exc

    expected = schema.get("type")
    if expected:
        _validate_type(instance, expected, path)

    if "enum" in schema and instance not in schema["enum"]:
        raise SchemaError(f"{path}: {instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, str) and len(instance) < int(schema.get("minLength", 0)):
        raise SchemaError(f"{path}: string shorter than minLength {schema['minLength']}")

    if isinstance(instance, (int, float)) and "minimum" in schema and instance < schema["minimum"]:
        raise SchemaError(f"{path}: {instance!r} is below minimum {schema['minimum']}")

    if isinstance(instance, (int, float)) and "maximum" in schema and instance > schema["maximum"]:
        raise SchemaError(f"{path}: {instance!r} is above maximum {schema['maximum']}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in instance]
        if missing:
            raise SchemaError(f"{path}: missing required keys {missing}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = sorted(set(instance) - set(properties))
            if extra:
                raise SchemaError(f"{path}: unexpected keys {extra}")

        for key, value in instance.items():
            if key in properties:
                _validate(value, properties[key], schemas, f"{path}.{key}")

    if isinstance(instance, list) and "items" in schema:
        for index, value in enumerate(instance):
            _validate(value, schema["items"], schemas, f"{path}[{index}]")


def _validate_type(instance: Any, expected: str, path: str) -> None:
    checks = {
        "object": lambda value: isinstance(value, dict),
        "array": lambda value: isinstance(value, list),
        "string": lambda value: isinstance(value, str),
        "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "number": lambda value: (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool),
        "boolean": lambda value: isinstance(value, bool),
    }
    if expected not in checks:
        raise SchemaError(f"{path}: unsupported schema type {expected}")
    if not checks[expected](instance):
        raise SchemaError(f"{path}: expected {expected}, got {type(instance).__name__}")


if __name__ == "__main__":
    raise SystemExit(main())
