from fastapi import FastAPI
from pydantic import BaseModel

from app.services.ariapay_service import AriapayAPIError, AriapayAuthError, get_me
from app.services.ollama_service import embed
from app.services.redis_service import find_similar_faq

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


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if _is_user_data_question(req.question):
        if not req.access_token:
            return ChatResponse(answer="Please sign in to view your account details.", short_circuit=True)
        try:
            user = await get_me(req.access_token)
        except AriapayAuthError:
            return ChatResponse(answer="Your session has expired. Please sign in again.", short_circuit=True)
        except AriapayAPIError:
            return ChatResponse(answer="Sorry, I couldn't fetch your account details right now.", short_circuit=True)
        return ChatResponse(answer=_format_me_answer(user), short_circuit=True)

    vector = await embed(req.question)
    match = await find_similar_faq(vector)
    if match is not None:
        return ChatResponse(answer=match["answer"], short_circuit=True)
    return ChatResponse(answer="Sorry, I don't have an answer for that yet.", short_circuit=False)
