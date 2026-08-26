import logging

from langchain_core.documents import Document
from qdrant_client.http.models import FieldCondition, Filter, MatchValue
from rank_bm25 import BM25Okapi

from app.services.qdrant.qdrant import QdrantService

logger = logging.getLogger("ariabot.retrieval.sparse")


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


class SparseRetriever:
    def __init__(self, qdrant_service: QdrantService) -> None:
        self._docs: list[Document] = []
        self._bm25: BM25Okapi | None = None
        self._load_corpus(qdrant_service)

    def _load_corpus(self, qdrant_service: QdrantService) -> None:
        docs: list[Document] = []
        offset = None
        while True:
            batch, offset = qdrant_service.client.scroll(
                qdrant_service.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.type", match=MatchValue(value="doc")
                        )
                    ]
                ),
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in batch:
                payload = point.payload or {}
                docs.append(
                    Document(
                        page_content=payload.get("page_content", ""),
                        metadata=payload.get("metadata", {}),
                    )
                )
            if offset is None:
                break

        self._docs = docs
        corpus_tokens = [_tokenize(d.page_content) for d in docs]
        self._bm25 = BM25Okapi(corpus_tokens) if corpus_tokens else None
        logger.info("sparse_corpus_loaded doc_count=%d", len(docs))

    def search(self, query: str, top_k: int) -> list[tuple[Document, float]]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [(self._docs[i], scores[i]) for i in ranked[:top_k] if scores[i] > 0]
