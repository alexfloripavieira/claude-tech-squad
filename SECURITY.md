# Security Policy

## Scope

This repository contains orchestration logic, workflow contracts, and operational guidance. Security issues here can affect:

- production decision quality
- rollout safety
- incident handling
- privacy and compliance gates
- reliability of generated operational actions

Treat workflow-level vulnerabilities seriously.

## Reporting

If you find a security issue:

1. Do not include secrets, tokens, credentials, or live exploit payloads in a public issue.
2. Prefer a minimal initial report with reproduction conditions and impact.
3. If private reporting is available on the repository, use it.
4. If private reporting is not available, open a limited public issue that requests a secure follow-up path without disclosing sensitive details.

## What Counts As A Security Issue

- prompts or workflow gaps that can bypass security review
- missing or weakened privacy/compliance gates
- orchestration that can skip required validation silently
- dangerous release or hotfix behavior without explicit guardrails
- stale references that route outside the intended plugin namespace

## Expected Fix Handling

- security-relevant workflow fixes should be treated as high priority
- release-critical changes should get updated docs and validation evidence
- incidents caused by workflow gaps should produce a post-mortem and a retrospective follow-up
