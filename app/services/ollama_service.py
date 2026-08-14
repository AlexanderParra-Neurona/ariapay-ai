import httpx

from app.config import settings


async def embed(text: str) -> list[float]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.OLLAMA_URL}/api/embed",
            json={"model": settings.EMBED_MODEL, "input": text},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]
