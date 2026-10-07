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

HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_NOT_FOUND = 404

ARIAPAY_PLATFORM_HEADERS = {"X-Platform": "android", "X-App-Version": "1.0.0"}

ARIAPAY_ME_PATH = "/api/v1/users/me"
ARIAPAY_LOGIN_PATH = "/api/v1/login"
ARIAPAY_PASSCODE_VERIFY_PATH = "/api/v1/passcode/verify"

ARIAPAY_TRANSACTION_CATEGORIES_PATH = "/api/v1/transaction-categories"
ARIAPAY_TRANSACTIONS_PATH = "/api/v1/transactions"
ARIAPAY_TRANSACTIONS_BY_CATEGORY_PATH = "/api/v1/transactions/categories/{category_id}"
ARIAPAY_EXPENSES_PATH = "/api/v1/transactions/categories/expenses"

ARIAPAY_TRANSACTIONS_PAGE_SIZE_MAX = 100

APP_TIMEZONE = "Asia/Jakarta"

DOCURA_QUERY_PATH = "/v1/query"
# a Docura query is an intent-classification LLM call plus an answer LLM call
HTTP_TIMEOUT_DOCURA_SECONDS = 120

# --- LLM ---


class TraceName(str, Enum):
    AGENT_LOOP = "agent_loop"
    QUERY_CLASSIFIER = "query_classifier"
    LITELLM_EMBED = "litellm_embed"
    QDRANT_UPSERT_TRANSACTIONS = "qdrant_upsert_transactions"
    QDRANT_SIMILARITY_SEARCH_TRANSACTIONS = "qdrant_similarity_search_transactions"
    QDRANT_GET_ALL_TRANSACTIONS = "qdrant_get_all_transactions"
    DOCURA_QUERY = "docura_query"
    ARIAPAY_GET_ME = "ariapay_get_me"
    ARIAPAY_LOGIN = "ariapay_login"
    ARIAPAY_VERIFY_PASSCODE = "ariapay_verify_passcode"
    TOOL_SEARCH_FAQ = "search_faq"
    TOOL_SEARCH_TRANSACTIONS = "search_transactions"
    TOOL_GET_ACCOUNT = "get_account"
    ARIAPAY_LIST_TRANSACTION_CATEGORIES = "ariapay_list_transaction_categories"
    ARIAPAY_LIST_TRANSACTIONS = "ariapay_list_transactions"
    ARIAPAY_GET_EXPENSES = "ariapay_get_expenses"
    TOOL_LIST_TRANSACTIONS = "list_transactions"
    TOOL_GET_SPENDING_SUMMARY = "get_spending_summary"


DEEPINFRA_OPENAI_BASE = "https://api.deepinfra.com/v1/openai"
OPENAI_MODEL_PREFIX = "openai/"

CHAT_MAX_TOKENS = 2048


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


class TransactionCategory(str, Enum):
    """Mirrors the payments service's seeded transaction_categories names."""

    FOOD_AND_BEVERAGE = "Food & Beverage"
    GROCERIES = "Groceries"
    TRANSPORTATION = "Transportation"
    SHOPPING = "Shopping"
    BILLS_AND_UTILITIES = "Bills & Utilities"
    ENTERTAINMENT = "Entertainment"
    HEALTH = "Health"
    EDUCATION = "Education"
    TRANSFER = "Transfer"
    OTHER = "Other"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


MSG_TRANSACTIONS_FETCH_FAILED = "Sorry, I couldn't fetch your transactions right now."


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

# --- UI / user-facing messages ---

CURRENCY_PREFIX = "Rp"
TIMESTAMP_DISPLAY_FORMAT = "%b %-d, %Y, %-I:%M %p"

MSG_OUT_OF_SCOPE = (
    "Sorry, I can't help with that. I can answer questions about Ariapay "
    "or your account balance and transactions."
)
MSG_NO_DOCS_FOUND = "Sorry, I don't have information on that."
MSG_AGENT_NO_ANSWER = "Sorry, I couldn't find an answer to that."
MSG_AGENT_TOO_COMPLEX = (
    "Sorry, that request needs more steps than I can take right now. "
    "Try breaking it into smaller questions."
)
MSG_SIGN_IN_FOR_ACCOUNT = "Please sign in to view your account details."
MSG_SESSION_EXPIRED = "Your session has expired. Please sign in again."
MSG_ACCOUNT_FETCH_FAILED = "Sorry, I couldn't fetch your account details right now."
MSG_SIGN_IN_FOR_TRANSACTIONS = "Please sign in to view your transactions."
MSG_NO_TRANSACTIONS_FOUND = "I couldn't find any transactions matching that."
