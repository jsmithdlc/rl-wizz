"""
Interface to interact with chat model
"""

from typing import Any, Iterator

import streamlit as st
from dotenv import load_dotenv
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.chain_filter import LLMChainFilter
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from chat.vector_store import vector_store

load_dotenv()


def _parse_retrieved_into_context(retrieved_docs: list[Document]) -> str:
    meta_keys = {
        "category",
        "source",
        "languages",
        "page_number",
        "element_id",
        "parent_id",
        "filetype",
    }
    docs_strs = []
    for doc in retrieved_docs:
        filtered_meta = " ; ".join(
            [f"{k}: {val}" for k, val in doc.metadata.items() if k in meta_keys]
        )
        docs_strs.append(
            (f"Source: ({filtered_meta})\n" f"Content: {doc.page_content}")
        )
    return "\n\n".join(docs_strs)


@st.cache_resource
def init_chat_app(
    model_name: str, temperature: float | None = None
) -> CompiledStateGraph:
    """Initialize chat LangGraph application

    Args:
        model_name (str): name of the OpenAI's LLM model to use
        temperature (float | None, optional): temperature setting for the chat model.
        Defaults to None.

    Returns:
        CompiledStateGraph: chat LangGraph application
    """
    workflow = StateGraph(state_schema=MessagesState)
    model = ChatOpenAI(model_name=model_name, temperature=temperature)
    llm = OpenAI(temperature=0)

    _filter = LLMChainFilter.from_llm(llm)
    base_retriever = vector_store.as_retriever(
        search_kwargs={"k": 5, "filter": {"detection_class_prob": {"$gte": 0.75}}}
    )
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=_filter, base_retriever=base_retriever
    )

    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query"""
        retrieved_docs = compression_retriever.invoke(query)
        serialized = _parse_retrieved_into_context(retrieved_docs)
        return serialized, retrieved_docs

    tools = ToolNode([retrieve])

    # Step 1: query retrieval or respond directly
    def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_retrieval = model.bind_tools([retrieve])
        response = llm_with_retrieval.invoke(state["messages"])
        return {"messages": [response]}

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
            "You are a helpful assistant, "
            "expert in reinforcement learning and meant for question-answering tasks."
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


def chat_stream(
    wf: CompiledStateGraph, query: str, thread_id: str
) -> Iterator[dict[str, Any] | Any]:
    """
    Trigger chat conversation stream
    """
    config = {"configurable": {"thread_id": thread_id}}
    messages = [HumanMessage(query)]
    return wf.stream({"messages": messages}, config=config, stream_mode="messages")
