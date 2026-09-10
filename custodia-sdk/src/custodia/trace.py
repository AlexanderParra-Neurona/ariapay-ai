import functools
import json
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional

from opentelemetry.trace import Status, StatusCode

from ._tracer import get_tracer

GENAI_PROMPT_ATTR = "gen_ai.prompt"
GENAI_COMPLETION_ATTR = "gen_ai.completion"


def _set_io_attributes(span: Any, args: tuple, kwargs: dict, result: Any) -> None:
    try:
        span.set_attribute(GENAI_PROMPT_ATTR, json.dumps({"args": _safe_repr(args), "kwargs": _safe_repr(kwargs)}))
        span.set_attribute(GENAI_COMPLETION_ATTR, _safe_repr(result))
    except TypeError:
        pass


def _safe_repr(value: Any) -> str:
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return repr(value)


def trace(name: Optional[str] = None, metadata: Optional[dict] = None) -> Callable:
    def decorator(fn: Callable) -> Callable:
        span_name = name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()
            with tracer.start_as_current_span(span_name) as span:
                if metadata:
                    for key, value in metadata.items():
                        span.set_attribute(f"metadata.{key}", _safe_repr(value))
                try:
                    result = fn(*args, **kwargs)
                except Exception as exc:
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    span.record_exception(exc)
                    raise
                _set_io_attributes(span, args, kwargs, result)
                return result

        return wrapper

    return decorator


@contextmanager
def trace_span(name: str, metadata: Optional[dict] = None) -> Generator[Any, None, None]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if metadata:
            for key, value in metadata.items():
                span.set_attribute(f"metadata.{key}", _safe_repr(value))
        try:
            yield span
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise
