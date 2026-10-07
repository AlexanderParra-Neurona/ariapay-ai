import logging

import httpx

from app.config import settings
from app.constants import (
    DOCURA_QUERY_PATH,
    HTTP_STATUS_OK,
    HTTP_TIMEOUT_DEFAULT_SECONDS,
    TraceName,
)
from app.tracing import trace_async

logger = logging.getLogger(__name__)


class DocuraAPIError(Exception):
    pass


@trace_async(name=TraceName.DOCURA_QUERY.value)
async def query(question: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.DOCURA_API_URL}{DOCURA_QUERY_PATH}",
            json={"question": question},
            timeout=HTTP_TIMEOUT_DEFAULT_SECONDS,
        )
    if resp.status_code != HTTP_STATUS_OK:
        logger.error("Docura query: API returned %s", resp.status_code)
        raise DocuraAPIError(f"Docura API returned {resp.status_code}")
    return resp.json()
