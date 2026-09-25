"""Thin tracing helpers on top of the Langfuse SDK.

Mirrors the decorator shapes previously provided by custodia-sdk
(`trace`, `trace_async`, `trace_tool_call`, `trace_tool_call_async`) so
call sites only need an import change. Prefer `@observe` directly for
new code.
"""

import functools
import re
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from langfuse import get_client, observe

F = TypeVar("F", bound=Callable[..., Any])

REDACT_KEYS = {"password", "passcode", "access_token", "refresh_token"}
REDACTED = "[REDACTED]"

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_PATTERN = re.compile(r"(?<!\d)(\+?\d[\d\-\s]{7,}\d)(?!\d)")


def redact(value: Any, keys: set[str] = REDACT_KEYS) -> Any:
    """Recursively replace values at `keys` (any nesting depth) with a redaction marker."""
    if isinstance(value, dict):
        return {k: REDACTED if k in keys else redact(v, keys) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, keys) for v in value]
    return value


def mask_pii(*, data: Any, **_: Any) -> Any:
    """Langfuse client-level mask: redacts known PII before spans leave the process.

    Applied to every trace's input/output (traced function args/return
    values, tool-call args/results), independent of `TraceIOMiddleware`
    which only covers the top-level HTTP request/response body. Handles
    structured data via key-based redaction and free text (e.g. the
    `format_account` tool output) via email/phone pattern scrubbing.
    """
    redacted = redact(data)
    if isinstance(redacted, str):
        redacted = _EMAIL_PATTERN.sub(REDACTED, redacted)
        redacted = _PHONE_PATTERN.sub(REDACTED, redacted)
    return redacted


def trace(name: str | None = None) -> Callable[[F], F]:
    """Wrap a synchronous function in a Langfuse span, capturing args/result."""
    return observe(name=name)


def trace_async(name: str | None = None) -> Callable[[F], F]:
    """Wrap an async function in a Langfuse span, capturing args/result."""
    return observe(name=name)


def trace_tool_call(
    name: str | None = None, description: str | None = None
) -> Callable[[F], F]:
    """Wrap a synchronous tool handler in a Langfuse tool-type span."""

    def decorator(fn: F) -> F:
        span_name = name or fn.__name__

        @functools.wraps(fn)
        def with_metadata(*args: Any, **kwargs: Any) -> Any:
            get_client().update_current_span(
                metadata={"tool_call_id": str(uuid.uuid4()), "description": description}
            )
            return fn(*args, **kwargs)

        return observe(name=span_name, as_type="tool")(with_metadata)  # type: ignore[return-value]

    return decorator


def trace_tool_call_async(
    name: str | None = None, description: str | None = None
) -> Callable[[F], F]:
    """Async counterpart to `trace_tool_call`."""

    def decorator(fn: F) -> F:
        span_name = name or fn.__name__

        @functools.wraps(fn)
        async def with_metadata(*args: Any, **kwargs: Any) -> Any:
            get_client().update_current_span(
                metadata={"tool_call_id": str(uuid.uuid4()), "description": description}
            )
            return await fn(*args, **kwargs)

        return observe(name=span_name, as_type="tool")(with_metadata)  # type: ignore[return-value]

    return decorator
