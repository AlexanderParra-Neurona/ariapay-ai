import httpx

from app.config import settings
from app.services.llm.base import LLMService


class OllamaService(LLMService):
    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.OLLAMA_URL}/api/embed",
                json={"model": settings.EMBED_MODEL, "input": text},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["embeddings"][0]

    async def chat(self, messages: list[dict[str, str]]) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.OLLAMA_URL}/api/chat",
                json={"model": settings.CHAT_MODEL, "messages": messages, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]
