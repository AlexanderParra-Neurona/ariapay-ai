import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.services.ollama_service import embed
from app.services.qdrant.factory import make_qdrant_service

SEED_FILE = Path("data/seed/faq_docs.json")


def load_seed_docs() -> list[dict]:
    return json.loads(SEED_FILE.read_text())


async def seed() -> None:
    service = make_qdrant_service()
    docs = load_seed_docs()
    for doc in docs:
        vector = await embed(doc["question"])
        await service.upsert_faq_entry(doc["question"], doc["answer"], vector, category=doc["category"])
    print(f"Seeded {len(docs)} entries across {len({d['category'] for d in docs})} categories.")


async def clear() -> None:
    service = make_qdrant_service()
    if await service.client.collection_exists(service.collection_name):
        await service.client.delete_collection(service.collection_name)
    print(f"Cleared collection: {service.collection_name}")


if __name__ == "__main__":
    if "--clear" in sys.argv:
        asyncio.run(clear())
    else:
        asyncio.run(seed())
