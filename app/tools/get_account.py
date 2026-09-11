from custodia import trace_tool_call_async

from app.constants import MSG_ACCOUNT_FETCH_FAILED, MSG_SESSION_EXPIRED, TraceName
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError, get_me
from app.tools.base import Tool

_NAME = TraceName.TOOL_GET_ACCOUNT.value
_DESCRIPTION = (
    "Get the signed-in user's own account profile: name, email, phone number, "
    "and cards on file. Use for questions about the user's identity or account "
    "details, not their transactions."
)
_PARAMETERS: dict = {"type": "object", "properties": {}}


def _format_account(user: dict) -> str:
    cards = user.get("cards") or []
    card_lines = [
        f"- {c['card_network']} {c['number']} ({c['card_type']})" for c in cards
    ]
    lines = [
        f"Name: {user['first_name']} {user['last_name']}",
        f"Email: {user['email']}",
        f"Phone: {user['country_code']}{user['phone_number']}",
    ]
    if card_lines:
        lines.append("Cards:")
        lines.extend(card_lines)
    return "\n".join(lines)


def build_get_account_tool(access_token: str) -> Tool:
    @trace_tool_call_async(name=_NAME, description=_DESCRIPTION)
    async def _run() -> str:
        try:
            user = await get_me(access_token)
        except AriapayAuthError:
            return MSG_SESSION_EXPIRED
        except AriapayAPIError:
            return MSG_ACCOUNT_FETCH_FAILED
        return _format_account(user)

    return Tool(name=_NAME, description=_DESCRIPTION, parameters=_PARAMETERS, run=_run)
