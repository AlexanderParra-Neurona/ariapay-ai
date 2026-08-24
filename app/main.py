import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.logging_config import setup_logging
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError, get_me, login, verify_passcode
from app.services.classification import QueryCategory, get_query_classifier
from app.services.llm import get_llm_service
from app.services.retrieval import get_hybrid_retriever

setup_logging()
logger = logging.getLogger("ariabot.api")

app = FastAPI(title="ariabot")

OUT_OF_SCOPE_ANSWER = (
    "Sorry, I can't help with that. I can answer questions about Ariapay or your account balance and transactions."
)


class ChatRequest(BaseModel):
    question: str
    access_token: str | None = None


class ChatResponse(BaseModel):
    answer: str
    short_circuit: bool


class LoginRequest(BaseModel):
    phone_number: str
    country_code: str
    password: str
    passcode: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str


def _answer_from_docs(question: str) -> str:
    docs = get_hybrid_retriever().search(question)
    if not docs:
        return "Sorry, I don't have information on that."

    context_block = "\n\n".join(d.page_content for d in docs)
    prompt = (
        "Answer the question using only the context below. Be concise.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {question}\n\nAnswer:"
    )
    return get_llm_service().chat([{"role": "user", "content": prompt}])


def _format_me_answer(user: dict) -> str:
    cards = user.get("cards") or []
    card_lines = [f"- {c['card_network']} {c['number']} ({c['card_type']})" for c in cards]
    lines = [
        f"Name: {user['first_name']} {user['last_name']}",
        f"Email: {user['email']}",
        f"Phone: {user['country_code']}{user['phone_number']}",
    ]
    if card_lines:
        lines.append("Cards:")
        lines.extend(card_lines)
    return "\n".join(lines)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
async def auth_login(req: LoginRequest):
    logger.info("call=/auth/login phone=%s%s", req.country_code, req.phone_number)
    try:
        passcode_token = await login(req.phone_number, req.country_code, req.password)
        token = await verify_passcode(passcode_token, req.passcode)
    except AriapayAuthError as e:
        logger.warning("call=/auth/login result=auth_error detail=%s", e)
        raise HTTPException(status_code=401, detail=str(e))
    except AriapayAPIError as e:
        logger.error("call=/auth/login result=api_error detail=%s", e)
        raise HTTPException(status_code=502, detail=str(e))
    logger.info("call=/auth/login result=success")
    return LoginResponse(access_token=token["access_token"], refresh_token=token["refresh_token"])


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    logger.info("call=/chat question=%r authenticated=%s", req.question, bool(req.access_token))
    category = get_query_classifier().classify(req.question)
    logger.info("call=/chat category=%s", category.value)

    if category == QueryCategory.TRANSACTION_INQUIRY:
        if not req.access_token:
            logger.info("call=/chat result=unauthenticated")
            return ChatResponse(answer="Please sign in to view your account details.", short_circuit=True)
        try:
            user = await get_me(req.access_token)
        except AriapayAuthError:
            logger.warning("call=/chat result=session_expired")
            return ChatResponse(answer="Your session has expired. Please sign in again.", short_circuit=True)
        except AriapayAPIError as e:
            logger.error("call=/chat result=api_error detail=%s", e)
            return ChatResponse(answer="Sorry, I couldn't fetch your account details right now.", short_circuit=True)
        logger.info("call=/chat result=user_data_success")
        return ChatResponse(answer=_format_me_answer(user), short_circuit=True)

    if category == QueryCategory.OUT_OF_SCOPE:
        logger.info("call=/chat result=out_of_scope")
        return ChatResponse(answer=OUT_OF_SCOPE_ANSWER, short_circuit=True)

    answer = _answer_from_docs(req.question)
    logger.info("call=/chat result=doc_answer")
    return ChatResponse(answer=answer, short_circuit=False)
