from enum import Enum


class QueryCategory(str, Enum):
    GENERAL_FAQ = "general_faq"
    ACCOUNT_PROFILE = "account_profile"
    TRANSACTION_HISTORY = "transaction_history"
    OUT_OF_SCOPE = "out_of_scope"
