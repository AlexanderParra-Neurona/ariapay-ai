from datetime import datetime

from langchain_core.documents import Document

from app.constants import CURRENCY_PREFIX, TIMESTAMP_DISPLAY_FORMAT, TransactionStatus


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


def _amount_value(amount: str) -> float | None:
    try:
        return float(amount)
    except (TypeError, ValueError):
        return None


def _largest_success(days: list[dict]) -> tuple[str, dict] | None:
    # the chat model can't be trusted to compare amounts, so pick it here
    candidates = [
        (day["date"], t)
        for day in days
        for t in day.get("items") or []
        if t.get("status") == TransactionStatus.SUCCESS.value
        and _amount_value(t.get("amount")) is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda c: _amount_value(c[1]["amount"]))


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

    largest = _largest_success(days)
    if largest:
        date, t = largest
        lines.append(
            f"\n[Mention only if the user asks for their biggest/largest "
            f"transaction] Largest successful transaction shown: "
            f"{t.get('merchant_name', 'Unknown')} - "
            f"{format_amount(t['amount'])} on {date}"
        )
    return "\n".join(lines)


def format_expenses(categories: list[dict]) -> str:
    if not categories:
        return ""
    # every row carries the same queried period
    p = categories[0].get("period") or {}
    grand_total = sum(float(c.get("total", 0)) for c in categories)
    lines = [
        (
            f"Spending from {p.get('from')} to {p.get('to')}: "
            f"{CURRENCY_PREFIX}{grand_total:,.0f} total"
        )
    ]
    lines.extend(
        f"- {c.get('category_name', 'Unknown')}: {format_amount(c.get('total', '0'))}"
        for c in categories
    )
    return "\n".join(lines)
