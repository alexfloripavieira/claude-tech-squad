# Releasing `claude-tech-squad`

## How Auto-Update Works

When users install the plugin with `autoUpdate: true` in their `~/.claude/settings.json`, Claude Code periodically checks the marketplace for new versions by reading `marketplace.json` from the repository. When it detects a version bump, it updates automatically.

For this to work every release must:
1. Bump both `marketplace.json` and `plugin.json` to the same version
2. Push a git tag `v<version>` to GitHub
3. Have a CHANGELOG entry for the version

The `scripts/release.sh` script does all of this in one command.

## Versioning Policy

Use semantic versioning.

- **major**: workflow contract changes or roster changes that alter expected behavior
- **minor**: new specialists, stronger docs, or meaningful workflow improvements
- **patch**: documentation, wording, and low-risk fixes

## Release Process (Automated)

### Step 1 — Add CHANGELOG entry

Add a section to `CHANGELOG.md` before releasing:

```markdown
## [5.2.0] - 2026-MM-DD — Short description

### Added
- ...

### Changed
- ...
```

### Step 2 — Run the release script

```bash
./scripts/release.sh 5.2.0
```

This script:
1. Validates the plugin (`scripts/validate.sh`)
2. Bumps `marketplace.json` and `plugin.json` to the new version
3. Checks that `CHANGELOG.md` has an entry for the version
4. Commits the version bumps
5. Creates and pushes the git tag `v5.2.0`
6. GitHub Actions (`release.yml`) then creates the GitHub Release automatically with the changelog notes extracted from `CHANGELOG.md`

### Step 3 — Verify on GitHub

After pushing, check:
- GitHub Actions tab: `release` workflow passes
- Releases page: new release created with correct notes
- `marketplace.json` on `main`: version matches the tag

## Manual Release (if needed)

If you need to release without the script:

```bash
# 1. Bump versions manually
# Edit .claude-plugin/marketplace.json — plugins[0].version
# Edit plugins/claude-tech-squad/.claude-plugin/plugin.json — version

# 2. Validate
bash scripts/validate.sh

# 3. Commit
git add .claude-plugin/marketplace.json plugins/claude-tech-squad/.claude-plugin/plugin.json
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
