from functools import lru_cache

from app.services.qdrant.factory import get_qdrant_service
from app.services.retrieval.hybrid import HybridRetriever


@lru_cache
def get_hybrid_retriever() -> HybridRetriever:
    return HybridRetriever(get_qdrant_service())
