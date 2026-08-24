from enum import Enum


class QueryCategory(str, Enum):
    GENERAL_FAQ = "general_faq"
    TRANSACTION_INQUIRY = "transaction_inquiry"
    OUT_OF_SCOPE = "out_of_scope"
