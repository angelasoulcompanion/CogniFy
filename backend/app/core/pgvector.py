"""
CogniFy pgvector Utilities
Single source of truth for embedding ↔ pgvector conversion
"""

from typing import Any, List


def embedding_to_pgvector(embedding: Any) -> str:
    """
    Convert an embedding to pgvector string format.

    pgvector expects: "[0.1,0.2,0.3,...]" as a string.
    Input can be: list of floats, nested list, numpy array, or already a string.

    Args:
        embedding: The embedding in any common format

    Returns:
        pgvector-compatible string like "[0.1,0.2,...]"

    Raises:
        ValueError: If the embedding cannot be converted
    """
    # Already a string — validate and return
    if isinstance(embedding, str):
        if embedding.startswith("[") and embedding.endswith("]"):
            return embedding
        return f"[{embedding}]"

    # Nested list [[...]] — unwrap one level
    if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], list):
        embedding = embedding[0]

    # List / iterable of numbers
    if hasattr(embedding, "__iter__"):
        values = ",".join(str(float(v)) for v in embedding)
        return f"[{values}]"

    raise ValueError(f"Cannot convert embedding of type {type(embedding)} to pgvector format")
