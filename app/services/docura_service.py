import logging

import httpx

from app.config import settings
from app.constants import (
    DOCURA_QUERY_PATH,
    HTTP_STATUS_OK,
    HTTP_STATUS_UNAUTHORIZED,
    HTTP_TIMEOUT_DOCURA_SECONDS,
    TraceName,
)
from app.tracing import trace_async

logger = logging.getLogger(__name__)


class DocuraAPIError(Exception):
    pass


def _headers() -> dict[str, str]:
    # Docura requires X-API-Key whenever its API_KEY is set (always in production)
    return {"X-API-Key": settings.DOCURA_API_KEY} if settings.DOCURA_API_KEY else {}


@trace_async(name=TraceName.DOCURA_QUERY.value)
async def query(question: str) -> dict:
    url = f"{settings.DOCURA_API_URL.rstrip('/')}{DOCURA_QUERY_PATH}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={"question": question},
                headers=_headers(),
                timeout=HTTP_TIMEOUT_DOCURA_SECONDS,
            )
    except httpx.TimeoutException as exc:
        logger.error("Docura query: timed out after %ss", HTTP_TIMEOUT_DOCURA_SECONDS)
        raise DocuraAPIError("Docura API timed out") from exc
    except httpx.HTTPError as exc:
        # also covers an unset/invalid DOCURA_API_URL (UnsupportedProtocol)
        logger.error("Docura query: request failed: %s", exc)
        raise DocuraAPIError("Could not reach Docura API") from exc

    if resp.status_code == HTTP_STATUS_UNAUTHORIZED:
        logger.error("Docura query: 401, check DOCURA_API_KEY matches Docura's API_KEY")
        raise DocuraAPIError("Docura API rejected the API key")
    if resp.status_code != HTTP_STATUS_OK:
        logger.error("Docura query: API returned %s", resp.status_code)
        raise DocuraAPIError(f"Docura API returned {resp.status_code}")

    try:
        return resp.json()
    except ValueError as exc:
        logger.error("Docura query: response is not JSON")
        raise DocuraAPIError("Docura API returned invalid JSON") from exc
