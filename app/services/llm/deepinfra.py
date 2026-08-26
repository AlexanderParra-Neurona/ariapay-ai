from langchain_community.chat_models import ChatDeepInfra
from langchain_community.embeddings import DeepInfraEmbeddings

from app.config import settings
from app.services.llm.base import LLMService


class DeepInfraService(LLMService):
    def __init__(self) -> None:
        self._embeddings = DeepInfraEmbeddings(
            model_id=settings.DEEPINFRA_EMBED_MODEL,
            deepinfra_api_token=settings.DEEPINFRA_API_TOKEN,
            query_instruction="",
            embed_instruction="",
        )
        self._chat = ChatDeepInfra(
            model=settings.DEEPINFRA_CHAT_MODEL,
            deepinfra_api_token=settings.DEEPINFRA_API_TOKEN,
        )

    def embed(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    def chat(self, messages: list[dict[str, str]]) -> str:
        resp = self._chat.invoke(messages)
        return resp.content
