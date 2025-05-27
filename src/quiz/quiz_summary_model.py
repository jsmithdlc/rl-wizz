import json
import os
from datetime import datetime
from typing import Literal

import streamlit as st
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field

from database.database import fetch_past_questions


class QuizSummaryFormatter(BaseModel):
    """Always use this tool to format the summary of the quiz results."""

    overall_performance: Literal["Bad", "Average", "Good"] = Field(
        description="Overall assesment of the user performance with respect to their answers to quiz questions"
    )
    areas_improvement: list[str] = Field(
        description="Reinforcement learning topics (one or two words) that should be foritified to improve user performance on quiz."
    )
    suggestion: str = Field(
        description="A thorough suggestion of what areas can be improved."
    )


class QuizSummary(QuizSummaryFormatter):
    date: str
    n_correct_questions: int
    n_incorrect_questions: int


@st.cache_resource
def init_quiz_summary_wf(model_name: str) -> CompiledStateGraph:
    wf = StateGraph(state_schema=MessagesState)
    model = ChatOpenAI(model_name=model_name)

    model = model.with_structured_output(QuizSummaryFormatter)

    def generate_summary(state: MessagesState):
        """
        Generate a summary evaluation of answers to reinforcement learning questions
        """

        solved_quizzes = []
        unsolved_quizzes = []
        for q in fetch_past_questions():
            if q.solved:
                solved_quizzes.append(q.question)
                continue
            unsolved_quizzes.append(q.question)

        prompt = (
            "Your goal is to evaluate different answers to questions about reinforcement learning.",
            f"The questions that were note solved are the following: {'\n'.join(unsolved_quizzes)}"
            f"And the questions that were correctly solved are: {'\n'.join(solved_quizzes)}",
        )
        result = model.invoke(prompt)
        summary = QuizSummary(
            date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            n_correct_questions=len(solved_quizzes),
            n_incorrect_questions=len(unsolved_quizzes),
            **result.model_dump(),
        )
        return summary

    def save_summary(state: QuizSummary):
        json_path = "data/quiz_ai_summaries.json"
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as file:
                summaries = json.load(file)
        else:
            summaries = []
        state_dict = state.model_dump()
        summaries.append(state_dict)
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(summaries, file, indent=4)
        return state

    wf.add_node("generate_summary", generate_summary)
    wf.add_node("save_summary", save_summary)

    wf.add_edge(START, "generate_summary")
    wf.add_edge("generate_summary", "save_summary")

    wf = wf.compile()
    return wf
