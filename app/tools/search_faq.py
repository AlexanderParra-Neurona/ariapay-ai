from typing import Annotated

from custodia import trace_tool_call_async
from langchain_core.tools import tool

from app.constants import MSG_NO_DOCS_FOUND, TraceName
from app.services.docura_service import DocuraAPIError
from app.services.docura_service import query as docura_query

_NAME = TraceName.TOOL_SEARCH_FAQ.value
_DESCRIPTION = (
    "Search Ariapay's FAQ and product documentation for general questions about "
    "the app, its features, policies, or how-to guidance. Not for the user's own "
    "account or transaction data."
)


@tool(_NAME, description=_DESCRIPTION)
@trace_tool_call_async(name=_NAME, description=_DESCRIPTION)
async def search_faq(
    query: Annotated[str, "The user's question, in their own words."],
) -> str:
    try:
        result = await docura_query(query)
    except DocuraAPIError:
        return MSG_NO_DOCS_FOUND

    answer = result.get("answer", "")
    if not answer:
        return MSG_NO_DOCS_FOUND

    sources = result.get("sources", "")
    if sources:
        return f"{answer}\n\n(Sources: {', '.join(sources)})"
    return answer


def build_search_faq_tool():
    return search_faq
