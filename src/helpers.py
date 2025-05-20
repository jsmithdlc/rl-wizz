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
