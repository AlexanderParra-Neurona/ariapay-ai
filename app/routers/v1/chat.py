from datetime import datetime

from fastapi import APIRouter
from langchain_core.documents import Document

from app.constants import (
    CURRENCY_PREFIX,
    MSG_ACCOUNT_FETCH_FAILED,
    MSG_NO_DOCS_FOUND,
    MSG_NO_TRANSACTIONS_FOUND,
    MSG_OUT_OF_SCOPE,
    MSG_SESSION_EXPIRED,
    MSG_SIGN_IN_FOR_ACCOUNT,
    MSG_SIGN_IN_FOR_TRANSACTIONS,
    Role,
    TIMESTAMP_DISPLAY_FORMAT,
    TraceName,
    TRACE_NAME_METADATA_KEY,
)
from app.schemas import ChatRequest, ChatResponse, Citation, PolicyDecision
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError, get_me
from app.services.classification import (
    QueryCategory,
    get_query_classifier,
    get_transaction_scope_classifier,
)
from app.services.llm import get_llm_service
from app.services.retrieval import get_hybrid_retriever

router = APIRouter()


def _answer_from_docs(question: str) -> tuple[str, list[Citation], float | None]:
    hits = get_hybrid_retriever().search(question)
    if not hits:
        return MSG_NO_DOCS_FOUND, [], None

    docs = [doc for doc, _ in hits]
    citations = [
        Citation(
            source=d.metadata.get("source", ""), heading=d.metadata.get("heading", "")
        )
        for d in docs
    ]
    confidence = hits[0][1]

    context_block = "\n\n".join(d.page_content for d in docs)
    prompt = (
        "Answer the question using only the context below. Be concise.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\nAnswer:"
    )
    answer = get_llm_service().chat(
        [{"role": Role.USER, "content": prompt}],
        metadata={TRACE_NAME_METADATA_KEY: TraceName.CHAT_ANSWER},
    )
    return answer, citations, confidence


def _format_timestamp(timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return timestamp
    return dt.strftime(TIMESTAMP_DISPLAY_FORMAT)


def _transaction_bullets(docs: list[Document]) -> str:
    lines = [
        "- {merchant} - {currency}{price:,.0f} on {timestamp}".format(
            merchant=d.metadata.get("merchant_name", "Unknown"),
            currency=CURRENCY_PREFIX,
            price=d.metadata.get("price", 0.0),
            timestamp=_format_timestamp(d.metadata.get("timestamp", "")),
        )
        for d in docs
    ]
    return "\n".join(lines)


def _answer_from_transactions(question: str) -> str | None:
    scope = get_transaction_scope_classifier().classify(question)
    docs = get_hybrid_retriever().search_transactions(question, scope=scope)
    if scope is not None and scope.category is not None:
        docs = [d for d in docs if d.metadata.get("category") == scope.category]
    if not docs:
        return None

    total = sum(d.metadata.get("price", 0.0) for d in docs)
    summary = (
        f"You spent a total of {CURRENCY_PREFIX}{total:,.0f} "
        f"across {len(docs)} transaction(s)."
    )
    bullets = _transaction_bullets(docs)
    return f"{summary}\n\n{bullets}"


def _format_me_answer(user: dict) -> str:
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


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    category = get_query_classifier().classify(req.question)

    if category == QueryCategory.ACCOUNT_PROFILE:
        if not req.access_token:
            return ChatResponse(
                answer=MSG_SIGN_IN_FOR_ACCOUNT,
                short_circuit=True,
                category=category,
                policy_decision=PolicyDecision.DECLINED_AUTH_REQUIRED,
            )
        try:
            user = await get_me(req.access_token)
        except AriapayAuthError:
            return ChatResponse(
                answer=MSG_SESSION_EXPIRED,
                short_circuit=True,
                category=category,
                policy_decision=PolicyDecision.DECLINED_AUTH_REQUIRED,
            )
        except AriapayAPIError:
            return ChatResponse(
                answer=MSG_ACCOUNT_FETCH_FAILED,
                short_circuit=True,
                category=category,
                policy_decision=PolicyDecision.HANDOFF_NO_DATA,
            )
        return ChatResponse(
            answer=_format_me_answer(user),
            short_circuit=True,
            category=category,
            policy_decision=PolicyDecision.ANSWERED,
        )

    if category == QueryCategory.TRANSACTION_HISTORY:
        if not req.access_token:
            return ChatResponse(
                answer=MSG_SIGN_IN_FOR_TRANSACTIONS,
                short_circuit=True,
                category=category,
                policy_decision=PolicyDecision.DECLINED_AUTH_REQUIRED,
            )
        answer = _answer_from_transactions(req.question)
        if answer is None:
            return ChatResponse(
                answer=MSG_NO_TRANSACTIONS_FOUND,
                short_circuit=True,
                category=category,
                policy_decision=PolicyDecision.HANDOFF_NO_DATA,
            )
        return ChatResponse(
            answer=answer,
            short_circuit=True,
            category=category,
            policy_decision=PolicyDecision.ANSWERED,
        )

    if category == QueryCategory.OUT_OF_SCOPE:
        return ChatResponse(
            answer=MSG_OUT_OF_SCOPE,
            short_circuit=True,
            category=category,
            policy_decision=PolicyDecision.DECLINED_OUT_OF_SCOPE,
        )

    answer, citations, confidence = _answer_from_docs(req.question)
    policy_decision = (
        PolicyDecision.ANSWERED if citations else PolicyDecision.HANDOFF_NO_DATA
    )
    return ChatResponse(
        answer=answer,
        short_circuit=False,
        category=category,
        policy_decision=policy_decision,
        citations=citations,
        confidence=confidence,
    )
