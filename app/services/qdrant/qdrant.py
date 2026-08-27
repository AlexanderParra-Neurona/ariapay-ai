import hashlib

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    VectorParams,
)

from app.config import settings
from app.services.llm import LLMServiceEmbeddings, get_llm_service

COLLECTION_NAME = settings.QDRANT_COLLECTION
DOCS_VECTOR = "docs"
TRANSACTIONS_VECTOR = "transactions"


class QdrantService:
    def __init__(self, embeddings: Embeddings | None = None) -> None:
        self._client = _QdrantClient(url=settings.QDRANT_URL)
        self._embeddings = embeddings or LLMServiceEmbeddings(get_llm_service())
        self._ensure_collection()
        self._docs_store = QdrantVectorStore(
            client=self._client,
            collection_name=COLLECTION_NAME,
            embedding=self._embeddings,
            vector_name=DOCS_VECTOR,
        )
        self._transactions_store = QdrantVectorStore(
            client=self._client,
            collection_name=COLLECTION_NAME,
            embedding=self._embeddings,
            vector_name=TRANSACTIONS_VECTOR,
        )

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(COLLECTION_NAME):
            self._verify_schema()
            return
        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                DOCS_VECTOR: VectorParams(
                    size=settings.EMBED_DIM, distance=Distance.COSINE
                ),
                TRANSACTIONS_VECTOR: VectorParams(
                    size=settings.EMBED_DIM, distance=Distance.COSINE
                ),
            },
        )

    def _verify_schema(self) -> None:
        vectors = self._client.get_collection(COLLECTION_NAME).config.params.vectors
        if (
            not isinstance(vectors, dict)
            or DOCS_VECTOR not in vectors
            or TRANSACTIONS_VECTOR not in vectors
        ):
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' exists with an incompatible schema "
                f"(expected named vectors '{DOCS_VECTOR}' and '{TRANSACTIONS_VECTOR}'). "
                "Drop the collection and re-run ingestion to migrate."
            )

    @staticmethod
    def _point_id(text: str) -> str:
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    def upsert_doc_chunk(self, source: str, heading: str, text: str) -> None:
        self.upsert_doc_chunks([(source, heading, text)])

    def upsert_doc_chunks(self, chunks: list[tuple[str, str, str]]) -> None:
        if not chunks:
            return
        docs = [
            Document(
                page_content=f"{heading}\n\n{text}" if heading else text,
                metadata={"type": "doc", "source": source, "heading": heading},
            )
            for source, heading, text in chunks
        ]
        ids = [self._point_id(f"{source}:{heading}") for source, heading, _ in chunks]
        self._docs_store.add_documents(docs, ids=ids)

    def upsert_transaction(
        self, merchant_name: str, category: str, price: float, timestamp: str
    ) -> None:
        self.upsert_transactions([(merchant_name, category, price, timestamp)])

    def upsert_transactions(
        self, transactions: list[tuple[str, str, float, str]]
    ) -> None:
        if not transactions:
            return
        docs = [
            Document(
                page_content=f"{merchant_name} ({category}) - Rp{price:,.0f} on {timestamp}",
                metadata={
                    "type": "transaction",
                    "merchant_name": merchant_name,
                    "category": category,
                    "price": price,
                    "timestamp": timestamp,
                },
            )
            for merchant_name, category, price, timestamp in transactions
        ]
        ids = [
            self._point_id(f"{merchant_name}:{timestamp}")
            for merchant_name, _, _, timestamp in transactions
        ]
        self._transactions_store.add_documents(docs, ids=ids)

    def similarity_search(self, query: str, k: int = 4) -> list[Document]:
        return self._docs_store.similarity_search(query, k=k)

    def similarity_search_with_score(
        self, query: str, k: int = 4
    ) -> list[tuple[Document, float]]:
        return self._docs_store.similarity_search_with_score(query, k=k)

    def similarity_search_transactions(self, query: str, k: int = 4) -> list[Document]:
        return self._transactions_store.similarity_search(query, k=k)

    def similarity_search_transactions_with_score(
        self, query: str, k: int = 4
    ) -> list[tuple[Document, float]]:
        return self._transactions_store.similarity_search_with_score(query, k=k)

    def get_all_transactions(
        self, category: str | None = None, max_results: int = 200
    ) -> list[Document]:
        must = [
            FieldCondition(key="metadata.type", match=MatchValue(value="transaction"))
        ]
        if category is not None:
            must.append(
                FieldCondition(
                    key="metadata.category", match=MatchValue(value=category)
                )
            )

        docs: list[Document] = []
        offset = None
        while len(docs) < max_results:
            batch, offset = self._client.scroll(
                self.collection_name,
                scroll_filter=Filter(must=must),
                limit=min(1000, max_results - len(docs)),
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
        return docs[:max_results]

    @property
    def client(self) -> _QdrantClient:
        return self._client

    @property
    def collection_name(self) -> str:
        return COLLECTION_NAME
