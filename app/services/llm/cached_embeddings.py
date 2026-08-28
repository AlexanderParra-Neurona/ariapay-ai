import hashlib
import json
from pathlib import Path

from langchain_core.embeddings import Embeddings


class FileCachedEmbeddings(Embeddings):
    """Wraps an Embeddings backend with an on-disk cache keyed by text hash.

    Persists across process/container restarts so re-running ingestion on
    unchanged content skips the underlying API call entirely.
    """

    def __init__(self, embeddings: Embeddings, cache_path: Path) -> None:
        self._embeddings = embeddings
        self._cache_path = cache_path
        self._cache: dict[str, list[float]] = self._load()

    def _load(self) -> dict[str, list[float]]:
        if not self._cache_path.exists():
            return {}
        return json.loads(self._cache_path.read_text())

    def _save(self) -> None:
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(json.dumps(self._cache))

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        keys = [self._key(text) for text in texts]
        missing = [
            (text, key)
            for text, key in zip(texts, keys)
            if key not in self._cache
        ]
        if missing:
            fresh = self._embeddings.embed_documents([text for text, _ in missing])
            for (_, key), vector in zip(missing, fresh):
                self._cache[key] = vector
            self._save()
        return [self._cache[key] for key in keys]

    def embed_query(self, text: str) -> list[float]:
        key = self._key(text)
        if key not in self._cache:
            self._cache[key] = self._embeddings.embed_query(text)
            self._save()
        return self._cache[key]
