from typing import Annotated

from custodia import trace_tool_call
from langchain_core.tools import BaseTool, tool

from app.constants import CURRENCY_PREFIX, MSG_NO_TRANSACTIONS_FOUND, TraceName
from app.services.classification import get_transaction_scope_classifier
from app.services.formatting import format_transaction_bullets
from app.services.retrieval import get_hybrid_retriever

_NAME = TraceName.TOOL_SEARCH_TRANSACTIONS.value
_DESCRIPTION = (
    "Search the signed-in user's own transaction history and spending. Use for "
    "questions about their balance, past purchases, or spending by category."
)


@trace_tool_call(name=_NAME, description=_DESCRIPTION)
def _run(query: str) -> str:
    scope = get_transaction_scope_classifier().classify(query)
    docs = get_hybrid_retriever().search_transactions(query, scope=scope)
    if scope is not None and scope.category is not None:
        docs = [d for d in docs if d.metadata.get("category") == scope.category]
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
) -> str:
    return _run(query)


def build_search_transactions_tool() -> BaseTool:
    return search_transactions
