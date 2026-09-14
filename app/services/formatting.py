from datetime import datetime

from langchain_core.documents import Document

from app.constants import CURRENCY_PREFIX, TIMESTAMP_DISPLAY_FORMAT


def format_timestamp(timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return timestamp
    return dt.strftime(TIMESTAMP_DISPLAY_FORMAT)


def format_transaction_bullets(docs: list[Document]) -> str:
    lines = [
        "- {merchant} - {currency}{price:,.0f} on {timestamp}".format(
            merchant=d.metadata.get("merchant_name", "Unknown"),
            currency=CURRENCY_PREFIX,
            price=d.metadata.get("price", 0.0),
            timestamp=format_timestamp(d.metadata.get("timestamp", "")),
        )
        for d in docs
    ]
    return "\n".join(lines)


def format_account(user: dict) -> str:
    cards = user.get("cards") or []
    card_lines = [
        f"- {c['card_network']} {c['number']} ({c['card_type']})" for c in cards
    ]
    lines = [
        f"Name: {user['first_name']} {user['last_name']}",
        f"Email: {user['email']}",
        f"Phone: {user['country_code']}{user['phone_number']}",
    ]
    if card_lines:
        lines.append("Cards:")
        lines.extend(card_lines)
    return "\n".join(lines)
