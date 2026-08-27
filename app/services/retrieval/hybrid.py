import logging

from langchain_core.documents import Document

from app.config import settings
from app.services.classification.types import TransactionScope
from app.services.qdrant.qdrant import QdrantService
from app.services.retrieval.fusion import rrf_fuse
from app.services.retrieval.sparse import SparseRetriever

logger = logging.getLogger("ariabot.retrieval.hybrid")


class HybridRetriever:
    def __init__(self, qdrant_service: QdrantService) -> None:
        self._qdrant_service = qdrant_service
        self._sparse = SparseRetriever(qdrant_service)

    def search(self, query: str, top_k: int | None = None) -> list[Document]:
        top_k = top_k or settings.RETRIEVAL_TOP_K
        pool = settings.RETRIEVAL_CANDIDATE_POOL

        dense_hits = self._qdrant_service.similarity_search_with_score(query, k=pool)
        sparse_hits = self._sparse.search(query, top_k=pool)

        if not dense_hits and not sparse_hits:
            logger.info("hybrid_search_empty query=%r", query)
            return []

        fused = rrf_fuse([dense_hits, sparse_hits])[:top_k]
        docs = [doc for doc, _ in fused]

        if docs:
            top = docs[0]
            logger.info(
                "hybrid_search query=%r result_count=%d top_source=%s top_heading=%s",
                query,
                len(docs),
                top.metadata.get("source"),
                top.metadata.get("heading"),
            )
        return docs

    def search_transactions(
        self,
        query: str,
        scope: TransactionScope | None = None,
        top_k: int | None = None,
    ) -> list[Document]:
        if scope is not None and scope.wants_all:
            docs = self._qdrant_service.get_all_transactions(
                category=scope.category, max_results=settings.TRANSACTIONS_MAX_ALL
            )
            logger.info(
                "hybrid_search_transactions_all query=%r category=%s result_count=%d",
                query,
                scope.category,
                len(docs),
            )
            return docs

        top_k = top_k or settings.RETRIEVAL_TOP_K
        hits = self._qdrant_service.similarity_search_transactions_with_score(
            query, k=top_k
        )
        docs = [doc for doc, _ in hits]
        logger.info(
            "hybrid_search_transactions query=%r result_count=%d", query, len(docs)
        )
        return docs
