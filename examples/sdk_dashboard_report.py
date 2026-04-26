from __future__ import annotations

from squad_cli.sdk import create_client


def main() -> None:
    client = create_client(project_root=".", plugin_root="plugins/claude-tech-squad")
    print(client.dashboard_report(limit=5).to_json())


if __name__ == "__main__":
    main()
