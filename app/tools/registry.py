from langchain_core.tools import BaseTool

from app.tools.get_account import build_get_account_tool
from app.tools.search_faq import build_search_faq_tool
from app.tools.search_transactions import build_search_transactions_tool


def get_tools(signed_in: bool) -> list[BaseTool]:
    """Build the set of tools available for one chat request.

    Tools that require a signed-in user (get_account, search_transactions)
    are omitted when `signed_in` is False, rather than exposed with no way
    to authenticate. The actual access token is threaded in per-invocation
    via `RunnableConfig`, not baked into the tool closure, so the tool set
    itself is token-agnostic and safe to build once per (signed_in) value.
    """
    tools = [build_search_faq_tool()]
    if signed_in:
        tools.append(build_search_transactions_tool())
        tools.append(build_get_account_tool())
    return tools
