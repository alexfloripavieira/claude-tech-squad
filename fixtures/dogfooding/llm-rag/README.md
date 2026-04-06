# llm-rag fixture

RAG pipeline fixture for dogfooding the claude-tech-squad AI specialist bench.

## Purpose

Simulates a production RAG service (Anthropic SDK + LangChain) to validate that the discovery skill activates AI-specific specialists (`ai-engineer`, `llm-eval-specialist`) and does not route to generic backend agents alone.

## Structure

```
src/
  pipeline/
    ingestor.py       # document ingestion and chunking
    embedder.py       # embedding generation (Anthropic embeddings)
    retriever.py      # vector store retrieval
  eval/
    eval_harness.py   # RAGAS evaluation harness
tests/
  test_pipeline.py    # unit tests for chunking and retrieval
pyproject.toml
```
