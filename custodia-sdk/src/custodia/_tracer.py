import os

from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_initialized = False


def _ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return

    endpoint = os.environ.get("CUSTODIA_INGEST_URL", "http://localhost:4318/v1/traces")
    api_key = os.environ.get("CUSTODIA_API_KEY", "")

    provider = TracerProvider(
        resource=Resource.create({"service.name": os.environ.get("CUSTODIA_SERVICE_NAME", "unknown-service")})
    )
    exporter = OTLPSpanExporter(
        endpoint=endpoint,
        headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    otel_trace.set_tracer_provider(provider)
    _initialized = True


def get_tracer() -> otel_trace.Tracer:
    _ensure_initialized()
    return otel_trace.get_tracer("custodia-sdk")
