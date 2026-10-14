import asyncio

import httpx
import pytest

from app.services import ariapay_transactions_service, docura_service
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError
from app.services.ariapay_transactions_service import (
    AriapayNotFoundError,
    AriapayReadOnlyViolation,
    _reject_non_get,
)
from app.services.docura_service import DocuraAPIError
from app.services.formatting import format_transaction_page
from app.tools import get_tools
from app.tools.get_account import build_get_account_tool
from app.tools.get_spending_summary import build_get_spending_summary_tool
from app.tools.list_transactions import build_list_transactions_tool
from app.tools.search_faq import build_search_faq_tool

_CONFIG = {"configurable": {"access_token": "tok-123"}}


def _patch_docura_transport(monkeypatch, handler) -> None:
    """Route docura_service's httpx.AsyncClient through a MockTransport."""
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        docura_service.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    monkeypatch.setattr(
        docura_service.settings, "DOCURA_API_URL", "http://docura:8000/"
    )


def test_search_faq_tool_returns_answer_with_sources(monkeypatch) -> None:
    async def fake_query(question: str) -> dict:
        assert question == "how do I top up?"
        return {"answer": "Top up via bank transfer.", "sources": ["faq.md"]}

    monkeypatch.setattr("app.tools.search_faq.docura_query", fake_query)
    tool = build_search_faq_tool()

    output = asyncio.run(tool.ainvoke({"query": "how do I top up?"}))
    assert "Top up via bank transfer." in output
    assert "faq.md" in output


def test_search_faq_tool_empty_answer_returns_fallback_message(monkeypatch) -> None:
    async def fake_query(question: str) -> dict:
        return {"answer": "", "sources": []}

    monkeypatch.setattr("app.tools.search_faq.docura_query", fake_query)
    tool = build_search_faq_tool()

    output = asyncio.run(tool.ainvoke({"query": "anything"}))
    assert output == "Sorry, I don't have information on that."


def test_search_faq_tool_docura_error_returns_fallback_message(monkeypatch) -> None:
    async def fake_query(question: str) -> dict:
        raise DocuraAPIError("Docura API timed out")

    monkeypatch.setattr("app.tools.search_faq.docura_query", fake_query)
    tool = build_search_faq_tool()

    output = asyncio.run(tool.ainvoke({"query": "anything"}))
    assert output == "Sorry, I don't have information on that."


def test_docura_query_sends_api_key(monkeypatch) -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["key"] = request.headers.get("X-API-Key")
        return httpx.Response(200, json={"answer": "ok", "sources": []})

    _patch_docura_transport(monkeypatch, handler)
    monkeypatch.setattr(docura_service.settings, "DOCURA_API_KEY", "secret")

    result = asyncio.run(docura_service.query("hi"))
    assert result == {"answer": "ok", "sources": []}
    assert seen == {"url": "http://docura:8000/v1/query", "key": "secret"}


def test_docura_query_omits_api_key_when_unset(monkeypatch) -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["has_key"] = "X-API-Key" in request.headers
        return httpx.Response(200, json={"answer": "ok", "sources": []})

    _patch_docura_transport(monkeypatch, handler)
    monkeypatch.setattr(docura_service.settings, "DOCURA_API_KEY", None)

    asyncio.run(docura_service.query("hi"))
    assert seen == {"has_key": False}


@pytest.mark.parametrize(
    "handler",
    [
        lambda request: httpx.Response(
            401, json={"detail": "Invalid or missing API key"}
        ),
        lambda request: httpx.Response(
            502, json={"detail": "Could not generate answer"}
        ),
        lambda request: httpx.Response(200, text="not json"),
    ],
    ids=["unauthorized", "bad-gateway", "invalid-json"],
)
def test_docura_query_bad_response_raises_docura_error(monkeypatch, handler) -> None:
    _patch_docura_transport(monkeypatch, handler)

    with pytest.raises(DocuraAPIError):
        asyncio.run(docura_service.query("hi"))


@pytest.mark.parametrize(
    "exc",
    [httpx.ReadTimeout("timed out"), httpx.ConnectError("connection refused")],
    ids=["timeout", "connect-error"],
)
def test_docura_query_transport_error_raises_docura_error(monkeypatch, exc) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    _patch_docura_transport(monkeypatch, handler)

    with pytest.raises(DocuraAPIError):
        asyncio.run(docura_service.query("hi"))


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


def _patch_ariapay_transport(monkeypatch, handler) -> None:
    """Route ariapay_transactions_service's httpx.AsyncClient through a MockTransport."""
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        ariapay_transactions_service.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )
    monkeypatch.setattr(
        ariapay_transactions_service.settings,
        "ARIAPAY_PAYMENT_API_URL",
        "https://ariapay.test/payment",
    )


def test_list_transactions_uses_payment_api_url(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payment/api/v1/transactions"
        return httpx.Response(200, json={"transactions": []})

    _patch_ariapay_transport(monkeypatch, handler)
    asyncio.run(ariapay_transactions_service.list_transactions("tok-123"))


def test_list_transactions_router_404_raises_api_error(monkeypatch) -> None:
    _patch_ariapay_transport(
        monkeypatch, lambda request: httpx.Response(404, text="404 page not found")
    )
    with pytest.raises(AriapayAPIError) as exc_info:
        asyncio.run(ariapay_transactions_service.list_transactions("tok-123"))
    assert not isinstance(exc_info.value, AriapayNotFoundError)


def test_list_transactions_json_404_raises_not_found(monkeypatch) -> None:
    _patch_ariapay_transport(
        monkeypatch,
        lambda request: httpx.Response(
            404, json={"err_code": "EC0404", "error_message": "category not found"}
        ),
    )
    with pytest.raises(AriapayNotFoundError, match="category not found"):
        asyncio.run(ariapay_transactions_service.list_transactions("tok-123"))


def test_list_transactions_tool_router_404_reports_fetch_failure(monkeypatch) -> None:
    _patch_ariapay_transport(
        monkeypatch, lambda request: httpx.Response(404, text="404 page not found")
    )
    output = asyncio.run(build_list_transactions_tool().ainvoke({}, config=_CONFIG))
    assert output == "Sorry, I couldn't fetch your transactions right now."


def test_get_expenses_reads_categories(monkeypatch) -> None:
    categories = [{"category_id": 1, "category_name": "Food & Beverage", "total": "1"}]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payment/api/v1/expenses"
        assert request.url.params["month"] == "2026-10"
        return httpx.Response(200, json={"categories": categories})

    _patch_ariapay_transport(monkeypatch, handler)
    result = asyncio.run(
        ariapay_transactions_service.get_expenses("tok-123", month="2026-10")
    )
    assert result == categories


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


def test_format_transaction_page_names_largest_successful_item() -> None:
    def item(merchant: str, amount: str, status: str = "SUCCESS") -> dict:
        return {"merchant_name": merchant, "amount": amount, "status": status}

    output = format_transaction_page(
        {
            "transactions": [
                {
                    "date": "2026-10-12",
                    "total": "10069",
                    "items": [item("LYNKID", "10069")],
                },
                {
                    "date": "2026-10-08",
                    "total": "43258",
                    "items": [item("PT Tokopedia", "43258")],
                },
                {
                    "date": "2026-10-07",
                    "total": "92000",
                    "items": [
                        item("JESSILINE IMANUELA", "50000"),
                        item("WARUNG MBAK YULI", "22000"),
                        item("FAILED MERCHANT", "900000", status="FAILED"),
                    ],
                },
            ]
        }
    )
    assert output.endswith(
        "Largest successful transaction shown: JESSILINE IMANUELA - Rp50,000 on 2026-10-07"
    )


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
        period = {"from": "2026-10-01", "to": "2026-10-31"}
        return [
            {
                "category_id": 1,
                "category_name": "Food & Beverage",
                "period": period,
                "total": "50000",
            },
            {
                "category_id": 3,
                "category_name": "Transportation",
                "period": period,
                "total": "18000",
            },
        ]

    monkeypatch.setattr(
        "app.tools.get_spending_summary.get_expenses", fake_get_expenses
    )
    output = asyncio.run(
        build_get_spending_summary_tool().ainvoke({"month": "2026-10"}, config=_CONFIG)
    )
    assert "Rp68,000 total" in output
    assert "Spending from 2026-10-01 to 2026-10-31" in output
    assert "- Food & Beverage: Rp50,000" in output


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
