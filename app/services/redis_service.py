import hashlib
import struct

import redis.asyncio as redis
from redis.commands.search.field import TagField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType

from app.config import settings
from app.constants import FAQ_INDEX_NAME, FAQ_KEY_PREFIX

_client: redis.Redis | None = None

FAQ_INDEX = FAQ_INDEX_NAME
FAQ_PREFIX = FAQ_KEY_PREFIX


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=False)
    return _client


def _doc_id(question: str) -> str:
    normalized = question.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def _vec_bytes(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


async def ensure_faq_index() -> None:
    r = get_redis()
    try:
        await r.ft(FAQ_INDEX).info()
        return
    except Exception:
        pass
    schema = (
        TextField("question"),
        TextField("answer"),
        TagField("category"),
        VectorField(
            "embedding",
            "HNSW",
            {"TYPE": "FLOAT32", "DIM": settings.EMBED_DIM, "DISTANCE_METRIC": "COSINE"},
        ),
    )
    await r.ft(FAQ_INDEX).create_index(
        schema,
        definition=IndexDefinition(prefix=[FAQ_PREFIX], index_type=IndexType.HASH),
    )


async def set_faq_entry(
    question: str, answer: str, embedding: list[float], category: str | None = None
) -> None:
    await ensure_faq_index()
    key = f"{FAQ_PREFIX}{_doc_id(question)}"
    r = get_redis()
    await r.hset(
        key,
        mapping={
            "question": question,
            "answer": answer,
            "category": category or "",
            "embedding": _vec_bytes(embedding),
        },
    )
    await r.expire(key, settings.FAQ_CACHE_TTL_SECONDS)
