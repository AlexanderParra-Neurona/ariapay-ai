from app.tools.base import Tool
from app.tools.get_account import build_get_account_tool
from app.tools.search_faq import build_search_faq_tool
from app.tools.search_transactions import build_search_transactions_tool


def get_tools(access_token: str | None = None) -> list[Tool]:
    """Build the set of tools available for one chat request.

    `access_token` is the signed-in user's Ariapay token, if any. Tools that
    require a signed-in user (get_account, search_transactions) are omitted
    when absent, rather than exposed with no way to authenticate.
    """
    tools = [build_search_faq_tool()]
    if access_token:
        tools.append(build_search_transactions_tool())
        tools.append(build_get_account_tool(access_token))
    return tools
