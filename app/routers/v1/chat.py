from fastapi import APIRouter

from app.constants import (
    MSG_OUT_OF_SCOPE,
    MSG_SIGN_IN_FOR_ACCOUNT,
    MSG_SIGN_IN_FOR_TRANSACTIONS,
)
from app.schemas import ChatRequest, ChatResponse, PolicyDecision
from app.services.agent import run_agent
from app.services.classification import QueryCategory, get_query_classifier

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    category = get_query_classifier().classify(req.question)

    if category == QueryCategory.OUT_OF_SCOPE:
        return ChatResponse(
            answer=MSG_OUT_OF_SCOPE,
            short_circuit=True,
            category=category,
            policy_decision=PolicyDecision.DECLINED_OUT_OF_SCOPE,
        )

    if category == QueryCategory.ACCOUNT_PROFILE and not req.access_token:
        return ChatResponse(
            answer=MSG_SIGN_IN_FOR_ACCOUNT,
            short_circuit=True,
            category=category,
            policy_decision=PolicyDecision.DECLINED_AUTH_REQUIRED,
        )

    if category == QueryCategory.TRANSACTION_HISTORY and not req.access_token:
        return ChatResponse(
            answer=MSG_SIGN_IN_FOR_TRANSACTIONS,
            short_circuit=True,
            category=category,
            policy_decision=PolicyDecision.DECLINED_AUTH_REQUIRED,
        )

    answer, no_data_found = await run_agent(req.question, access_token=req.access_token)
    policy_decision = (
        PolicyDecision.HANDOFF_NO_DATA if no_data_found else PolicyDecision.ANSWERED
    )
    return ChatResponse(
        answer=answer,
        short_circuit=False,
        category=category,
        policy_decision=policy_decision,
    )
