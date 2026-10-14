from langchain_core.tools import BaseTool

from app.tools.get_account import build_get_account_tool
from app.tools.get_spending_summary import build_get_spending_summary_tool
from app.tools.list_transactions import build_list_transactions_tool
from app.tools.search_faq import build_search_faq_tool


def get_tools(signed_in: bool) -> list[BaseTool]:
    """Build the set of tools available for one chat request.

    Tools that require a signed-in user (list_transactions,
    get_spending_summary, get_account) are omitted when `signed_in` is False,
    rather than exposed with no way to authenticate. The actual access token is
    threaded in per-invocation via `RunnableConfig`, not baked into the tool
    closure, so the tool set itself is token-agnostic and safe to build once
    per (signed_in) value.
    """
    tools = [build_search_faq_tool()]
    if signed_in:
        tools.append(build_list_transactions_tool())
        tools.append(build_get_spending_summary_tool())
        tools.append(build_get_account_tool())
    return tools
