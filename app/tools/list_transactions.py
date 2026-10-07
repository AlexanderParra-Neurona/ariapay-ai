import calendar
import logging
from datetime import date
from typing import Annotated, Literal

from custodia import trace_tool_call_async
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, StructuredTool

from app.constants import (
    ARIAPAY_TRANSACTIONS_PAGE_SIZE_MAX,
    MSG_NO_TRANSACTIONS_FOUND,
    MSG_SESSION_EXPIRED,
    MSG_TRANSACTIONS_FETCH_FAILED,
    TraceName,
    TransactionCategory,
    TransactionStatus,
)
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError
from app.services.ariapay_transactions_service import (
    AriapayBadRequestError,
    AriapayNotFoundError,
    resolve_category_id,
)
from app.services.ariapay_transactions_service import (
    list_transactions as fetch_transactions,
)
from app.services.formatting import format_transaction_page

logger = logging.getLogger(__name__)

_NAME = TraceName.TOOL_LIST_TRANSACTIONS.value
_DESCRIPTION = (
    "List the signed-in user's own transactions (QRIS payments), grouped by "
    "day, optionally filtered by category, status, or period. Use for 'show my "
    "recent transactions', 'what did I buy last week', or 'which payments "
    "failed'. For totals or 'how much did I spend' questions, use "
    "get_spending_summary instead."
)
_DEFAULT_LIMIT = 20

_CategoryLiteral = Literal[tuple(c.value for c in TransactionCategory)]
_StatusLiteral = Literal[tuple(s.value for s in TransactionStatus)]


def month_to_range(month: str) -> tuple[str, str]:
    year, mon = (int(part) for part in month.split("-"))
    last_day = calendar.monthrange(year, mon)[1]
    return date(year, mon, 1).isoformat(), date(year, mon, last_day).isoformat()


def build_list_transactions_tool() -> BaseTool:
    @trace_tool_call_async(name=_NAME, description=_DESCRIPTION)
    async def _run(
        config: RunnableConfig,
        category: Annotated[
            _CategoryLiteral | None,
            "Spending category, if the user mentions or implies one. Omit otherwise.",
        ] = None,
        status: Annotated[
            _StatusLiteral | None,
            "Only if the user asks about pending, successful, or failed payments.",
        ] = None,
        month: Annotated[
            str | None,
            "Calendar month as YYYY-MM. Do not combine with date_from/date_to.",
        ] = None,
        date_from: Annotated[str | None, "Start date YYYY-MM-DD, inclusive."] = None,
        date_to: Annotated[str | None, "End date YYYY-MM-DD, inclusive."] = None,
        limit: Annotated[
            int,
            "Max transactions to return (1-100). Use 100 when the user asks for "
            "everything in a period; keep small for 'recent'/'last few'.",
        ] = _DEFAULT_LIMIT,
    ) -> str:
        access_token = config["configurable"]["access_token"]
        if month:
            if date_from or date_to:
                return "Use either month or date_from/date_to, not both."
            try:
                date_from, date_to = month_to_range(month)
            except ValueError:
                return f"Invalid month {month!r}; expected YYYY-MM."

        try:
            category_id = None
            if category:
                category_id = await resolve_category_id(access_token, category)
                if category_id is None:
                    return MSG_NO_TRANSACTIONS_FOUND
            data = await fetch_transactions(
                access_token,
                category_id=category_id,
                date_from=date_from,
                date_to=date_to,
                status=status,
                page_size=max(1, min(limit, ARIAPAY_TRANSACTIONS_PAGE_SIZE_MAX)),
            )
        except AriapayAuthError:
            return MSG_SESSION_EXPIRED
        except AriapayBadRequestError as e:
            return f"The transaction filter was rejected: {e}"
        except AriapayNotFoundError:
            return MSG_NO_TRANSACTIONS_FOUND
        except AriapayAPIError:
            return MSG_TRANSACTIONS_FETCH_FAILED
        except Exception:
            logger.exception("list_transactions: unexpected failure")
            return MSG_TRANSACTIONS_FETCH_FAILED

        if not data.get("transactions"):
            return MSG_NO_TRANSACTIONS_FOUND
        return format_transaction_page(data)

    return StructuredTool.from_function(
        coroutine=_run, name=_NAME, description=_DESCRIPTION
    )
