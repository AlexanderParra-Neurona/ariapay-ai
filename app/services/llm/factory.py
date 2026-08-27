from functools import lru_cache

from app.config import settings
from app.services.llm.base import LLMService
from app.services.llm.litellm_service import LiteLLMService


@lru_cache
def get_llm_service() -> LLMService:
    match settings.LLM_PROVIDER:
        case "ollama" | "deepinfra":
            return LiteLLMService()
        case _:
            raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}")
