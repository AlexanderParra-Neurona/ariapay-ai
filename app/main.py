from fastapi import FastAPI
from pydantic import BaseModel

from app.redis_client import find_faq

app = FastAPI(title="ariabot")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    found: bool


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    match = await find_faq(req.question)
    if match is None:
        return ChatResponse(answer="Sorry, I don't have an answer for that yet.", found=False)
    return ChatResponse(answer=match["answer"], found=True)
