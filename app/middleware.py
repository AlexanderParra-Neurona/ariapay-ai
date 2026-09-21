import json
from collections.abc import Awaitable, Callable
from typing import Any

from langfuse import get_client
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

DEFAULT_REDACT_KEYS = {"password", "passcode", "access_token", "refresh_token"}
REDACTED = "[REDACTED]"


class TraceIOMiddleware(BaseHTTPMiddleware):
    """Records request/response JSON bodies on the current root span's input/output.

    `FastAPIInstrumentor.instrument_app` creates one span per HTTP request
    but does not populate its input/output. Add this middleware alongside
    it to fill those in for the dashboard's Input/Output columns:

        app = FastAPI()
        FastAPIInstrumentor.instrument_app(app)
        app.add_middleware(TraceIOMiddleware)

    Keys in `redact_keys` (default: password/passcode/access_token/
    refresh_token) are replaced with "[REDACTED]" at any nesting depth
    before the body is recorded.
    """

    def __init__(self, app, redact_keys: set[str] = DEFAULT_REDACT_KEYS):
        super().__init__(app)
        self._redact_keys = redact_keys

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_body = await request.body()
        response = await call_next(request)

        chunks = [chunk async for chunk in response.body_iterator]
        response_body = b"".join(chunks)
        response.body_iterator = _replay(chunks)

        get_client().update_current_span(
            input=self._redacted_json(request_body),
            output=self._redacted_json(response_body),
        )

        return response

    def _redacted_json(self, body: bytes) -> Any | None:
        if not body:
            return None
        try:
            return _redact(json.loads(body), self._redact_keys)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None


def _redact(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            k: REDACTED if k in keys else _redact(v, keys) for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v, keys) for v in value]
    return value


async def _replay(chunks: list[bytes]):
    for chunk in chunks:
        yield chunk
