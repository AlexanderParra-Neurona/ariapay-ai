from functools import lru_cache

from langchain_litellm import ChatLiteLLM

from app.config import settings
from app.constants import CHAT_MAX_TOKENS, LLMProvider

_QWEN3_MODEL_KWARGS = {
    "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
}


@lru_cache
def get_chat_model() -> ChatLiteLLM:
    is_ollama = settings.LLM_PROVIDER == LLMProvider.OLLAMA
    model_kwargs = _QWEN3_MODEL_KWARGS if "Qwen3" in settings.CHAT_MODEL else {}

    return ChatLiteLLM(
        model=settings.CHAT_MODEL,
        api_base=settings.OLLAMA_URL if is_ollama else None,
        api_key=None if is_ollama else settings.DEEPINFRA_API_TOKEN,
        max_tokens=CHAT_MAX_TOKENS,
        model_kwargs=model_kwargs,
    )
