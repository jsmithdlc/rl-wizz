"""
Project-wise utilities
"""

from typing import Any, Iterator

from langchain_core.messages import AIMessage


def stream_llm_response(stream: Iterator[dict[str, Any] | Any]):
    """
    Yield content of `AIMessage type messages from stream
    """
    for chunk, _ in stream:
        if isinstance(chunk, AIMessage):
            yield chunk.content
