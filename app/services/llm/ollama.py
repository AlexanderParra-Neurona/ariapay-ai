from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.config import settings
from app.services.llm.base import LLMService


class OllamaService(LLMService):
    def __init__(self) -> None:
        self._embeddings = OllamaEmbeddings(model=settings.OLLAMA_EMBED_MODEL, base_url=settings.OLLAMA_URL)
        self._chat = ChatOllama(
            model=settings.OLLAMA_CHAT_MODEL, base_url=settings.OLLAMA_URL, client_kwargs={"timeout": 120}
        )

    def embed(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    def chat(self, messages: list[dict[str, str]]) -> str:
        resp = self._chat.invoke(messages)
        return resp.content
