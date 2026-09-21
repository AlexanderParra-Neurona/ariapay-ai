import re
from typing import Annotated, Literal

from langchain_core.tools import BaseTool, tool

from app.constants import (
    CURRENCY_PREFIX,
    MSG_NO_TRANSACTIONS_FOUND,
    SpendingCategory,
    TraceName,
)
from app.services.classification.types import TransactionScope
from app.services.formatting import format_transaction_bullets
from app.services.retrieval import get_hybrid_retriever
from app.tracing import trace_tool_call

_WANTS_ALL_PATTERN = re.compile(
    r"\b(all|every|entire|total|how much|how many|altogether|combined)\b",
    re.IGNORECASE,
)

_NAME = TraceName.TOOL_SEARCH_TRANSACTIONS.value
_DESCRIPTION = (
    "Search the signed-in user's own transaction history and spending. Use for "
    "questions about their balance, past purchases, or spending by category. "
    "Set wants_all=True whenever the answer requires summing or counting every "
    "matching transaction (e.g. total/average spend, 'how much', 'how many') - "
    "otherwise the total will silently be based on only a partial result set."
)

_SpendingCategoryLiteral = Literal[tuple(c.value for c in SpendingCategory)]


@trace_tool_call(name=_NAME, description=_DESCRIPTION)
def _run(query: str, wants_all: bool = False, category: str | None = None) -> str:
    if not wants_all and _WANTS_ALL_PATTERN.search(query):
        wants_all = True
    scope = TransactionScope(wants_all=wants_all, category=category)
    docs = get_hybrid_retriever().search_transactions(query, scope=scope)
    if not docs:
        return MSG_NO_TRANSACTIONS_FOUND

    total = sum(d.metadata.get("price", 0.0) for d in docs)
    summary = (
        f"You spent a total of {CURRENCY_PREFIX}{total:,.0f} "
        f"across {len(docs)} transaction(s)."
    )
    return f"{summary}\n\n{format_transaction_bullets(docs)}"


@tool(_NAME, description=_DESCRIPTION)
def search_transactions(
    query: Annotated[
        str, "The user's question about their transactions, in their own words."
    ],
    wants_all: Annotated[
        bool,
        "True if the user asks for their full/entire/complete transaction "
        "history or every transaction in a category (e.g. 'show all my "
        "transactions', 'how much did I spend on food' [needs every food "
        "transaction to sum correctly], 'list everything'). False if the user "
        "asks for a small/recent/specific number of transactions (e.g. 'show "
        "my last 3 transactions', 'did I buy coffee today').",
    ] = False,
    category: Annotated[
        _SpendingCategoryLiteral | None,
        "The spending category the user is asking about, if mentioned or "
        "implied. Omit if no category applies.",
    ] = None,
) -> str:
    return _run(query, wants_all=wants_all, category=category)


def build_search_transactions_tool() -> BaseTool:
    return search_transactions
