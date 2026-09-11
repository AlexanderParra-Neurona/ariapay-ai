import instructor
import litellm
from ragas.embeddings import LiteLLMEmbeddings
from ragas.llms import LiteLLMStructuredLLM
from ragas.metrics.collections import (
    AnswerCorrectness,
    AnswerRelevancy,
    ContextPrecisionWithoutReference,
    ContextRecall,
    Faithfulness,
    SemanticSimilarity,
)
from ragas.metrics.collections.base import BaseMetric

from app.config import settings
from app.constants import DEEPINFRA_OPENAI_BASE, LLMProvider, OPENAI_MODEL_PREFIX


def _require_deepinfra_token() -> str:
    token = settings.DEEPINFRA_API_TOKEN
    if not token or token == "changeme":
        raise RuntimeError(
            "DEEPINFRA_API_TOKEN is not set. The RAG eval judge runs headlessly "
            "against DeepInfra (not local Ollama) so it works in CI - set "
            "DEEPINFRA_API_TOKEN before running `pytest -m eval`."
        )
    return token


def get_judge_llm() -> LiteLLMStructuredLLM:
    api_key = _require_deepinfra_token()
    judge_client = instructor.from_litellm(litellm.acompletion, mode=instructor.Mode.JSON)
    return LiteLLMStructuredLLM(
        client=judge_client,
        model=f"{LLMProvider.DEEPINFRA.value}/{settings.DEEPINFRA_CHAT_MODEL}",
        provider=LLMProvider.DEEPINFRA.value,
        api_base=None,
        api_key=api_key,
    )


def get_judge_embeddings() -> LiteLLMEmbeddings:
    api_key = _require_deepinfra_token()
    return LiteLLMEmbeddings(
        model=f"{OPENAI_MODEL_PREFIX}{settings.DEEPINFRA_EMBED_MODEL}",
        api_base=DEEPINFRA_OPENAI_BASE,
        api_key=api_key,
    )


def get_ragas_metrics() -> list[BaseMetric]:
    judge_llm = get_judge_llm()
    judge_embeddings = get_judge_embeddings()
    return [
        ContextPrecisionWithoutReference(llm=judge_llm),
        ContextRecall(llm=judge_llm),
        Faithfulness(llm=judge_llm),
        AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings),
        AnswerCorrectness(llm=judge_llm, embeddings=judge_embeddings),
        SemanticSimilarity(embeddings=judge_embeddings),
    ]
