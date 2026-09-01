import json
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.config import settings
from app.services.llm import FileCachedEmbeddings, LLMServiceEmbeddings, get_llm_service
from app.services.qdrant import QdrantService

DATA_DIR = Path("data")
TRANSACTIONS_FILE = Path("data/seed/transactions.json")
CACHE_DIR = Path("data/embed_cache")
HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def get_cached_qdrant_service() -> QdrantService:
    cache_file = (
        CACHE_DIR
        / f"{settings.LLM_PROVIDER}_{settings.EMBED_MODEL}.json".replace("/", "_")
    )
    embeddings = FileCachedEmbeddings(
        LLMServiceEmbeddings(get_llm_service()), cache_file
    )
    return QdrantService(embeddings=embeddings)


def load_md_files() -> list[Path]:
    return sorted(DATA_DIR.glob("*.md"))


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [("", text.strip())]

    chunks = []
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            chunks.append(("", preamble))

    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        chunks.append((heading, body))

    return chunks


def seed_docs(service) -> None:
    files = load_md_files()
    chunks = []
    for path in files:
        text = path.read_text()
        for heading, body in chunk_markdown(text):
            if not body:
                continue
            chunks.append((path.name, heading, body))
    service.upsert_doc_chunks(chunks)
    print(f"Seeded {len(chunks)} doc chunks from {len(files)} files.")


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
    seed_docs(service)
    seed_transactions(service)


if __name__ == "__main__":
    seed()
