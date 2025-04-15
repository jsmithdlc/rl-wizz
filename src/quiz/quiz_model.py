"""
Interface to interact with the Quiz application
"""

from typing import Any, Iterator

import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict

from database.database import add_question, fetch_past_questions

load_dotenv()

DATE_FORMAT = "%d/%m/%Y"


class QuizState(TypedDict):
    """Quiz data"""

    question: str | None = None
    answer: str | None = None
    model_evaluation: str | None = None
    solved: bool | None = None


# TODO: make quiz bot consider past-interactions and success/failure in answering these.
# and adjust difficulty of question based on answers to these
@st.cache_resource
def init_quiz_app(model_name: str) -> CompiledStateGraph:
    """Initialized a LangGraph app for quizzing user

    Args:
        model_name (str): LLM model name to use for the quiz

    Returns:
        CompiledStateGraph: LangGraph quiz app
    """

    workflow = StateGraph(state_schema=MessagesState)

    model = ChatOpenAI(model_name=model_name)

    def ask_question(state: QuizState):
        """Random question to ask user"""
        solved_quizzes = []
        unsolved_quizzes = []
        for q in fetch_past_questions():
            date_str = q.date.strftime(DATE_FORMAT)
            q_str = f"[{date_str}] " + q.question
            if q.solved:
                solved_quizzes.append(q_str)
                continue
            unsolved_quizzes.append(q_str)
        prompt = f"""
            You are a helpful quizz-maker with the goal of teaching reinforcement learning.
            Be gentle when interacting with user.

            Randomly choose a question to test his/her reinforcement learning knowledge. The question can be any of the types
            listed below:

            - Conceptual
            - Multiple choice
            - Understanding of a piece of code

            When choosing the topic, structure and difficulty for the new question, try to avoid repeating past
            questions answered correctly as specified by the following list (format: [date] question):

            {" ; ".join(solved_quizzes)}

            And consider the following list of questions not answered correctly:

            {" ; ".join(unsolved_quizzes)}

            Your response should just contain the question.
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
        and the user's answer: '{state["answer"]}', provide in your evaluation:

        - An initial "Correct" text if question properly answered.
        - Congratulations to user if correct. Be effusive in congratulations and consider using emojis.
        - Brief explanation of why the answer is right or wrong. Be more detailed when answer is wrong.
        """
        model_evaluation = model.invoke(prompt)
        return {
            "model_evaluation": model_evaluation.content,
            "solved": (
                True
                if "correct" in model_evaluation.content[:10].strip().lower()
                else False
            ),
        }

    def save_question_in_database(state: QuizState):
        add_question(state["question"], state["solved"])

    workflow.add_node("ask_question", ask_question)
    workflow.add_node("human_answer", human_answer)
    workflow.add_node("evaluation", evaluation)
    workflow.add_node("save_quiz", save_question_in_database)

    workflow.add_edge(START, "ask_question")
    workflow.add_edge("ask_question", "human_answer")
    workflow.add_edge("human_answer", "evaluation")
    workflow.add_edge("evaluation", "save_quiz")

    # checkpoint
    memory = MemorySaver()

    # compile graph
    workflow = workflow.compile(checkpointer=memory)

    return workflow


def ask_question_stream(wf: CompiledStateGraph) -> Iterator[dict[str, Any] | Any]:
    """
    Stream question formulation
    """
    config = {"configurable": {"thread_id": "quizzer"}}
    return wf.stream(QuizState(), config=config, stream_mode="messages")


def evaluate_answer_stream(
    wf: CompiledStateGraph, answer: str
) -> Iterator[dict[str, Any] | Any]:
    """
    Stream quiz evaluation and explanation
    """
    config = {"configurable": {"thread_id": "quizzer"}}
    return wf.stream(Command(resume=answer), config=config, stream_mode="messages")
