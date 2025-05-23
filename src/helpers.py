"""
Project-wise utilities
"""

from typing import Any, Iterator

import streamlit as st
from langchain_core.messages import AIMessage, AIMessageChunk


def _check_if_doing_retrieval(chunk: AIMessageChunk) -> bool:
    """Checks if chunk informs of document retrieval

    Args:
        chunk (AIMessageChunk): AI message from llm stream

    Returns:
        bool: True if it corresponds to retrieval
    """
    tool_calls = chunk.tool_calls
    for call in tool_calls:
        if call["name"] == "retrieve":
            return True
    return False


def stream_llm_response_with_status(
    stream: Iterator[dict[str, Any] | Any], status_message: str
):
    """
    Yield content of LLM stream, with a status bar before any word is generated
    """
    container = st.empty()
    with container.status(status_message) as stat:
        first_word = None
        for chunk, _ in stream:
            if isinstance(chunk, AIMessage):
                if _check_if_doing_retrieval(chunk):
                    stat.update(expanded=True)
                    stat.write("Searching knowledge base ...")
                elif len(chunk.content.strip()) != 0:
                    first_word = chunk.content
                    break
                yield chunk.content
    container.empty()
    yield first_word
    yield from stream_llm_response(stream)


def stream_llm_response(stream: Iterator[dict[str, Any] | Any]):
    """
    Yield content of LLM stream
    """
    for chunk, _ in stream:
        if isinstance(chunk, AIMessage):
            yield chunk.content


def sqlalchemy_model_to_dict(model) -> dict[str, Any]:
    """Transforms SQLAlchemt Model into dictionary representation

    Args:
        model: SQLAlchemy model

    Returns:
        dict[str, Any]: dictionary representation
    """
    dict_rep = model.__dict__
    del dict_rep["_sa_instance_state"]
    return dict_rep
