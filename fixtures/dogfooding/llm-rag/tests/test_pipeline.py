"""Unit tests for the RAG pipeline."""
from src.pipeline.ingestor import ingest


def test_ingest_splits_long_text():
    text = "word " * 1000
    chunks = ingest(text, chunk_size=100, chunk_overlap=10)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 120  # allow slight overflow from overlap


def test_ingest_short_text_returns_single_chunk():
    text = "short document"
    chunks = ingest(text)
    assert len(chunks) == 1
    assert chunks[0] == text
