import hashlib

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import settings
from app.services.llm import get_llm_service
from app.services.qdrant.embeddings import LLMServiceEmbeddings

COLLECTION_NAME = settings.QDRANT_COLLECTION
DOCS_VECTOR = "docs"
TRANSACTIONS_VECTOR = "transactions"


class QdrantService:
    def __init__(self) -> None:
        self._client = _QdrantClient(url=settings.QDRANT_URL)
        self._embeddings = LLMServiceEmbeddings(get_llm_service())
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
        doc = Document(
            page_content=f"{heading}\n\n{text}" if heading else text,
            metadata={"type": "doc", "source": source, "heading": heading},
        )
        point_id = self._point_id(f"{source}:{heading}")
        self._docs_store.add_documents([doc], ids=[point_id])

    def upsert_transaction(
        self, merchant_name: str, category: str, price: float, timestamp: str
    ) -> None:
        text = f"{merchant_name} ({category}) - Rp{price:,.0f} on {timestamp}"
        doc = Document(
            page_content=text,
            metadata={
                "type": "transaction",
                "merchant_name": merchant_name,
                "category": category,
                "price": price,
                "timestamp": timestamp,
            },
        )
        point_id = self._point_id(f"{merchant_name}:{timestamp}")
        self._transactions_store.add_documents([doc], ids=[point_id])

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

    @property
    def client(self) -> _QdrantClient:
        return self._client

    @property
    def collection_name(self) -> str:
        return COLLECTION_NAME
