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


def format_amount(amount: str) -> str:
    try:
        return f"{CURRENCY_PREFIX}{float(amount):,.0f}"
    except ValueError:
        return f"{CURRENCY_PREFIX}{amount}"


def format_transaction_page(data: dict) -> str:
    days = data.get("transactions") or []
    lines = []
    for day in days:
        lines.append(f"{day['date']} (spent {format_amount(day.get('total', '0'))}):")
        for t in day.get("items") or []:
            line = (
                f"- {t.get('merchant_name', 'Unknown')} - "
                f"{format_amount(t.get('amount', '0'))} - "
                f"{t.get('category_name', 'Uncategorized')} - "
                f"{t.get('status', 'UNKNOWN')}"
            )
            if t.get("failure_reason"):
                line += f" ({t['failure_reason']})"
            lines.append(line)

    shown = sum(len(d.get("items") or []) for d in days)
    total = (data.get("pagination") or {}).get("total_items", shown)
    if total > shown:
        lines.append(f"\nShowing {shown} of {total} matching transactions.")
    return "\n".join(lines)


def format_expenses(expenses: list[dict]) -> str:
    blocks = []
    for period in expenses:
        categories = period.get("categories") or []
        if not categories:
            continue
        p = period.get("period") or {}
        grand_total = sum(float(c.get("total", 0)) for c in categories)
        lines = [
            f"Spending from {p.get('from')} to {p.get('to')}: "
            f"{CURRENCY_PREFIX}{grand_total:,.0f} total"
        ]
        lines.extend(
            f"- {c.get('category_name', 'Unknown')}: "
            f"{format_amount(c.get('total', '0'))} across "
            f"{c.get('transaction_count', 0)} transaction(s)"
            for c in categories
        )
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)
