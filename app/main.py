import logging

from fastapi import FastAPI
from langfuse import get_client
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.constants import API_V1_PREFIX, APP_TITLE
from app.middleware import TraceIOMiddleware
from app.routers.v1.auth import router as auth_v1_router
from app.routers.v1.chat import router as chat_v1_router
from app.routers.v1.health import router as health_v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

get_client()  # initialize the Langfuse client eagerly, before the first request

app = FastAPI(title=APP_TITLE)
FastAPIInstrumentor.instrument_app(app)
app.add_middleware(TraceIOMiddleware)

app.include_router(health_v1_router, prefix=API_V1_PREFIX)
app.include_router(auth_v1_router, prefix=API_V1_PREFIX)
app.include_router(chat_v1_router, prefix=API_V1_PREFIX)
