from typing import Any, Iterator

import langchain
import langchain.chat_models
import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph

load_dotenv()


@st.cache_resource
def init_chat_app(model_name) -> CompiledStateGraph:
    workflow = StateGraph(state_schema=MessagesState)

    prompt_template = ChatPromptTemplate(
        [
            (
                "system",
                (
                    "You are a helpful assistant, expert in reinforcement learning. Respond the question "
                    "to the best of your abilities. If you don't know the answer, say you don't know. "
                ),
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    model = ChatOpenAI(model_name=model_name)

    def call_model(state):
        prompt = prompt_template.invoke(state)
        response = model.invoke(prompt)
        return {"messages": response}

    # add chat model to graph
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model)

    # add in memory
    memory = MemorySaver()

    # compile graph
    workflow = workflow.compile(checkpointer=memory)

    return workflow


def stream_llm_response(stream: Iterator[dict[str, Any] | Any]):
    for chunk, metadata in stream:
        if isinstance(chunk, AIMessage):
            yield chunk.content


def query_workflow_stream(
    wf: CompiledStateGraph, query: str, thread_id: str
) -> Iterator[dict[str, Any] | Any]:
    config = {"configurable": {"thread_id": thread_id}}
    input_messages = [HumanMessage(query)]
    return wf.stream(
        {"messages": input_messages}, config=config, stream_mode="messages"
    )
