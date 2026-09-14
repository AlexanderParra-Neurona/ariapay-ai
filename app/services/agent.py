from custodia import trace_async
from langchain_core.messages import SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.constants import MSG_NO_DOCS_FOUND, TraceName
from app.services.llm import get_chat_model
from app.tools import get_tools

_SYSTEM_PROMPT = """You are Ariabot, Ariapay's assistant. Answer using the provided \
tools when the question needs FAQ/product info, the user's transactions, or the \
user's account details. If no tool result answers the question, say so concisely. \
Never invent transaction, account, or FAQ content that didn't come from a tool."""

_RECURSION_LIMIT = 8

def _build_graph(access_token: str | None):
    tools = get_tools(access_token)
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


@trace_async(name=TraceName.AGENT_LOOP.value)
async def run_agent(question: str, access_token: str | None = None) -> str:
    graph = _build_graph(access_token)
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"recursion_limit": _RECURSION_LIMIT},
    )
    final_message = result["messages"][-1]
    return final_message.content or MSG_NO_DOCS_FOUND
