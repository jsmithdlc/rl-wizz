from typing import Any, Iterator

from langchain_core.messages import AIMessage


def stream_llm_response(stream: Iterator[dict[str, Any] | Any]):
    for chunk, metadata in stream:
        if isinstance(chunk, AIMessage):
            yield chunk.content
