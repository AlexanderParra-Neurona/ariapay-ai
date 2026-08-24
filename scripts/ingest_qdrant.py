import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")

from app.services.llm import get_llm_service
from app.services.qdrant.factory import make_qdrant_service

DATA_DIR = Path("data")
HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)


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


async def seed() -> None:
    service = make_qdrant_service()
    files = load_md_files()
    total = 0
    for path in files:
        text = path.read_text()
        for heading, body in chunk_markdown(text):
            if not body:
                continue
            content = f"{heading}\n\n{body}" if heading else body
            vector = get_llm_service().embed(content)
            await service.upsert_doc_chunk(path.name, heading, body, vector)
            total += 1
    print(f"Seeded {total} doc chunks from {len(files)} files.")


if __name__ == "__main__":
    asyncio.run(seed())
