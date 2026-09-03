from abc import ABC, abstractmethod
from typing import Any


class LLMService(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def chat(
        self, messages: list[dict[str, str]], metadata: dict[str, Any] | None = None
    ) -> str: ...
