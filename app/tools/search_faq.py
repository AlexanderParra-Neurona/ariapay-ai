from custodia import trace_tool_call

from app.constants import MSG_NO_DOCS_FOUND, TraceName
from app.services.retrieval import get_hybrid_retriever
from app.tools.base import Tool

_NAME = TraceName.TOOL_SEARCH_FAQ.value
_DESCRIPTION = (
    "Search Ariapay's FAQ and product documentation for general questions about "
    "the app, its features, policies, or how-to guidance. Not for the user's own "
    "account or transaction data."
)
_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The user's question, in their own words.",
        }
    },
    "required": ["query"],
}


@trace_tool_call(name=_NAME, description=_DESCRIPTION)
def _run(query: str) -> str:
    hits = get_hybrid_retriever().search(query)
    if not hits:
        return MSG_NO_DOCS_FOUND

    blocks = [
        f"[{doc.metadata.get('source', '')} - {doc.metadata.get('heading', '')}]\n"
        f"{doc.page_content}"
        for doc, _ in hits
    ]
    return "\n\n".join(blocks)


async def _run_async(query: str) -> str:
    return _run(query)


def build_search_faq_tool() -> Tool:
    return Tool(
        name=_NAME, description=_DESCRIPTION, parameters=_PARAMETERS, run=_run_async
    )
