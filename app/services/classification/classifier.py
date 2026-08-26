import logging
import re

from app.services.classification.types import QueryCategory
from app.services.llm.base import LLMService

logger = logging.getLogger("ariabot.classification")

_SYSTEM_PROMPT = """You are a query classifier for Ariapay, a payments app assistant.
Classify the user's message into exactly one category:

- general_faq: general questions, how-to, product info, education about Ariapay features (not tied to the user's own account data).
- account_profile: questions about the user's own identity, cards on file, or profile details (e.g. "what cards do I have", "what's my email").
- transaction_history: questions about the user's own spending, balance, or past transactions (e.g. "how much did I spend on food", "show my recent transactions").
- out_of_scope: anything else - payment requests/instructions to move money, unrelated topics, or requests the assistant should not act on.

Respond with only the category label, nothing else. Valid labels: general_faq, account_profile, transaction_history, out_of_scope."""

_LABEL_PATTERN = re.compile(
    r"general_faq|account_profile|transaction_history|out_of_scope"
)


class QueryClassifier:
    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    def classify(self, question: str) -> QueryCategory:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        raw = self._llm_service.chat(messages)
        category = self._parse(raw)
        logger.info(
            "classify question=%r raw=%r category=%s", question, raw, category.value
        )
        return category

    @staticmethod
    def _parse(raw: str) -> QueryCategory:
        match = _LABEL_PATTERN.search(raw.strip().lower())
        if not match:
            logger.warning(
                "classify_unparseable raw=%r fallback=%s",
                raw,
                QueryCategory.OUT_OF_SCOPE.value,
            )
            return QueryCategory.OUT_OF_SCOPE
        return QueryCategory(match.group(0))
