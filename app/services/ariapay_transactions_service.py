"""Read-only client for the Ariapay payments service's transaction endpoints.

Ariabot must never write to this service: every request goes through a client
whose request hook rejects anything but GET. QRIS inquiry/charge are
deliberately not wrapped here.
"""

import logging

import httpx

from app.config import settings
from app.constants import (
    ARIAPAY_EXPENSES_PATH,
    ARIAPAY_PLATFORM_HEADERS,
    ARIAPAY_TRANSACTION_CATEGORIES_PATH,
    ARIAPAY_TRANSACTIONS_BY_CATEGORY_PATH,
    ARIAPAY_TRANSACTIONS_PAGE_SIZE_MAX,
    ARIAPAY_TRANSACTIONS_PATH,
    BEARER_PREFIX,
    HTTP_STATUS_BAD_REQUEST,
    HTTP_STATUS_NOT_FOUND,
    HTTP_STATUS_OK,
    HTTP_STATUS_UNAUTHORIZED,
    HTTP_TIMEOUT_DEFAULT_SECONDS,
    TraceName,
)
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError
from app.tracing import trace_async

logger = logging.getLogger(__name__)

_category_ids: dict[str, int] = {}


class AriapayReadOnlyViolation(Exception):
    pass


class AriapayBadRequestError(AriapayAPIError):
    pass


class AriapayNotFoundError(AriapayAPIError):
    pass


async def _reject_non_get(request: httpx.Request) -> None:
    if request.method != "GET":
        raise AriapayReadOnlyViolation(
            f"Blocked {request.method} {request.url.path}: ariabot is read-only "
            "against the payments service"
        )


def _error_message(resp: httpx.Response) -> str:
    try:
        return resp.json().get("error_message") or resp.text
    except ValueError:
        return resp.text


async def _get(path: str, access_token: str, params: dict | None = None) -> dict:
    query = {k: v for k, v in (params or {}).items() if v is not None}
    async with httpx.AsyncClient(event_hooks={"request": [_reject_non_get]}) as client:
        resp = await client.get(
            f"{settings.ARIAPAY_API_URL}{path}",
            params=query,
            headers={
                **ARIAPAY_PLATFORM_HEADERS,
                "Authorization": f"{BEARER_PREFIX} {access_token}",
            },
            timeout=HTTP_TIMEOUT_DEFAULT_SECONDS,
        )

    if resp.status_code == HTTP_STATUS_UNAUTHORIZED:
        logger.warning("GET %s: invalid or expired access_token", path)
        raise AriapayAuthError("Missing or invalid access_token")
    if resp.status_code == HTTP_STATUS_BAD_REQUEST:
        raise AriapayBadRequestError(_error_message(resp))
    if resp.status_code == HTTP_STATUS_NOT_FOUND:
        raise AriapayNotFoundError(_error_message(resp))
    if resp.status_code != HTTP_STATUS_OK:
        logger.error("GET %s: Ariapay API returned %s", path, resp.status_code)
        raise AriapayAPIError(f"Ariapay API returned {resp.status_code}")
    return resp.json()


@trace_async(name=TraceName.ARIAPAY_LIST_TRANSACTION_CATEGORIES.value)
async def list_transaction_categories(access_token: str) -> list[dict]:
    data = await _get(ARIAPAY_TRANSACTION_CATEGORIES_PATH, access_token)
    return data["transaction_categories"]


async def resolve_category_id(access_token: str, name: str) -> int | None:
    if not _category_ids:
        categories = await list_transaction_categories(access_token)
        _category_ids.update({c["name"].lower(): c["id"] for c in categories})
    return _category_ids.get(name.lower())


@trace_async(name=TraceName.ARIAPAY_LIST_TRANSACTIONS.value)
async def list_transactions(
    access_token: str,
    *,
    category_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: str | None = None,
    page_no: int = 1,
    page_size: int = ARIAPAY_TRANSACTIONS_PAGE_SIZE_MAX,
) -> dict:
    path = (
        ARIAPAY_TRANSACTIONS_BY_CATEGORY_PATH.format(category_id=category_id)
        if category_id is not None
        else ARIAPAY_TRANSACTIONS_PATH
    )
    return await _get(
        path,
        access_token,
        params={
            "date_from": date_from,
            "date_to": date_to,
            "status": status,
            "page_no": page_no,
            "page_size": page_size,
        },
    )


@trace_async(name=TraceName.ARIAPAY_GET_EXPENSES.value)
async def get_expenses(
    access_token: str,
    *,
    month: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    data = await _get(
        ARIAPAY_EXPENSES_PATH,
        access_token,
        params={"month": month, "date_from": date_from, "date_to": date_to},
    )
    return data["expenses"]
