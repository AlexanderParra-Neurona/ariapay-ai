from functools import lru_cache

from app.services.qdrant.qdrant import QdrantService


@lru_cache
def get_qdrant_service() -> QdrantService:
    return QdrantService()
