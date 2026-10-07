import logging
from typing import Annotated

from custodia import trace_tool_call_async
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool

from app.constants import (
    MSG_NO_TRANSACTIONS_FOUND,
    MSG_SESSION_EXPIRED,
    MSG_TRANSACTIONS_FETCH_FAILED,
    TraceName,
)
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError
from app.services.ariapay_transactions_service import (
    AriapayBadRequestError,
    get_expenses,
)
from app.services.formatting import format_expenses

logger = logging.getLogger(__name__)

_NAME = TraceName.TOOL_GET_SPENDING_SUMMARY.value
_DESCRIPTION = (
    "Get the signed-in user's total completed spending per category for one "
    "calendar month or a date range. Only successful payments count. Use for "
    "'how much did I spend', 'what did I spend most on', or monthly breakdown "
    "questions. Defaults to the current month when no period is given."
)


def build_get_spending_summary_tool() -> BaseTool:
    @trace_tool_call_async(name=_NAME, description=_DESCRIPTION)
    async def _run(
        config: RunnableConfig,
        month: Annotated[
            str | None,
            "Calendar month as YYYY-MM. Do not combine with date_from/date_to.",
        ] = None,
        date_from: Annotated[
            str | None, "Start date YYYY-MM-DD. Requires date_to."
        ] = None,
        date_to: Annotated[
            str | None, "End date YYYY-MM-DD. Requires date_from."
        ] = None,
    ) -> str:
        if month and (date_from or date_to):
            return "Use either month or date_from/date_to, not both."
        if bool(date_from) != bool(date_to):
            return "date_from and date_to must be given together."

        access_token = config["configurable"]["access_token"]
        try:
            expenses = await get_expenses(
                access_token, month=month, date_from=date_from, date_to=date_to
            )
        except AriapayAuthError:
            return MSG_SESSION_EXPIRED
        except AriapayBadRequestError as e:
            return f"The spending period was rejected: {e}"
        except AriapayAPIError:
            return MSG_TRANSACTIONS_FETCH_FAILED
        except Exception:
            logger.exception("get_spending_summary: unexpected failure")
            return MSG_TRANSACTIONS_FETCH_FAILED

        return format_expenses(expenses) or MSG_NO_TRANSACTIONS_FOUND

    return StructuredTool.from_function(
        coroutine=_run, name=_NAME, description=_DESCRIPTION
    )
