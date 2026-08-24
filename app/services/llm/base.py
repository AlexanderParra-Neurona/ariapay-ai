from abc import ABC, abstractmethod


class LLMService(ABC):
    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]]) -> str: ...
