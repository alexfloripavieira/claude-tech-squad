# Releasing `claude-tech-squad`

## Versioning Policy

Use semantic versioning.

- major: workflow contract changes or roster changes that alter expected behavior
- minor: new specialists, stronger docs, new capabilities, or meaningful workflow improvements
- patch: documentation, wording, and low-risk fixes

## Release Checklist

1. Run `scripts/validate.sh`
2. Review the roster and workflow docs for consistency
3. Update `CHANGELOG.md`
4. Bump versions in:
   - `.claude-plugin/marketplace.json`
   - `plugins/claude-tech-squad/.claude-plugin/plugin.json`
5. Create a git tag and release notes
