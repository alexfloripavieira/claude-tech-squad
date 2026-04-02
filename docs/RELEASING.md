# Releasing `claude-tech-squad`

## How Auto-Update Works

When users install the plugin with `autoUpdate: true` in their `~/.claude/settings.json`, Claude Code periodically checks the marketplace for new versions by reading `marketplace.json` from the repository. When it detects a version bump, it updates automatically.

For this to work every release must:
1. Bump both `marketplace.json` and `plugin.json` to the same version
2. Keep `docs/MANUAL.md` on the same version
3. Have a CHANGELOG entry for the version
4. Merge the release metadata to `main`

## Official Release Path

The official path is **GitHub Actions automation on `main`**.

When your release automation updates the version files and changelog on `main`, the repository pipeline now does the rest:

- runs `scripts/smoke-test.sh`
- verifies changelog and version alignment
- builds a release bundle and checksum
- creates and pushes the git tag automatically
- creates or updates the GitHub Release
- uploads the bundle as a release asset

Before release, the expected quality bar is:

- `bash scripts/validate.sh`
- `bash scripts/smoke-test.sh`
- `bash scripts/dogfood.sh`
- `bash scripts/dogfood-report.sh --schema-only`

For release-critical workflow changes, also run real golden runs and validate them with:

```bash
bash scripts/dogfood-report.sh
```

## Versioning Policy

Use semantic versioning.

- **major**: workflow contract changes or roster changes that alter expected behavior
- **minor**: new specialists, stronger docs, or meaningful workflow improvements
- **patch**: documentation, wording, and low-risk fixes

## Release Process (Automated)

### Step 1 — Your automation updates release metadata

Your release automation should update:

- `.claude-plugin/marketplace.json`
- `plugins/claude-tech-squad/.claude-plugin/plugin.json`
- `docs/MANUAL.md`
- `CHANGELOG.md`

The changelog must include a section like:

```markdown
## [5.2.0] - 2026-MM-DD — Short description

### Added
- ...

### Changed
- ...
```

### Step 2 — Your automation merges the release commit to `main`

When the release metadata lands on `main`, `.github/workflows/release.yml` runs automatically.
It derives the version from `plugin.json`, validates it, creates `vX.Y.Z`, builds the bundle, and publishes the GitHub Release.

### Step 3 — Verify on GitHub

After pushing, check:
- GitHub Actions tab: `publish` workflow passes
- Releases page: release exists or was updated with the right notes
- release assets include the tarball and checksum
- `marketplace.json`, `plugin.json`, and `MANUAL.md` match the release version
- the workflow-created tag matches the release version

## Optional Fallback Script

If your automation is unavailable and you need an emergency fallback, `scripts/release.sh` still exists. It is no longer the primary path.

If you need to release manually:

```bash
# 1. Bump versions manually
# Edit .claude-plugin/marketplace.json — plugins[0].version
# Edit plugins/claude-tech-squad/.claude-plugin/plugin.json — version
# Edit docs/MANUAL.md — version

# 2. Validate
bash scripts/smoke-test.sh

# 3. Commit
git add .claude-plugin/marketplace.json plugins/claude-tech-squad/.claude-plugin/plugin.json docs/MANUAL.md CHANGELOG.md
git commit -m "chore: release vX.Y.Z"

# 4. Tag and push
git tag vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

## User Configuration for Auto-Update

Users must have this in `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "alexfloripavieira-plugins": {
      "source": { "source": "github", "repo": "alexfloripavieira/claude-tech-squad" },
      "autoUpdate": true
    }
  }
}
```

With `autoUpdate: true`, Claude Code picks up new versions automatically when a new tag is published.
