import os
from typing import Any

import litellm

from app.config import settings
from app.constants import DEEPINFRA_OPENAI_BASE, LLMProvider, OPENAI_MODEL_PREFIX
from app.services.llm.base import LLMService

if settings.LANGFUSE_ENABLED:
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
    os.environ.setdefault("LANGFUSE_HOST", settings.LANGFUSE_HOST)
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]


class LiteLLMService(LLMService):
    """Routes chat/embedding calls through LiteLLM.

    Chat uses LiteLLM's native "ollama/..." / "deepinfra/..." routing.
    LiteLLM's embedding() has no native DeepInfra route, so DeepInfra
    embeddings go through its OpenAI-compatible endpoint instead
    ("openai/<model>" + api_base override) - same provider, different
    LiteLLM entry point.
    """

    def __init__(self) -> None:
        self._chat_model = settings.CHAT_MODEL
        self._is_ollama = settings.LLM_PROVIDER == LLMProvider.OLLAMA

        if self._is_ollama:
            self._embed_model = settings.EMBED_MODEL
            self._embed_api_base = settings.OLLAMA_URL
            self._embed_api_key = None
        else:
            self._embed_model = f"{OPENAI_MODEL_PREFIX}{settings.DEEPINFRA_EMBED_MODEL}"
            self._embed_api_base = DEEPINFRA_OPENAI_BASE
            self._embed_api_key = settings.DEEPINFRA_API_TOKEN

        self._chat_api_base = settings.OLLAMA_URL if self._is_ollama else None
        self._chat_api_key = None if self._is_ollama else settings.DEEPINFRA_API_TOKEN

    def embed(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = litellm.embedding(
            model=self._embed_model,
            input=texts,
            api_base=self._embed_api_base,
            api_key=self._embed_api_key,
        )
        return [item["embedding"] for item in resp.data]

    def chat(
        self, messages: list[dict[str, str]], metadata: dict[str, Any] | None = None
    ) -> str:
        resp = litellm.completion(
            model=self._chat_model,
            messages=messages,
            api_base=self._chat_api_base,
            api_key=self._chat_api_key,
            metadata=metadata,
        )
        return resp.choices[0].message.content
