#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

LAST_TAG="$(git -C "$ROOT" describe --tags --abbrev=0 --match 'v*.*.*' 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  BASE_VERSION="${LAST_TAG#v}"
else
  RANGE="HEAD"
  BASE_VERSION="0.0.0"
fi

COMMITS_RAW="$(git -C "$ROOT" log --format='%s%x1f%b%x1e' $RANGE)"

if [ -z "$COMMITS_RAW" ]; then
  echo "No commits found to release." >&2
  exit 0
fi

PREPARED_JSON="$(python3 - <<'PY' "$BASE_VERSION" "$COMMITS_RAW"
import json
import re
import sys
from datetime import datetime, timezone

base_version = sys.argv[1]
raw = sys.argv[2]

entries = []
for chunk in raw.split("\x1e"):
    chunk = chunk.strip()
    if not chunk:
        continue
    subject, _, body = chunk.partition("\x1f")
    subject = subject.strip()
    body = body.strip()
    if subject.startswith("chore: prepare release v"):
        continue
    entries.append((subject, body))

if not entries:
    print(json.dumps({"skip": True}))
    raise SystemExit(0)

major = False
minor = False

sections = {"Added": [], "Changed": [], "Fixed": []}

def clean_subject(subject: str) -> str:
    cleaned = re.sub(r"^[a-zA-Z]+(?:\([^)]+\))?!?:\s*", "", subject).strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else subject

for subject, body in entries:
    conventional = re.match(r"^(?P<type>[a-zA-Z]+)(?:\([^)]+\))?(?P<bang>!)?:\s*(?P<rest>.+)$", subject)
    change_text = clean_subject(subject)
    is_breaking = "BREAKING CHANGE" in body or (conventional and conventional.group("bang"))

    if is_breaking:
      major = True

    change_type = conventional.group("type").lower() if conventional else "other"

    if change_type == "feat":
        minor = True
        sections["Added"].append(change_text)
    elif change_type == "fix":
        sections["Fixed"].append(change_text)
    else:
        sections["Changed"].append(change_text)

if major:
    bump = "major"
elif minor:
    bump = "minor"
else:
    bump = "patch"

major_v, minor_v, patch_v = map(int, base_version.split("."))
if bump == "major":
    next_version = f"{major_v + 1}.0.0"
elif bump == "minor":
    next_version = f"{major_v}.{minor_v + 1}.0"
else:
    next_version = f"{major_v}.{minor_v}.{patch_v + 1}"

headline_map = {
    "major": "Automated major release",
    "minor": "Automated feature release",
    "patch": "Automated maintenance release",
}

lines = [f"## [{next_version}] - {datetime.now(timezone.utc).strftime('%Y-%m-%d')} — {headline_map[bump]}", ""]
for title in ("Added", "Changed", "Fixed"):
    items = sections[title]
    if not items:
        continue
    lines.append(f"### {title}")
    lines.append("")
    for item in items:
        lines.append(f"- {item}")
    lines.append("")

print(json.dumps({
    "skip": False,
    "base_version": base_version,
    "next_version": next_version,
    "changelog_entry": "\n".join(lines).rstrip() + "\n"
}))
PY
)"

if python3 - <<'PY' "$PREPARED_JSON"
import json, sys
raise SystemExit(0 if json.loads(sys.argv[1]).get("skip") else 1)
PY
then
  echo "No releasable commits found." >&2
  exit 0
fi

NEXT_VERSION="$(python3 - <<'PY' "$PREPARED_JSON"
import json, sys
print(json.loads(sys.argv[1])["next_version"])
PY
)"

CHANGELOG_ENTRY="$(python3 - <<'PY' "$PREPARED_JSON"
import json, sys
print(json.loads(sys.argv[1])["changelog_entry"], end="")
PY
)"

python3 - <<'PY' "$ROOT" "$NEXT_VERSION" "$CHANGELOG_ENTRY"
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
version = sys.argv[2]
entry = sys.argv[3]

marketplace_path = root / ".claude-plugin" / "marketplace.json"
plugin_path = root / "plugins" / "claude-tech-squad" / ".claude-plugin" / "plugin.json"
manual_path = root / "docs" / "MANUAL.md"
changelog_path = root / "CHANGELOG.md"

marketplace = json.loads(marketplace_path.read_text())
marketplace["plugins"][0]["version"] = version
marketplace_path.write_text(json.dumps(marketplace, indent=2) + "\n")

plugin = json.loads(plugin_path.read_text())
plugin["version"] = version
plugin_path.write_text(json.dumps(plugin, indent=2) + "\n")

manual = manual_path.read_text()
manual = re.sub(r"(\*\*Versão:\*\*\s*)([0-9.]+)", rf"\g<1>{version}", manual, count=1)
manual_path.write_text(manual)

changelog = changelog_path.read_text()
if f"## [{version}]" not in changelog:
    if changelog.startswith("# Changelog\n\n"):
        changelog = "# Changelog\n\n" + entry + "\n" + changelog[len("# Changelog\n\n"):]
    else:
        changelog = "# Changelog\n\n" + entry + "\n" + changelog
    changelog_path.write_text(changelog)
PY

echo "$NEXT_VERSION"
