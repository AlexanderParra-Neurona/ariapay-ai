from langchain_core.documents import Document

from app.config import settings
from app.services.classification.types import TransactionScope
from app.services.qdrant.qdrant import QdrantService


class HybridRetriever:
    def __init__(self, qdrant_service: QdrantService) -> None:
        self._qdrant_service = qdrant_service

    def search_transactions(
        self,
        query: str,
        scope: TransactionScope | None = None,
        top_k: int | None = None,
    ) -> list[Document]:
        if scope is not None and scope.wants_all:
            return self._qdrant_service.get_all_transactions(
                category=scope.category, max_results=settings.TRANSACTIONS_MAX_ALL
            )

        top_k = top_k or settings.RETRIEVAL_TOP_K
        category = scope.category if scope is not None else None
        hits = self._qdrant_service.similarity_search_transactions_with_score(
            query, k=top_k, category=category
        )
        return [doc for doc, _ in hits]
