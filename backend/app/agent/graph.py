from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.state import ChatState
from app.llm.model import get_llm
from app.tools import TOOLS


llm = get_llm()

llm_with_tools = llm.bind_tools(TOOLS)


SYSTEM_PROMPT = """
You are LocalGPT, a helpful AI assistant.

Use the conversation history to answer the user's questions.

You have access to tools.

Important tool usage rules:

1. Use the calculator tool for exact mathematical calculations.
2. Use the date/time tool when the user asks for the current date or time.
3. Do not invent tool results.
4. If a tool is available and appropriate for the user's request, use it.
5. After receiving a tool result, use that result to answer the user naturally.
6. Do not mention internal tool names unless the user asks about them.
7. If a tool returns an error, explain the problem clearly instead of inventing an answer.
8. If the answer is already clearly available from the conversation, do not unnecessarily use a tool.
9. If the user provides personal information such as their name, use that information when relevant.
10. Do not claim that you cannot access information that is clearly present in the conversation.
"""


async def chatbot_node(state: ChatState):
    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
        ),
        *state["messages"],
    ]

    response = await llm_with_tools.ainvoke(messages)

    return {
        "messages": [response]
    }


def build_graph(checkpointer):
    builder = StateGraph(ChatState)

    # Main LLM node
    builder.add_node(
        "chatbot",
        chatbot_node,
    )

    # Tool execution node
    builder.add_node(
        "tools",
        ToolNode(TOOLS),
    )

    # Start with the LLM
    builder.add_edge(
        START,
        "chatbot",
    )

    # After the LLM:
    #
    # - If no tool call -> END
    # - If tool call -> tools
    builder.add_conditional_edges(
        "chatbot",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    # After executing a tool,
    # send the result back to the LLM.
    builder.add_edge(
        "tools",
        "chatbot",
    )

    return builder.compile(
        checkpointer=checkpointer
    )