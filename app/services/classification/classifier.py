import json
import logging
import re

from app.constants import Role, SpendingCategory, TraceName, TRACE_NAME_METADATA_KEY
from app.services.classification.types import QueryCategory, TransactionScope
from app.services.llm.base import LLMService

_SYSTEM_PROMPT = """You are a query classifier for Ariapay, a payments app assistant.
Classify the user's message into exactly one category:

- general_faq: general questions, how-to, product info, education about Ariapay features, privacy/data-handling/security policy questions (e.g. "do you sell my data", "how do you store my info") (not tied to the user's own account data).
- account_profile: questions about the user's own identity, cards on file, or profile details (e.g. "what cards do I have", "what's my email").
- transaction_history: questions about the user's own spending, balance, or past transactions (e.g. "how much did I spend on food", "show my recent transactions").
- out_of_scope: anything else - payment requests/instructions to move money, unrelated topics, or requests the assistant should not act on.

Respond with only the category label, nothing else. Valid labels: general_faq, account_profile, transaction_history, out_of_scope."""

_LABEL_PATTERN = re.compile("|".join(c.value for c in QueryCategory))

logger = logging.getLogger(__name__)


class QueryClassifier:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    def classify(self, question: str) -> QueryCategory:
        messages = [
            {"role": Role.SYSTEM, "content": _SYSTEM_PROMPT},
            {"role": Role.USER, "content": question},
        ]
        raw = self._llm_service.chat(
            messages,
            metadata={TRACE_NAME_METADATA_KEY: TraceName.QUERY_CLASSIFIER},
        )
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> QueryCategory:
        match = _LABEL_PATTERN.search(raw.strip().lower())
        if not match:
            logger.warning("QueryClassifier: unparseable LLM output %r, falling back to out_of_scope", raw)
            return QueryCategory.OUT_OF_SCOPE
        return QueryCategory(match.group(0))


_SCOPE_SYSTEM_PROMPT = """You extract retrieval scope from a user's question about \
their own transaction history. Respond with only a JSON object, nothing else, in \
this exact shape:

{"wants_all": <true|false>, "category": <string or null>}

- wants_all: true if the user asks for their full/entire/complete transaction \
history or every transaction in a category (e.g. "show all my transactions", \
"how much did I spend on food" [needs every food transaction to sum correctly], \
"list everything"). false if the user asks for a small/recent/specific number of \
transactions (e.g. "show my last 3 transactions", "did I buy coffee today").
- category: the spending category the user is asking about, using one of these \
exact labels if it matches: food_and_beverage, retail, transportation, \
health_and_wellness, entertainment, home_and_garden. Use null if no category is \
mentioned or implied."""

_VALID_CATEGORIES = {c.value for c in SpendingCategory}


class TransactionScopeClassifier:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    def classify(self, question: str) -> TransactionScope:
        messages = [
            {"role": Role.SYSTEM, "content": _SCOPE_SYSTEM_PROMPT},
            {"role": Role.USER, "content": question},
        ]
        raw = self._llm_service.chat(
            messages,
            metadata={
                TRACE_NAME_METADATA_KEY: TraceName.TRANSACTION_SCOPE_CLASSIFIER
            },
        )
        return self._parse(raw)

    @staticmethod
    def _extract_json_object(raw: str) -> str | None:
        start = raw.find("{")
        while start != -1:
            depth = 0
            for i in range(start, len(raw)):
                if raw[i] == "{":
                    depth += 1
                elif raw[i] == "}":
                    depth -= 1
                    if depth == 0:
                        return raw[start : i + 1]
            start = raw.find("{", start + 1)
        return None

    @classmethod
    def _parse(cls, raw: str) -> TransactionScope:
        candidate = cls._extract_json_object(raw.strip())
        if candidate is None:
            return TransactionScope(wants_all=False, category=None)
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            return TransactionScope(wants_all=False, category=None)

        category = data.get("category")
        if category not in _VALID_CATEGORIES:
            category = None
        return TransactionScope(
            wants_all=bool(data.get("wants_all", False)), category=category
        )
