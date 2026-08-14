from fastapi import FastAPI
from pydantic import BaseModel

from app.services.ollama_service import embed
from app.services.redis_service import find_similar_faq

app = FastAPI(title="ariabot")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    short_circuit: bool


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    vector = await embed(req.question)
    match = await find_similar_faq(vector)
    if match is not None:
        return ChatResponse(answer=match["answer"], short_circuit=True)
    return ChatResponse(answer="Sorry, I don't have an answer for that yet.", short_circuit=False)
