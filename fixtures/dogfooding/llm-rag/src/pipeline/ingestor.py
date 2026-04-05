"""Document ingestion and chunking for the RAG pipeline."""
from langchain.text_splitter import RecursiveCharacterTextSplitter


def ingest(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[str]:
    """Split raw text into overlapping chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_text(text)
