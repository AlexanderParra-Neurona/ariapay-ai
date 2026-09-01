"""Centralized constants for ariabot.

Cross-cutting literals only. Runtime-configurable/env-backed values stay in
app/config.py.
"""

from enum import Enum

# --- App ---

APP_TITLE = "ariabot"

# --- HTTP / API ---

API_V1_PREFIX = "/v1"
BEARER_PREFIX = "Bearer"

HTTP_TIMEOUT_DEFAULT_SECONDS = 30
HTTP_TIMEOUT_CHAT_SECONDS = 300

HTTP_STATUS_OK = 200
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_BAD_GATEWAY = 502

ARIAPAY_PLATFORM_HEADERS = {"X-Platform": "android", "X-App-Version": "1.0.0"}

ARIAPAY_ME_PATH = "/api/v1/users/me"
ARIAPAY_LOGIN_PATH = "/api/v1/login"
ARIAPAY_PASSCODE_VERIFY_PATH = "/api/v1/passcode/verify"

# --- LLM ---


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"


class TraceName(str, Enum):
    CHAT_ANSWER = "chat_answer"
    QUERY_CLASSIFIER = "query_classifier"
    TRANSACTION_SCOPE_CLASSIFIER = "transaction_scope_classifier"


TRACE_NAME_METADATA_KEY = "trace_name"

DEEPINFRA_OPENAI_BASE = "https://api.deepinfra.com/v1/openai"
OPENAI_MODEL_PREFIX = "openai/"


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    DEEPINFRA = "deepinfra"


# --- Classification ---


class SpendingCategory(str, Enum):
    FOOD_AND_BEVERAGE = "food_and_beverage"
    RETAIL = "retail"
    TRANSPORTATION = "transportation"
    HEALTH_AND_WELLNESS = "health_and_wellness"
    ENTERTAINMENT = "entertainment"
    HOME_AND_GARDEN = "home_and_garden"


# --- Qdrant / retrieval ---

DOCS_VECTOR_NAME = "docs"
TRANSACTIONS_VECTOR_NAME = "transactions"

POINT_TYPE_DOC = "doc"
POINT_TYPE_TRANSACTION = "transaction"

POINT_ID_HASH_LENGTH = 32
QDRANT_SCROLL_BATCH_SIZE = 1000

DEFAULT_SIMILARITY_SEARCH_K = 4
DEFAULT_TRANSACTIONS_MAX_RESULTS = 200

RRF_K_CONSTANT = 60

# --- Redis / FAQ cache ---

FAQ_INDEX_NAME = "idx:faq"
FAQ_KEY_PREFIX = "faq:doc:"

# --- UI / user-facing messages ---

CURRENCY_PREFIX = "Rp"
TIMESTAMP_DISPLAY_FORMAT = "%b %-d, %Y, %-I:%M %p"

MSG_OUT_OF_SCOPE = (
    "Sorry, I can't help with that. I can answer questions about Ariapay "
    "or your account balance and transactions."
)
MSG_NO_DOCS_FOUND = "Sorry, I don't have information on that."
MSG_SIGN_IN_FOR_ACCOUNT = "Please sign in to view your account details."
MSG_SESSION_EXPIRED = "Your session has expired. Please sign in again."
MSG_ACCOUNT_FETCH_FAILED = "Sorry, I couldn't fetch your account details right now."
MSG_SIGN_IN_FOR_TRANSACTIONS = "Please sign in to view your transactions."
MSG_NO_TRANSACTIONS_FOUND = "I couldn't find any transactions matching that."
