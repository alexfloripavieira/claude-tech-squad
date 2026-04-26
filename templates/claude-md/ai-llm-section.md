## AI / LLM Workflow Rules

This project uses LLM/AI libraries: {{detected_llm_libraries}}.

### Mandatory Gates Before Release

- Before any release that includes AI changes: run `/claude-tech-squad:llm-eval`
- Before merging any PR that changes prompt files: run `/claude-tech-squad:prompt-review`
- Before shipping RAG changes: compare retrieval quality against the latest eval baseline

### Recommended AI Feature Flow

1. `/claude-tech-squad:discovery` to shape the AI feature with AI-aware specialists.
2. `/claude-tech-squad:implement` for TDD-first implementation.
3. `/claude-tech-squad:prompt-review` before merging prompt changes.
4. `/claude-tech-squad:llm-eval` before release.
5. `/claude-tech-squad:release` to cut the release.

### Detected AI Dependencies

{{detected_llm_libraries_baseline}}
