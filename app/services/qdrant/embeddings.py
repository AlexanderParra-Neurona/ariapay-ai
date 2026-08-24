from langchain_core.embeddings import Embeddings

from app.services.llm import LLMService


class LLMServiceEmbeddings(Embeddings):
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._llm_service.embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._llm_service.embed(text)
