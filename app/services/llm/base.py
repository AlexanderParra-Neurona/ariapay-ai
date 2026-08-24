from abc import ABC, abstractmethod


class LLMService(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str: ...
