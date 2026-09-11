from datetime import datetime

from custodia import trace_tool_call
from langchain_core.documents import Document

from app.constants import (
    CURRENCY_PREFIX,
    MSG_NO_TRANSACTIONS_FOUND,
    TIMESTAMP_DISPLAY_FORMAT,
    TraceName,
)
from app.services.classification import get_transaction_scope_classifier
from app.services.retrieval import get_hybrid_retriever
from app.tools.base import Tool

_NAME = TraceName.TOOL_SEARCH_TRANSACTIONS.value
_DESCRIPTION = (
    "Search the signed-in user's own transaction history and spending. Use for "
    "questions about their balance, past purchases, or spending by category."
)
_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The user's question about their transactions, in their own words.",
        }
    },
    "required": ["query"],
}


def _format_timestamp(timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return timestamp
    return dt.strftime(TIMESTAMP_DISPLAY_FORMAT)


def _transaction_bullets(docs: list[Document]) -> str:
    lines = [
        "- {merchant} - {currency}{price:,.0f} on {timestamp}".format(
            merchant=d.metadata.get("merchant_name", "Unknown"),
            currency=CURRENCY_PREFIX,
            price=d.metadata.get("price", 0.0),
            timestamp=_format_timestamp(d.metadata.get("timestamp", "")),
        )
        for d in docs
    ]
    return "\n".join(lines)


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
    return f"{summary}\n\n{_transaction_bullets(docs)}"


async def _run_async(query: str) -> str:
    return _run(query)


def build_search_transactions_tool() -> Tool:
    return Tool(
        name=_NAME, description=_DESCRIPTION, parameters=_PARAMETERS, run=_run_async
    )
