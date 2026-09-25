import logging
from functools import lru_cache

from langchain_core.messages import SystemMessage, ToolMessage
from langfuse.langchain import CallbackHandler
from langgraph.errors import GraphRecursionError
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.constants import (
    MSG_ACCOUNT_FETCH_FAILED,
    MSG_AGENT_NO_ANSWER,
    MSG_AGENT_TOO_COMPLEX,
    MSG_NO_DOCS_FOUND,
    MSG_NO_TRANSACTIONS_FOUND,
    MSG_SESSION_EXPIRED,
    TraceName,
)
from app.services.llm import get_chat_model
from app.tools import get_tools
from app.tracing import trace_async

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are Ariabot, Ariapay's assistant. Answer using the provided \
tools when the question needs FAQ/product info, the user's transactions, or the \
user's account details. If no tool result answers the question, say so concisely. \
Never invent transaction, account, or FAQ content that didn't come from a tool."""

_RECURSION_LIMIT = 8

_NO_DATA_TOOL_MESSAGES = {MSG_NO_DOCS_FOUND, MSG_NO_TRANSACTIONS_FOUND}
_AUTH_LOST_TOOL_MESSAGES = {MSG_SESSION_EXPIRED, MSG_ACCOUNT_FETCH_FAILED}

_langfuse_handler = CallbackHandler()


@lru_cache(maxsize=2)
def _build_graph(signed_in: bool):
    """Build the agent graph for one of exactly two tool sets (signed in or not).

    Token-agnostic: the actual `access_token` is threaded per-invocation via
    `RunnableConfig` (see `run_agent`), never baked into the graph, so this
    cache is bounded by `signed_in` and never grows with distinct tokens/users.
    """
    tools = get_tools(signed_in)
    model = get_chat_model().bind_tools(tools)

    def call_model(state: MessagesState) -> dict:
        response = model.invoke(
            [SystemMessage(content=_SYSTEM_PROMPT), *state["messages"]]
        )
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


def _found_no_data(messages: list) -> bool:
    return any(
        isinstance(m, ToolMessage)
        and (
            m.content in _NO_DATA_TOOL_MESSAGES or m.content in _AUTH_LOST_TOOL_MESSAGES
        )
        for m in messages
    )


@trace_async(name=TraceName.AGENT_LOOP.value)
async def run_agent(question: str, access_token: str | None = None) -> tuple[str, bool]:
    graph = _build_graph(signed_in=bool(access_token))
    try:
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": question}]},
            config={
                "recursion_limit": _RECURSION_LIMIT,
                "configurable": {"access_token": access_token},
                "callbacks": [_langfuse_handler],
            },
        )
    except GraphRecursionError:
        logger.warning("run_agent: hit recursion limit for question=%r", question)
        return MSG_AGENT_TOO_COMPLEX, True

    messages = result["messages"]
    final_message = messages[-1]
    no_data_found = _found_no_data(messages)
    answer = final_message.content or MSG_AGENT_NO_ANSWER
    return answer, no_data_found
