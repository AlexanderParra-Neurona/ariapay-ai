from functools import lru_cache

from app.config import settings
from app.services.llm.base import LLMService
from app.services.llm.ollama import OllamaService


@lru_cache
def get_llm_service() -> LLMService:
    match settings.LLM_PROVIDER:
        case "ollama":
            return OllamaService()
        case _:
            raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}")
