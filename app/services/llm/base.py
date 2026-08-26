from abc import ABC, abstractmethod
from typing import Any


class LLMService(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str: ...


class LangchainLLMService(LLMService):
    """Base for providers backed by a langchain embeddings + chat model pair."""

    _embeddings: Any
    _chat: Any

    def embed(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    def chat(self, messages: list[dict[str, str]]) -> str:
        resp = self._chat.invoke(messages)
        return resp.content
