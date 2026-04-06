# Repository Rules

## Commands

- Test: `pytest tests/`
- Lint: `ruff check .`
- Build: `python -m compileall src`

## Architecture

This repository implements a Retrieval-Augmented Generation (RAG) pipeline using the Anthropic SDK and LangChain. It is an AI-native service.

- `src/pipeline/` — ingestion, chunking, embedding, and retrieval components
- `src/eval/` — LLM evaluation harness (RAGAS-based)
- `tests/` — unit and integration tests

## Delivery Notes

- All LLM calls must be evaluated before shipping to production
- Prompt changes require a `/prompt-review` pass before merging
- Eval harness must run on every PR (RAGAS metrics: faithfulness, context_precision)
- Use explicit AI/LLM specialists for design decisions: ai-engineer, llm-eval-specialist
