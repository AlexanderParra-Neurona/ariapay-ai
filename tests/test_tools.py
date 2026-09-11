import asyncio

from langchain_core.documents import Document

from app.services.ariapay_service import AriapayAPIError, AriapayAuthError
from app.services.classification.types import TransactionScope
from app.tools import get_tools
from app.tools.get_account import build_get_account_tool
from app.tools.search_faq import build_search_faq_tool
from app.tools.search_transactions import build_search_transactions_tool


class StubHybridRetriever:
    def __init__(self, docs: list[Document] | None = None) -> None:
        self._docs = docs or []

    def search(self, query: str, top_k: int | None = None):
        return [(d, 1.0) for d in self._docs]

    def search_transactions(self, query: str, scope=None, top_k: int | None = None):
        return self._docs


class StubTransactionScopeClassifier:
    def __init__(self, scope: TransactionScope) -> None:
        self._scope = scope

    def classify(self, question: str) -> TransactionScope:
        return self._scope


def test_search_faq_tool_returns_doc_content(monkeypatch) -> None:
    doc = Document(
        page_content="Top up via bank transfer.",
        metadata={"source": "faq.md", "heading": "Top up"},
    )
    monkeypatch.setattr(
        "app.tools.search_faq.get_hybrid_retriever",
        lambda: StubHybridRetriever([doc]),
    )
    tool = build_search_faq_tool()

    output = asyncio.run(tool.run(query="how do I top up?"))
    assert "Top up via bank transfer." in output
    assert "faq.md" in output


def test_search_faq_tool_no_hits_returns_fallback_message(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.tools.search_faq.get_hybrid_retriever", lambda: StubHybridRetriever([])
    )
    tool = build_search_faq_tool()

    output = asyncio.run(tool.run(query="anything"))
    assert output == "Sorry, I don't have information on that."


def test_search_transactions_tool_summarizes_spend(monkeypatch) -> None:
    docs = [
        Document(
            page_content="",
            metadata={
                "merchant_name": "Warkop",
                "category": "food_and_beverage",
                "price": 25000.0,
                "timestamp": "2026-01-01T10:00:00Z",
            },
        ),
    ]
    monkeypatch.setattr(
        "app.tools.search_transactions.get_hybrid_retriever",
        lambda: StubHybridRetriever(docs),
    )
    monkeypatch.setattr(
        "app.tools.search_transactions.get_transaction_scope_classifier",
        lambda: StubTransactionScopeClassifier(
            TransactionScope(wants_all=True, category=None)
        ),
    )
    tool = build_search_transactions_tool()

    output = asyncio.run(tool.run(query="how much did I spend on food?"))
    assert "Rp25,000" in output
    assert "Warkop" in output


def test_search_transactions_tool_no_hits_returns_fallback_message(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.tools.search_transactions.get_hybrid_retriever",
        lambda: StubHybridRetriever([]),
    )
    monkeypatch.setattr(
        "app.tools.search_transactions.get_transaction_scope_classifier",
        lambda: StubTransactionScopeClassifier(
            TransactionScope(wants_all=False, category=None)
        ),
    )
    tool = build_search_transactions_tool()

    output = asyncio.run(tool.run(query="anything"))
    assert output == "I couldn't find any transactions matching that."


def test_get_account_tool_formats_user(monkeypatch) -> None:
    async def fake_get_me(access_token: str) -> dict:
        assert access_token == "tok-123"
        return {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "country_code": "+62",
            "phone_number": "8123456789",
            "cards": [{"card_network": "Visa", "number": "1111", "card_type": "debit"}],
        }

    monkeypatch.setattr("app.tools.get_account.get_me", fake_get_me)
    tool = build_get_account_tool("tok-123")

    output = asyncio.run(tool.run())
    assert "Ada Lovelace" in output
    assert "ada@example.com" in output
    assert "Visa 1111 (debit)" in output


def test_get_account_tool_session_expired(monkeypatch) -> None:
    async def fake_get_me(access_token: str) -> dict:
        raise AriapayAuthError("expired")

    monkeypatch.setattr("app.tools.get_account.get_me", fake_get_me)
    tool = build_get_account_tool("tok-123")

    output = asyncio.run(tool.run())
    assert output == "Your session has expired. Please sign in again."


def test_get_account_tool_api_error(monkeypatch) -> None:
    async def fake_get_me(access_token: str) -> dict:
        raise AriapayAPIError("boom")

    monkeypatch.setattr("app.tools.get_account.get_me", fake_get_me)
    tool = build_get_account_tool("tok-123")

    output = asyncio.run(tool.run())
    assert output == "Sorry, I couldn't fetch your account details right now."


def test_get_tools_omits_authenticated_tools_without_token() -> None:
    tools = get_tools()
    assert [t.name for t in tools] == ["search_faq"]


def test_get_tools_includes_authenticated_tools_with_token() -> None:
    tools = get_tools(access_token="tok-123")
    assert [t.name for t in tools] == [
        "search_faq",
        "search_transactions",
        "get_account",
    ]
