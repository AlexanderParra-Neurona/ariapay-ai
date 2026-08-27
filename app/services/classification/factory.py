from functools import lru_cache

from app.services.classification.classifier import (
    QueryClassifier,
    TransactionScopeClassifier,
)
from app.services.llm.factory import get_llm_service


@lru_cache
def get_query_classifier() -> QueryClassifier:
    return QueryClassifier(get_llm_service())


@lru_cache
def get_transaction_scope_classifier() -> TransactionScopeClassifier:
    return TransactionScopeClassifier(get_llm_service())
