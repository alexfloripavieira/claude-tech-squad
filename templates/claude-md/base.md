# CLAUDE.md

## Project Overview

{{project_name}} — {{project_description}}

**Stack:** {{detected_stack}}
**CI/CD:** {{detected_ci}}
**Container:** {{containerized}}

## Essential Commands

```bash
# Development
{{start_command}}

# Testing
{{test_command}}

# Lint
{{lint_command}}

# Build
{{build_command}}

# Database migrations
{{migrate_command}}
```

## Architecture

{{architecture_summary}}

## Key Conventions

- Keep changes scoped to the requested behavior.
- Prefer existing project patterns over new abstractions.
- Update tests with behavior changes.
- Do not commit or push without explicit authorization.

## Workflow Rules

- First run in this repository: `/claude-tech-squad:onboarding`
- Bug fixes that touch one or two files: fix directly or use `/claude-tech-squad:bug-fix`
- Features that touch three or more files: use `/claude-tech-squad:squad`
- Blueprint only: use `/claude-tech-squad:discovery`
- Build from an approved blueprint: use `/claude-tech-squad:implement`
- Production emergency: use `/claude-tech-squad:hotfix`
- Pull request review: use `/claude-tech-squad:pr-review`

## Squad Artifacts

- `ai-docs/` stores squad outputs and health baselines.
- `ai-docs/.squad-log/` stores SEP execution logs and must stay ignored by git.
- Keep generated artifacts out of source folders unless the skill explicitly asks for them.
