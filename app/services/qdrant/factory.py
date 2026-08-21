from functools import lru_cache

from app.config import settings
from app.services.qdrant.client import QdrantClient


@lru_cache(maxsize=1)
def make_qdrant_service() -> QdrantClient:
    """
    Initializes and returns a singleton QdrantClient instance.

    The result is cached using lru_cache to ensure only one instance
    of the client is created and returned on subsequent calls.

    Returns:
        QdrantClient: The initialized, cached singleton Qdrant client instance.

    Raises:
        RuntimeError: If QdrantClient instantiation fails due to invalid settings.
    """
    try:
        return QdrantClient(settings)
    except TypeError as e:
        raise RuntimeError(f"Failed to initialize Qdrant service: {e}") from e
    except Exception as e:
        raise RuntimeError(
            f"An unexpected error occurred during Qdrant service initialization: {e}"
        ) from e
