"""
Tool calling agent : the LLM decides which tools of tools.py to call, LangGraph runs them.

Graph : START -> agent -> (tools -> agent)* -> END
"""

import os
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from chat import CATEGORIES
from tools import TOOLS

MAX_STEPS = 15

SYSTEM_PROMPT = f"""You are a recruiting assistant connected to a database of CVs.
Always use the tools to find candidates, never invent a candidate or a fact about a candidate.

- search_candidates : find profiles. Use the category and min_years filters when the request is clear.
- get_candidate_details : read a CV before answering a detailed question (a tool, a degree, a company...).
- compare_candidates : compare or rank several candidates on the required skills.
- list_categories : know what is in the database.

Database categories : {", ".join(CATEGORIES)}

Cite every candidate you talk about with its file name in square brackets, like [10554236.pdf].
If no candidate matches the request, say it clearly."""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="openai/gpt-oss-20b",
    temperature=0,
)
llm_with_tools = llm.bind_tools(TOOLS)


def call_model(state):
    response = llm_with_tools.invoke([SystemMessage(SYSTEM_PROMPT)] + state["messages"])
    return {"messages": [response]}


graph = StateGraph(AgentState)
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode(TOOLS))

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

agent_graph = graph.compile()


def to_message(message):
    return HumanMessage(message["content"]) if message["role"] == "user" else AIMessage(message["content"])


def ask_agent(question, history=None):
    """Run the agent on a question.

    history : previous turns as [{"role": "user" | "assistant", "content": "..."}]
    returns : {"answer", "sources", "tool_calls"}
    """
    messages = [to_message(message) for message in history or []] + [HumanMessage(question)]
    result = agent_graph.invoke({"messages": messages}, {"recursion_limit": MAX_STEPS})
    new_messages = result["messages"][len(messages):]

    tool_calls = [
        {"name": call["name"], "args": call["args"]}
        for message in new_messages if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]

    # every CV returned by a tool is a potential source, duplicates are removed
    sources = {}
    for message in new_messages:
        if isinstance(message, ToolMessage) and message.artifact:
            for source in message.artifact:
                sources.setdefault(source["file_name"], source)

    return {"answer": new_messages[-1].content, "sources": list(sources.values()), "tool_calls": tool_calls}


if __name__ == "__main__":
    print("CV Screening Agent (tool calling)")
    print("Try: compare the 2 best accountants who know QuickBooks")
    print("/bye to quit\n")

    history = []
    while True:
        question = input("Ask something : ")
        if question.lower() in ["/quit", "/bye"]:
            print("Exiting the program.")
            break

        result = ask_agent(question, history)
        for call in result["tool_calls"]:
            print(f"  -> {call['name']}({call['args']})")
        print("AI : ", result["answer"], "\n")
        history += [{"role": "user", "content": question}, {"role": "assistant", "content": result["answer"]}]
