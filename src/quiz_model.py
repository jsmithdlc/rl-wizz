from typing import Any, Iterator

import langchain.chat_models
import streamlit as st
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel
from typing_extensions import TypedDict

load_dotenv()


class QuizState(TypedDict):
    question: str | None = None
    answer: str | None = None
    model_evaluation: str | None = None


# TODO: make quiz bot consider past-interactions and success/failure in answering these.
# and adjust difficulty of question based on answers to these
@st.cache_resource
def init_quiz_app(model_name) -> CompiledStateGraph:
    workflow = StateGraph(state_schema=MessagesState)

    model = ChatOpenAI(model_name=model_name)

    def ask_question(state: QuizState):
        """Random question to ask user"""
        prompt = """
            You are a helpful quizz-maker with the goal of teaching reinforcement learning.
            Be gentle when interacting with user.

            Ask the human a random engaging question to test his/her reinforcement learning knowledge. This can be any of:
            - Conceptual
            - Multiple choice

            Response should just contain question.
        """
        question = model.invoke(prompt)
        return {"question": question.content}

    def human_answer(state: QuizState):
        """Human answer to previously asked question"""
        answer = interrupt("Please provide answer ... ")
        return {"answer": answer}

    def evaluation(state: QuizState):
        """Evaluation of answer provided by user"""
        prompt = f"""
        You are quizzing a user who is trying to learn so you should use second-person and be
        sympathetic while not condescending. Try to be funny if possible

        Given the question: '{state["question"]}'
        and the user's answer: '{state["answer"]}', provide:

        - Congratulations to user if correct. Be effusive in congratulations and consider using emojis.
        - Brief explanation of why the answer is right or wrong. Be more detailed when answer is wrong
        """

        evaluation = model.invoke(prompt)
        return {"model_evaluation": evaluation}

    workflow.add_node("ask_question", ask_question)
    workflow.add_node("human_answer", human_answer)
    workflow.add_node("evaluation", evaluation)

    workflow.add_edge(START, "ask_question")
    workflow.add_edge("ask_question", "human_answer")
    workflow.add_edge("human_answer", "evaluation")

    # checkpoint
    memory = MemorySaver()

    # compile graph
    workflow = workflow.compile(checkpointer=memory)

    return workflow


def ask_question_stream(wf: CompiledStateGraph) -> Iterator[dict[str, Any] | Any]:
    config = {"configurable": {"thread_id": "quizzer"}}
    return wf.stream(QuizState(), config=config, stream_mode="messages")


def evaluate_answer_stream(
    wf: CompiledStateGraph, answer: str
) -> Iterator[dict[str, Any] | Any]:
    config = {"configurable": {"thread_id": "quizzer"}}
    return wf.stream(Command(resume=answer), config=config, stream_mode="messages")
