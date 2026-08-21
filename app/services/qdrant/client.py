import hashlib
from typing import Dict

from qdrant_client import AsyncQdrantClient, models

from app.config import Settings


class QdrantClient:
    """
    Manages async connections to a Qdrant vector store.

    This class handles client initialization and provides methods for
    health checks, FAQ collection management, and similarity search.

    Attributes:
        base_url (str): The Qdrant service URL.
        collection_name (str): The FAQ collection name.
        client (AsyncQdrantClient): The underlying Qdrant async client.
    """

    base_url: str
    collection_name: str
    client: AsyncQdrantClient

    def __init__(self, settings: Settings) -> None:
        """
        Initializes the QdrantClient and creates the async client.

        Args:
            settings (Settings): The application configuration object containing
                                 Qdrant connection details.

        Raises:
            TypeError: If 'settings' is not an instance of the Settings class.
            RuntimeError: If client creation fails.
        """
        if not isinstance(settings, Settings):
            raise TypeError(
                "Argument 'settings' must be an instance of the Settings class"
            )

        self.base_url = settings.QDRANT_URL
        self.collection_name = settings.QDRANT_COLLECTION
        self._embed_dim = settings.EMBED_DIM

        try:
            self.client = AsyncQdrantClient(url=self.base_url)
        except Exception as e:
            raise RuntimeError(f"Failed to create Qdrant client: {e}") from e

    async def health_check(self) -> Dict[str, str]:
        """
        Performs a health check against the Qdrant service.

        Returns:
            Dict[str, str]: A dictionary containing 'status' ('healthy' or
                            'unhealthy') and a descriptive 'message'.
        """
        try:
            await self.client.get_collections()
            return {"status": "healthy", "message": "Qdrant service is running"}
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Connection to Qdrant failed: {e}",
            }

    @staticmethod
    def _point_id(text: str) -> str:
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    async def ensure_collection(self) -> None:
        """
        Creates the collection if it does not already exist.
        """
        if await self.client.collection_exists(self.collection_name):
            return
        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self._embed_dim, distance=models.Distance.COSINE
            ),
        )

    async def upsert_doc_chunk(
        self, source: str, heading: str, text: str, embedding: list[float]
    ) -> None:
        """
        Upserts a single markdown doc chunk into the collection.
        """
        await self.ensure_collection()
        point_id = self._point_id(f"{source}:{heading}")
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "type": "doc",
                        "source": source,
                        "heading": heading,
                        "text": text,
                    },
                )
            ],
        )
