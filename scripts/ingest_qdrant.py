import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.config import settings
from app.services.llm import FileCachedEmbeddings, LLMServiceEmbeddings, get_llm_service
from app.services.qdrant import QdrantService

TRANSACTIONS_FILE = Path("data/seed/transactions.json")
CACHE_DIR = Path("data/embed_cache")


def get_cached_qdrant_service() -> QdrantService:
    cache_file = (
        CACHE_DIR
        / f"{settings.LLM_PROVIDER}_{settings.EMBED_MODEL}.json".replace("/", "_")
    )
    embeddings = FileCachedEmbeddings(
        LLMServiceEmbeddings(get_llm_service()), cache_file
    )
    return QdrantService(embeddings=embeddings)


def seed_transactions(service) -> None:
    if not TRANSACTIONS_FILE.exists():
        return
    transactions = json.loads(TRANSACTIONS_FILE.read_text())
    service.upsert_transactions(
        [
            (txn["merchant_name"], txn["category"], txn["price"], txn["timestamp"])
            for txn in transactions
        ]
    )
    print(f"Seeded {len(transactions)} transactions from {TRANSACTIONS_FILE}.")


def seed() -> None:
    service = get_cached_qdrant_service()
    seed_transactions(service)


if __name__ == "__main__":
    seed()
