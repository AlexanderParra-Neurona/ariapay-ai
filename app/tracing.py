"""Thin tracing helpers on top of the Langfuse SDK.

Mirrors the decorator shapes previously provided by custodia-sdk
(`trace`, `trace_async`, `trace_tool_call`, `trace_tool_call_async`) so
call sites only need an import change. Prefer these over a bare `@observe`:
`observe` records positional args as an unnamed tuple, which the key-based
PII mask can't see into, so these helpers bind args to parameter names first.
"""

import functools
import inspect
import re
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from langfuse import get_client, observe

F = TypeVar("F", bound=Callable[..., Any])

REDACT_KEYS = {
    "password",
    "passcode",
    "token",
    "passcode_token",
    "access_token",
    "refresh_token",
    "email",
    "phone_number",
}
REDACTED = "[REDACTED]"

# Not recorded as span input: bound-method receivers, and LangChain's injected
# RunnableConfig (callback managers, plus the access_token under `configurable`).
_SKIP_PARAMS = {"self", "cls", "config"}

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Digits and spaces only (no dashes), so ISO dates like 2026-09-24 in tool
# output aren't mistaken for phone numbers.
_PHONE_PATTERN = re.compile(r"(?<!\d)\+?\d[\d\s]{8,}\d(?!\d)")


def redact(value: Any, keys: set[str] = REDACT_KEYS) -> Any:
    """Recursively replace values at `keys` (any nesting depth) with a redaction marker."""
    if isinstance(value, dict):
        return {k: REDACTED if k in keys else redact(v, keys) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, keys) for v in value]
    return value


def _scrub_text(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _scrub_text(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_text(v) for v in value]
    if isinstance(value, str):
        return _PHONE_PATTERN.sub(REDACTED, _EMAIL_PATTERN.sub(REDACTED, value))
    return value


def mask_pii(*, data: Any, **_: Any) -> Any:
    """Langfuse client-level mask: redacts known PII before spans leave the process.

    Applied to every span's input/output/metadata (traced function args/return
    values, tool-call args/results, LangChain callback data), independent of
    `TraceIOMiddleware` which only covers the top-level HTTP request/response
    body. Handles structured data via key-based redaction and free text at any
    depth (e.g. the `format_account` tool output) via email/phone scrubbing.
    """
    return _scrub_text(redact(data))


def _named_input(sig: inspect.Signature, args: tuple, kwargs: dict) -> Any:
    try:
        bound = sig.bind_partial(*args, **kwargs)
    except TypeError:
        return {"args": list(args), "kwargs": kwargs}
    return {k: v for k, v in bound.arguments.items() if k not in _SKIP_PARAMS}


def _traced(
    name: str | None,
    *,
    as_type: str | None = None,
    capture_output: bool = True,
    metadata: Callable[[], dict] | None = None,
) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        sig = inspect.signature(fn)

        def record_input(args: tuple, kwargs: dict) -> None:
            update: dict[str, Any] = {"input": _named_input(sig, args, kwargs)}
            if metadata is not None:
                update["metadata"] = metadata()
            get_client().update_current_span(**update)

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                record_input(args, kwargs)
                return await fn(*args, **kwargs)

        else:

            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                record_input(args, kwargs)
                return fn(*args, **kwargs)

        observe_kwargs: dict[str, Any] = {
            "name": name or fn.__name__,
            "capture_input": False,
            "capture_output": capture_output,
        }
        if as_type is not None:
            observe_kwargs["as_type"] = as_type
        return observe(**observe_kwargs)(wrapper)  # type: ignore[return-value]

    return decorator


def trace(name: str | None = None, *, capture_output: bool = True) -> Callable[[F], F]:
    """Wrap a synchronous function in a Langfuse span, capturing args/result.

    Pass `capture_output=False` when the return value is itself a credential.
    """
    return _traced(name, capture_output=capture_output)


def trace_async(
    name: str | None = None, *, capture_output: bool = True
) -> Callable[[F], F]:
    """Wrap an async function in a Langfuse span, capturing args/result.

    Pass `capture_output=False` when the return value is itself a credential.
    """
    return _traced(name, capture_output=capture_output)


def _tool_metadata(description: str | None) -> Callable[[], dict]:
    return lambda: {"tool_call_id": str(uuid.uuid4()), "description": description}


def trace_tool_call(
    name: str | None = None, description: str | None = None
) -> Callable[[F], F]:
    """Wrap a synchronous tool handler in a Langfuse tool-type span."""
    return _traced(name, as_type="tool", metadata=_tool_metadata(description))


def trace_tool_call_async(
    name: str | None = None, description: str | None = None
) -> Callable[[F], F]:
    """Async counterpart to `trace_tool_call`."""
    return _traced(name, as_type="tool", metadata=_tool_metadata(description))
