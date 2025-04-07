import pprint
from typing import Annotated, Any, Iterator, List, TypedDict

import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from chat.vector_store import vector_store

load_dotenv()


@st.cache_resource
def init_chat_app(model_name, temperature: float | None = None) -> CompiledStateGraph:
    workflow = StateGraph(state_schema=MessagesState)
    model = ChatOpenAI(model_name=model_name, temperature=temperature)

    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query."""
        retrieved_docs = vector_store.similarity_search(query, k=8)
        serialized = "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
            for doc in retrieved_docs
        )
        return serialized, retrieved_docs

    # Step 1: query retrieval or respond directly
    def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_retrieval = model.bind_tools([retrieve])
        response = llm_with_retrieval.invoke(state["messages"])
        return {"messages": [response]}

    # Step 2: Execute the retrieval.
    tools = ToolNode([retrieve])

    def generate(state: MessagesState):
        """Generate answer."""
        # Get generated ToolMessages
        recent_tool_messages = []
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        tool_messages = recent_tool_messages[::-1]
        # Format into prompt
        docs_content = "\n\n".join(doc.content for doc in tool_messages)
        system_message_content = (
            "You are a helpful assistant, expert in reinforcement learning and meant for question-answering tasks."
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know."
            "\n\n"
            f"{docs_content}"
        )
        conversation_messages = [
            message
            for message in state["messages"]
            if message.type in ("human", "system")
            or (message.type == "ai" and not message.tool_calls)
        ]
        prompt = [SystemMessage(system_message_content)] + conversation_messages

        # Run
        response = model.invoke(prompt)
        return {"messages": [response]}

    # add chat model to graph
    workflow.add_node("query_or_respond", query_or_respond)
    workflow.add_node("tools", tools)
    workflow.add_node("generate", generate)

    workflow.set_entry_point("query_or_respond")
    workflow.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    workflow.add_edge("tools", "generate")
    workflow.add_edge("generate", END)

    # add in memory
    memory = MemorySaver()

    # compile graph
    workflow = workflow.compile(checkpointer=memory)

    return workflow


def stream_chat_response(stream: Iterator[dict[str, Any] | Any]):
    for chunk, metadata in stream:
        if isinstance(chunk, AIMessage):
            yield chunk.content


def query_workflow_stream(
    wf: CompiledStateGraph, query: str, thread_id: str
) -> Iterator[dict[str, Any] | Any]:
    config = {"configurable": {"thread_id": thread_id}}
    messages = [HumanMessage(query)]
    return wf.stream({"messages": messages}, config=config, stream_mode="messages")
