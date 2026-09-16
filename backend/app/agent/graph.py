from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage

from app.agent.state import ChatState
from app.llm.model import get_llm


llm = get_llm()


async def chatbot_node(state: ChatState):

    # print("\n========== CURRENT STATE ==========")

    # for message in state["messages"]:
    #     print(
    #         f"{type(message).__name__}: {message.content}"
    #     )

    # print("===================================\n")

    messages = [
        SystemMessage(
            content=(
                "You are LocalGPT, a helpful AI assistant. "
                "Use the conversation history to answer the user's questions. "
                "If the user provides personal information such as their name, "
                "use that information when relevant. "
                "Do not claim that you cannot access information that is "
                "clearly present in the conversation."
            )
        ),
        *state["messages"],
    ]

    response = await llm.ainvoke(messages)

    return {"messages": [response]}


def build_graph(checkpointer):
    builder = StateGraph(ChatState)

    builder.add_node("chatbot", chatbot_node)

    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)

    return builder.compile(
        checkpointer=checkpointer
    )