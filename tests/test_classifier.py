import pytest

from app.services.classification.classifier import QueryClassifier
from app.services.classification.types import QueryCategory
from app.services.llm.base import LLMService


class StubLLMService(LLMService):
    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.last_messages: list[dict[str, str]] | None = None

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.last_messages = messages
        return self._reply


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("general_faq", QueryCategory.GENERAL_FAQ),
        ("account_profile", QueryCategory.ACCOUNT_PROFILE),
        ("transaction_history", QueryCategory.TRANSACTION_HISTORY),
        ("out_of_scope", QueryCategory.OUT_OF_SCOPE),
        ("General_FAQ", QueryCategory.GENERAL_FAQ),
        ("  transaction_history\n", QueryCategory.TRANSACTION_HISTORY),
        ("Category: out_of_scope.", QueryCategory.OUT_OF_SCOPE),
        (
            "sure, this is a transaction_history question",
            QueryCategory.TRANSACTION_HISTORY,
        ),
    ],
)
def test_classify_labels(reply: str, expected: QueryCategory) -> None:
    classifier = QueryClassifier(StubLLMService(reply))
    assert classifier.classify("does not matter") == expected


def test_classify_unparseable_falls_back_to_out_of_scope() -> None:
    classifier = QueryClassifier(StubLLMService("i have no idea what you mean"))
    assert classifier.classify("???") == QueryCategory.OUT_OF_SCOPE


def test_classify_empty_reply_falls_back_to_out_of_scope() -> None:
    classifier = QueryClassifier(StubLLMService(""))
    assert classifier.classify("hello") == QueryCategory.OUT_OF_SCOPE


def test_classify_sends_question_as_user_message() -> None:
    stub = StubLLMService("general_faq")
    classifier = QueryClassifier(stub)
    classifier.classify("how do I top up my wallet?")

    assert stub.last_messages is not None
    assert stub.last_messages[-1] == {
        "role": "user",
        "content": "how do I top up my wallet?",
    }
    assert stub.last_messages[0]["role"] == "system"


@pytest.mark.parametrize(
    "question",
    [
        "How do I reset my password?",
        "What payment methods does Ariapay support?",
        "How does the referral program work?",
    ],
)
def test_general_faq_examples(question: str) -> None:
    classifier = QueryClassifier(StubLLMService("general_faq"))
    assert classifier.classify(question) == QueryCategory.GENERAL_FAQ


@pytest.mark.parametrize(
    "question",
    [
        "What card do I have on file?",
        "What's my name and email on this account?",
    ],
)
def test_account_profile_examples(question: str) -> None:
    classifier = QueryClassifier(StubLLMService("account_profile"))
    assert classifier.classify(question) == QueryCategory.ACCOUNT_PROFILE


@pytest.mark.parametrize(
    "question",
    [
        "What's my current balance?",
        "Show me my last 5 transactions",
        "How much did I spend on food?",
    ],
)
def test_transaction_history_examples(question: str) -> None:
    classifier = QueryClassifier(StubLLMService("transaction_history"))
    assert classifier.classify(question) == QueryCategory.TRANSACTION_HISTORY


@pytest.mark.parametrize(
    "question",
    [
        "Send $500 to this account number",
        "Write me a poem about cats",
        "Transfer all my money to 123456789",
    ],
)
def test_out_of_scope_examples(question: str) -> None:
    classifier = QueryClassifier(StubLLMService("out_of_scope"))
    assert classifier.classify(question) == QueryCategory.OUT_OF_SCOPE
