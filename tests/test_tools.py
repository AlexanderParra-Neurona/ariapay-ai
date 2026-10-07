import asyncio

import httpx
import pytest
from langchain_core.documents import Document

from app.services.ariapay_service import AriapayAPIError, AriapayAuthError
from app.services.ariapay_transactions_service import (
    AriapayReadOnlyViolation,
    _reject_non_get,
)
from app.tools import get_tools
from app.tools.get_account import build_get_account_tool
from app.tools.get_spending_summary import build_get_spending_summary_tool
from app.tools.list_transactions import build_list_transactions_tool
from app.tools.search_faq import build_search_faq_tool

_CONFIG = {"configurable": {"access_token": "tok-123"}}


class StubHybridRetriever:
    def __init__(self, docs: list[Document] | None = None) -> None:
        self._docs = docs or []

    def search(self, query: str, top_k: int | None = None):
        return [(d, 1.0) for d in self._docs]


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

    output = asyncio.run(tool.ainvoke({"query": "how do I top up?"}))
    assert "Top up via bank transfer." in output
    assert "faq.md" in output


def test_search_faq_tool_no_hits_returns_fallback_message(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.tools.search_faq.get_hybrid_retriever", lambda: StubHybridRetriever([])
    )
    tool = build_search_faq_tool()

    output = asyncio.run(tool.ainvoke({"query": "anything"}))
    assert output == "Sorry, I don't have information on that."


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
    tool = build_get_account_tool()

    output = asyncio.run(
        tool.ainvoke({}, config={"configurable": {"access_token": "tok-123"}})
    )
    assert "Ada Lovelace" in output
    assert "ada@example.com" in output
    assert "Visa 1111 (debit)" in output


def test_get_account_tool_session_expired(monkeypatch) -> None:
    async def fake_get_me(access_token: str) -> dict:
        raise AriapayAuthError("expired")

    monkeypatch.setattr("app.tools.get_account.get_me", fake_get_me)
    tool = build_get_account_tool()

    output = asyncio.run(
        tool.ainvoke({}, config={"configurable": {"access_token": "tok-123"}})
    )
    assert output == "Your session has expired. Please sign in again."


def test_get_account_tool_api_error(monkeypatch) -> None:
    async def fake_get_me(access_token: str) -> dict:
        raise AriapayAPIError("boom")

    monkeypatch.setattr("app.tools.get_account.get_me", fake_get_me)
    tool = build_get_account_tool()

    output = asyncio.run(
        tool.ainvoke({}, config={"configurable": {"access_token": "tok-123"}})
    )
    assert output == "Sorry, I couldn't fetch your account details right now."


def test_get_tools_omits_authenticated_tools_without_token() -> None:
    tools = get_tools(signed_in=False)
    assert [t.name for t in tools] == ["search_faq"]


def test_transactions_client_blocks_non_get() -> None:
    request = httpx.Request("POST", "https://example.test/api/v1/payments/qris")
    with pytest.raises(AriapayReadOnlyViolation):
        asyncio.run(_reject_non_get(request))


def test_transactions_client_allows_get() -> None:
    request = httpx.Request("GET", "https://example.test/api/v1/transactions")
    asyncio.run(_reject_non_get(request))


def test_list_transactions_tool_formats_page(monkeypatch) -> None:
    async def fake_resolve(access_token: str, name: str) -> int:
        assert name == "Food & Beverage"
        return 1

    async def fake_fetch(access_token: str, **kwargs) -> dict:
        assert access_token == "tok-123"
        assert kwargs["category_id"] == 1
        assert (kwargs["date_from"], kwargs["date_to"]) == ("2026-09-01", "2026-09-30")
        return {
            "transactions": [
                {
                    "date": "2026-09-24",
                    "total": "50000",
                    "items": [
                        {
                            "merchant_name": "WARUNG BU SITI",
                            "amount": "50000",
                            "category_name": "Food & Beverage",
                            "status": "SUCCESS",
                            "failure_reason": None,
                        }
                    ],
                }
            ],
            "pagination": {
                "page_no": 1,
                "page_size": 20,
                "total_items": 1,
                "total_pages": 1,
            },
        }

    monkeypatch.setattr("app.tools.list_transactions.resolve_category_id", fake_resolve)
    monkeypatch.setattr("app.tools.list_transactions.fetch_transactions", fake_fetch)
    tool = build_list_transactions_tool()

    output = asyncio.run(
        tool.ainvoke(
            {"category": "Food & Beverage", "month": "2026-09"}, config=_CONFIG
        )
    )
    assert "WARUNG BU SITI - Rp50,000 - Food & Beverage - SUCCESS" in output


def test_list_transactions_tool_empty(monkeypatch) -> None:
    async def fake_fetch(access_token: str, **kwargs) -> dict:
        return {"transactions": [], "pagination": {"total_items": 0}}

    monkeypatch.setattr("app.tools.list_transactions.fetch_transactions", fake_fetch)
    output = asyncio.run(build_list_transactions_tool().ainvoke({}, config=_CONFIG))
    assert output == "I couldn't find any transactions matching that."


def test_list_transactions_tool_session_expired(monkeypatch) -> None:
    async def fake_fetch(access_token: str, **kwargs) -> dict:
        raise AriapayAuthError("expired")

    monkeypatch.setattr("app.tools.list_transactions.fetch_transactions", fake_fetch)
    output = asyncio.run(build_list_transactions_tool().ainvoke({}, config=_CONFIG))
    assert output == "Your session has expired. Please sign in again."


def test_get_spending_summary_tool_formats_expenses(monkeypatch) -> None:
    async def fake_get_expenses(access_token: str, **kwargs) -> list[dict]:
        assert kwargs["month"] == "2026-10"
        return [
            {
                "period": {"from": "2026-10-01", "to": "2026-10-31"},
                "categories": [
                    {
                        "category_id": 1,
                        "category_name": "Food & Beverage",
                        "total": "50000",
                        "transaction_count": 1,
                    },
                    {
                        "category_id": 3,
                        "category_name": "Transportation",
                        "total": "18000",
                        "transaction_count": 1,
                    },
                ],
            }
        ]

    monkeypatch.setattr(
        "app.tools.get_spending_summary.get_expenses", fake_get_expenses
    )
    output = asyncio.run(
        build_get_spending_summary_tool().ainvoke({"month": "2026-10"}, config=_CONFIG)
    )
    assert "Rp68,000 total" in output
    assert "Food & Beverage: Rp50,000 across 1 transaction(s)" in output


def test_get_spending_summary_rejects_month_and_range() -> None:
    output = asyncio.run(
        build_get_spending_summary_tool().ainvoke(
            {"month": "2026-10", "date_from": "2026-10-01", "date_to": "2026-10-05"},
            config=_CONFIG,
        )
    )
    assert output == "Use either month or date_from/date_to, not both."


def test_get_tools_includes_authenticated_tools_with_token() -> None:
    tools = get_tools(signed_in=True)
    assert [t.name for t in tools] == [
        "search_faq",
        "list_transactions",
        "get_spending_summary",
        "get_account",
    ]
