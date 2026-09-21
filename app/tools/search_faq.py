from typing import Annotated

from langchain_core.tools import tool

from app.constants import MSG_NO_DOCS_FOUND, TraceName
from app.services.retrieval import get_hybrid_retriever
from app.tracing import trace_tool_call

_NAME = TraceName.TOOL_SEARCH_FAQ.value
_DESCRIPTION = (
    "Search Ariapay's FAQ and product documentation for general questions about "
    "the app, its features, policies, or how-to guidance. Not for the user's own "
    "account or transaction data."
)


@tool(_NAME, description=_DESCRIPTION)
@trace_tool_call(name=_NAME, description=_DESCRIPTION)
def search_faq(
    query: Annotated[str, "The user's question, in their own words."],
) -> str:
    hits = get_hybrid_retriever().search(query)
    if not hits:
        return MSG_NO_DOCS_FOUND

    blocks = [
        f"[{doc.metadata.get('source', '')} - {doc.metadata.get('heading', '')}]\n"
        f"{doc.page_content}"
        for doc, _ in hits
    ]
    return "\n\n".join(blocks)


def build_search_faq_tool():
    return search_faq
