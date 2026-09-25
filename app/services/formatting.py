from datetime import datetime

from langchain_core.documents import Document

from app.constants import CURRENCY_PREFIX, TIMESTAMP_DISPLAY_FORMAT


def format_timestamp(timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(timestamp)
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
        f"- {c.get('card_network', 'Unknown')} {c.get('number', '')} "
        f"({c.get('card_type', 'Unknown')})"
        for c in cards
    ]
    lines = [
        f"Name: {user.get('first_name', '')} {user.get('last_name', '')}".strip(),
        f"Email: {user.get('email', 'Unknown')}",
        f"Phone: {user.get('country_code', '')}{user.get('phone_number', '')}",
    ]
    if card_lines:
        lines.append("Cards:")
        lines.extend(card_lines)
    return "\n".join(lines)
