import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.embeddings import embed
from app.redis_client import FAQ_PREFIX, get_redis, set_faq_entry

SEED_FILE = Path("data/seed/faq_docs.json")


def load_seed_docs() -> list[dict]:
    return json.loads(SEED_FILE.read_text())


async def seed() -> None:
    docs = load_seed_docs()
    for doc in docs:
        vector = await embed(doc["question"])
        await set_faq_entry(doc["question"], doc["answer"], vector, category=doc["category"])
    print(f"Seeded {len(docs)} entries across {len({d['category'] for d in docs})} categories.")


async def clear() -> None:
    r = get_redis()
    keys = [key async for key in r.scan_iter(match=f"{FAQ_PREFIX}*")]
    deleted = await r.delete(*keys) if keys else 0
    print(f"Cleared {deleted} entries.")


if __name__ == "__main__":
    if "--clear" in sys.argv:
        asyncio.run(clear())
    else:
        asyncio.run(seed())
