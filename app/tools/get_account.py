import logging

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool

from app.constants import MSG_ACCOUNT_FETCH_FAILED, MSG_SESSION_EXPIRED, TraceName
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError, get_me
from app.services.formatting import format_account
from app.tracing import trace_tool_call_async

logger = logging.getLogger(__name__)

_NAME = TraceName.TOOL_GET_ACCOUNT.value
_DESCRIPTION = (
    "Get the signed-in user's own account profile: name, email, phone number, "
    "and cards on file. Use for questions about the user's identity or account "
    "details, not their transactions."
)


def build_get_account_tool() -> BaseTool:
    @trace_tool_call_async(name=_NAME, description=_DESCRIPTION)
    async def _run(config: RunnableConfig) -> str:
        access_token = config["configurable"]["access_token"]
        try:
            user = await get_me(access_token)
        except AriapayAuthError:
            return MSG_SESSION_EXPIRED
        except AriapayAPIError:
            return MSG_ACCOUNT_FETCH_FAILED
        except Exception:
            logger.exception("get_account: unexpected failure fetching account")
            return MSG_ACCOUNT_FETCH_FAILED
        return format_account(user)

    return StructuredTool.from_function(
        coroutine=_run, name=_NAME, description=_DESCRIPTION
    )
