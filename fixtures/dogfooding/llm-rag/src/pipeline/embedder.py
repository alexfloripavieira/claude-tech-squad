"""Embedding generation using the Anthropic SDK."""
import anthropic


def embed(texts: list[str], model: str = "voyage-3") -> list[list[float]]:
    """Generate embeddings for a list of text chunks via Anthropic."""
    client = anthropic.Anthropic()
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.embeddings]
