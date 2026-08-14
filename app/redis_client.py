import hashlib

import redis.asyncio as redis
from redis.commands.search.field import TagField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from app.config import settings

_client: redis.Redis | None = None

FAQ_INDEX = "idx:faq"
FAQ_PREFIX = "faq:doc:"


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=False)
    return _client


def _doc_id(question: str) -> str:
    normalized = question.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


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
    )
    await r.ft(FAQ_INDEX).create_index(
        schema, definition=IndexDefinition(prefix=[FAQ_PREFIX], index_type=IndexType.HASH)
    )


async def set_faq_entry(question: str, answer: str, category: str | None = None) -> None:
    await ensure_faq_index()
    key = f"{FAQ_PREFIX}{_doc_id(question)}"
    r = get_redis()
    await r.hset(
        key,
        mapping={
            "question": question,
            "answer": answer,
            "category": category or "",
        },
    )
    await r.expire(key, settings.FAQ_CACHE_TTL_SECONDS)


async def find_faq(question: str) -> dict | None:
    await ensure_faq_index()
    r = get_redis()
    query = Query(f"@question:{question}").paging(0, 1)
    result = await r.ft(FAQ_INDEX).search(query)
    if not result.docs:
        return None
    doc = result.docs[0]
    return {
        "question": doc.question,
        "answer": doc.answer,
        "category": doc.category,
    }
