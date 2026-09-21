"""Thin tracing helpers on top of the Langfuse SDK.

Mirrors the decorator shapes previously provided by custodia-sdk
(`trace`, `trace_async`, `trace_tool_call`, `trace_tool_call_async`) so
call sites only need an import change. Prefer `@observe` directly for
new code.
"""

import functools
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from langfuse import get_client, observe

F = TypeVar("F", bound=Callable[..., Any])


def trace(name: str | None = None) -> Callable[[F], F]:
    """Wrap a synchronous function in a Langfuse span, capturing args/result."""
    return observe(name=name)


def trace_async(name: str | None = None) -> Callable[[F], F]:
    """Wrap an async function in a Langfuse span, capturing args/result."""
    return observe(name=name)


def trace_tool_call(
    name: str | None = None, description: str | None = None
) -> Callable[[F], F]:
    """Wrap a synchronous tool handler in a Langfuse tool-type span.

    Pass `tool_call_id` as a keyword argument to the wrapped function to
    attribute the span to a specific model-issued tool call; it is
    consumed by the wrapper and not forwarded to the wrapped function.
    """

    def decorator(fn: F) -> F:
        span_name = name or fn.__name__

        @functools.wraps(fn)
        def with_metadata(*args: Any, **kwargs: Any) -> Any:
            tool_call_id = kwargs.pop("tool_call_id", None) or str(uuid.uuid4())
            get_client().update_current_span(
                metadata={"tool_call_id": tool_call_id, "description": description}
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
            tool_call_id = kwargs.pop("tool_call_id", None) or str(uuid.uuid4())
            get_client().update_current_span(
                metadata={"tool_call_id": tool_call_id, "description": description}
            )
            return await fn(*args, **kwargs)

        return observe(name=span_name, as_type="tool")(with_metadata)  # type: ignore[return-value]

    return decorator
