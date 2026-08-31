from enum import Enum

from pydantic import BaseModel

from app.services.classification import QueryCategory


class PolicyDecision(str, Enum):
    ANSWERED = "answered"
    DECLINED_OUT_OF_SCOPE = "declined_out_of_scope"
    DECLINED_AUTH_REQUIRED = "declined_auth_required"
    HANDOFF_NO_DATA = "handoff_no_data"


class ChatRequest(BaseModel):
    question: str
    access_token: str | None = None


class Citation(BaseModel):
    source: str
    heading: str


class ChatResponse(BaseModel):
    answer: str
    short_circuit: bool
    category: QueryCategory
    policy_decision: PolicyDecision
    citations: list[Citation] = []
    confidence: float | None = None
