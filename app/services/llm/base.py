from abc import ABC, abstractmethod


class LLMService(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
