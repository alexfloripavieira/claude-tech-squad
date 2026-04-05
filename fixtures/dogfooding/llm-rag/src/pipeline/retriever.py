"""Vector store retrieval for the RAG pipeline."""
import chromadb
from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA


def build_qa_chain(collection_name: str = "docs") -> RetrievalQA:
    """Build a RetrievalQA chain backed by ChromaDB and Claude."""
    client = chromadb.Client()
    collection = client.get_or_create_collection(collection_name)
    llm = ChatAnthropic(model="claude-opus-4-6")
    # Chain wires retriever → LLM for grounded answers
    return RetrievalQA.from_chain_type(llm=llm, retriever=collection.as_retriever())
