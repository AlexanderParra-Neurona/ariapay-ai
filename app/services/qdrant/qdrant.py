import hashlib

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.config import settings
from app.services.llm import get_llm_service
from app.services.qdrant.embeddings import LLMServiceEmbeddings

COLLECTION_NAME = settings.QDRANT_COLLECTION


class QdrantService:
    def __init__(self) -> None:
        self._client = _QdrantClient(url=settings.QDRANT_URL)
        self._embeddings = LLMServiceEmbeddings(get_llm_service())
        self._ensure_collection()
        self._store = QdrantVectorStore(
            client=self._client,
            collection_name=COLLECTION_NAME,
            embedding=self._embeddings,
        )

    def _ensure_collection(self) -> None:
        if self._client.collection_exists(COLLECTION_NAME):
            return
        self._client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=settings.EMBED_DIM, distance=Distance.COSINE),
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
        self._store.add_documents([doc], ids=[point_id])

    def similarity_search(self, query: str, k: int = 4) -> list[Document]:
        return self._store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        return self._store.similarity_search_with_score(query, k=k)

    @property
    def client(self) -> _QdrantClient:
        return self._client

    @property
    def collection_name(self) -> str:
        return COLLECTION_NAME
