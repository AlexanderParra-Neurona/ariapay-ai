import litellm

from app.config import settings
from app.constants import (
    DEEPINFRA_OPENAI_BASE,
    OPENAI_MODEL_PREFIX,
    LLMProvider,
    TraceName,
)
from app.services.llm.base import LLMService
from app.tracing import trace


class LiteLLMService(LLMService):
    """Routes embedding calls through LiteLLM.

    LiteLLM's embedding() has no native DeepInfra route, so DeepInfra
    embeddings go through its OpenAI-compatible endpoint instead
    ("openai/<model>" + api_base override) - same provider, different
    LiteLLM entry point.
    """

    def __init__(self) -> None:
        is_ollama = settings.LLM_PROVIDER == LLMProvider.OLLAMA

        if is_ollama:
            self._embed_model = settings.EMBED_MODEL
            self._embed_api_base = settings.OLLAMA_URL
            self._embed_api_key = None
        else:
            self._embed_model = f"{OPENAI_MODEL_PREFIX}{settings.DEEPINFRA_EMBED_MODEL}"
            self._embed_api_base = DEEPINFRA_OPENAI_BASE
            self._embed_api_key = settings.DEEPINFRA_API_TOKEN

    def embed(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    @trace(name=TraceName.LITELLM_EMBED.value)
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = litellm.embedding(
            model=self._embed_model,
            input=texts,
            api_base=self._embed_api_base,
            api_key=self._embed_api_key,
        )
        return [item["embedding"] for item in resp.data]
