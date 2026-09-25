from functools import lru_cache

from app.services.classification.classifier import QueryClassifier
from app.services.llm import get_chat_model


@lru_cache
def get_query_classifier() -> QueryClassifier:
    return QueryClassifier(get_chat_model())
