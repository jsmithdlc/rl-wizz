"""
Interface to interact with chat model
"""

import logging
import sqlite3
from typing import Any, Iterator

import streamlit as st
from dotenv import load_dotenv
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors.chain_filter import LLMChainFilter
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from chat.db.database import save_conversation_title, update_chat_source_n_retrieved
from chat.vector_store import vector_store

load_dotenv()


BASE_SYSTEM_MSG = """
    You are a helpful assistant, whose purpose is to help in learning and exploring the
    area of reinforcement learning through question-answering tasks.

    Writing math formulas:
    You have a MathJax render environment.
    - Any LaTeX text between single dollar sign ($) will be rendered as a TeX formula;
    - Use $(tex_formula)$ in-line delimiters to display equations instead of backslash;
    - The render environment only uses $ (single dollarsign) as a container delimiter, never output $$.
    Example: $x^2 + 3x$ is output for "x² + 3x" to appear as TeX.

"""


def _parse_retrieved_into_context(retrieved_docs: list[Document]) -> str:
    meta_keys = {
        "category",
        "source",
        "languages",
        "page_number",
        "element_id",
        "parent_id",
        "filetype",
        "url",
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


def _update_source_retrieval_count(documents: list[Document]):
    """
    Increases the retrival count of retrieved sources

    Args:
        documents (list[Document]): retrieved documents
    """
    retrieved_sources: dict[str, any] = {}
    for doc in documents:
        source_name = doc.metadata.get("source") or doc.metadata.get("url")
        if source_name not in retrieved_sources:
            retrieved_sources[source_name] = 0
        retrieved_sources[source_name] += 1
    for source, retrieval_count in retrieved_sources.items():
        update_chat_source_n_retrieved(source, retrieval_count)


@st.cache_resource
def init_chat_app(
    model_name: str, temperature: float = 0.0, rag_n_docs: int = 5
) -> CompiledStateGraph:
    """Initialize chat LangGraph application

    Args:
        model_name (str): name of the OpenAI's LLM model to use
        temperature (float): temperature setting for the chat model.
        rag_n_docs (int): number of documents used during RAG. Defaults to 5.
        Defaults to None.

    Returns:
        CompiledStateGraph: chat LangGraph application
    """

    workflow = StateGraph(state_schema=MessagesState)
    model = ChatOpenAI(model_name=model_name, temperature=temperature)
    llm = OpenAI(temperature=0)

    _filter = LLMChainFilter.from_llm(llm)
    base_retriever = vector_store.as_retriever(
        search_kwargs={
            "k": rag_n_docs,
            "filter": {"detection_class_prob": {"$gte": 0.75}},
        }
    )
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=_filter, base_retriever=base_retriever
    )

    @tool(response_format="content_and_artifact")
    def retrieve(query: str):
        """Retrieve information related to a query"""
        logging.info("triggering document retrieval")
        retrieved_docs = compression_retriever.invoke(query)
        serialized = _parse_retrieved_into_context(retrieved_docs)
        _update_source_retrieval_count(retrieved_docs)
        return serialized, retrieved_docs

    tools = ToolNode([retrieve])

    def set_conversation_title(state: MessagesState, config: RunnableConfig):
        if not config["configurable"]["has_title"]:
            prompt = [
                SystemMessage(
                    f"""Based on user message, try to detect a conversation title
                with a meaningful topic (max 5 words). If not possible, simply return UNKNOWN

                Message is: {state["messages"]}"""
                )
            ]
            model.disable_streaming = True
            response = model.invoke(prompt)
            model.disable_streaming = False
            if response.content != "UNKNOWN":
                save_conversation_title(
                    config["configurable"]["thread_id"], response.content
                )

        return {"messages": state["messages"]}

    # Step 1: query retrieval or respond directly
    def query_or_respond(state: MessagesState):
        """Generate tool call for retrieval or respond."""
        llm_with_retrieval = model.bind_tools([retrieve])
        prompt = [SystemMessage(BASE_SYSTEM_MSG)] + state["messages"]
        response = llm_with_retrieval.invoke(prompt)
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
            f"{BASE_SYSTEM_MSG}"
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say politely that you "
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
    workflow.add_node("set_conversation_title", set_conversation_title)
    workflow.add_node("query_or_respond", query_or_respond)
    workflow.add_node("tools", tools)
    workflow.add_node("generate", generate)

    workflow.set_entry_point("set_conversation_title")
    workflow.add_edge("set_conversation_title", "query_or_respond")
    workflow.add_conditional_edges(
        "query_or_respond",
        tools_condition,
        {END: END, "tools": "tools"},
    )
    workflow.add_edge("tools", "generate")
    workflow.add_edge("generate", END)

    # add SQLite memory checkpoint
    conn = sqlite3.connect("data/conversations.db", check_same_thread=False)
    memory = SqliteSaver(conn)

    # compile graph
    workflow = workflow.compile(checkpointer=memory)

    return workflow


def chat_stream(
    wf: CompiledStateGraph, query: str, thread_id: str, has_title: bool
) -> Iterator[dict[str, Any] | Any]:
    """
    Trigger chat conversation stream
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
            "has_title": has_title,
        }
    }
    messages = [HumanMessage(query)]
    return wf.stream({"messages": messages}, config=config, stream_mode="messages")
