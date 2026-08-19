import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.logging_config import setup_logging
from app.services.ariapay_service import AriapayAPIError, AriapayAuthError, get_me, login, verify_passcode
from app.services.ollama_service import embed
from app.services.redis_service import find_similar_faq

setup_logging()
logger = logging.getLogger("ariabot.api")

app = FastAPI(title="ariabot")

USER_DATA_KEYWORDS = (
    "my profile",
    "my account",
    "my card",
    "my cards",
    "my balance",
    "my email",
    "my phone number",
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


def _is_user_data_question(question: str) -> bool:
    lowered = question.lower()
    return any(keyword in lowered for keyword in USER_DATA_KEYWORDS)


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
    if _is_user_data_question(req.question):
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

    vector = await embed(req.question)
    match = await find_similar_faq(vector)
    if match is not None:
        logger.info("call=/chat result=faq_match")
        return ChatResponse(answer=match["answer"], short_circuit=True)
    logger.info("call=/chat result=no_match")
    return ChatResponse(answer="Sorry, I don't have an answer for that yet.", short_circuit=False)
