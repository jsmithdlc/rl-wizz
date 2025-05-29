"""
Streamlit page for an interactive quiz application that
generates questions and evaluates answers using LLM.
"""

import streamlit as st

from helpers import stream_llm_response_with_status
from quiz.quiz_model import ask_question_stream, evaluate_answer_stream, init_quiz_app

quiz_app = init_quiz_app("gpt-4o-mini")


class QuizStageNames:
    """
    Static class for handling at which state is currently the quiz at
    """

    quiz_question: str = "quiz_question"
    quiz_answer: str = "quiz_answer"
    quiz_evaluation: str = "quiz_evaluation"


styles = {
    QuizStageNames.quiz_question: None,
    QuizStageNames.quiz_answer: "blue",
    QuizStageNames.quiz_evaluation: None,
}


def render_stored_component(component: str):
    """Renders a component that is stored in session state

    Args:
        component (str): static component to render
    """
    if styles[component] is None:
        st.markdown(f"{st.session_state[component]}")
        return
    st.markdown(f":{styles[component]}[{st.session_state[component]}]")


# Each step is defined here
def question_stage():
    """
    Logic to handle starting the quiz with a question
    """
    if QuizStageNames.quiz_question in st.session_state:
        render_stored_component(QuizStageNames.quiz_question)
    else:
        full_question = st.write_stream(
            stream_llm_response_with_status(
                ask_question_stream(quiz_app), "Generating quiz question ..."
            )
        )
        st.session_state[QuizStageNames.quiz_question] = full_question


def answer_stage():
    """
    Logic to input the user answer into the quiz
    """
    if QuizStageNames.quiz_answer in st.session_state:
        render_stored_component(QuizStageNames.quiz_answer)
    elif (
        QuizStageNames.quiz_answer not in st.session_state
        and QuizStageNames.quiz_evaluation not in st.session_state
    ):
        text_input_container = st.empty()
        answer = text_input_container.text_area("Your answer here", value=None)
        if answer is not None:
            answer = answer.replace("\n", "     ")
            text_input_container.empty()
            st.session_state[QuizStageNames.quiz_answer] = answer
            render_stored_component(QuizStageNames.quiz_answer)


def evaluation_stage():
    """
    Logic to evaluate user answer
    """

    if QuizStageNames.quiz_evaluation in st.session_state:
        render_stored_component(QuizStageNames.quiz_evaluation)

    elif (
        QuizStageNames.quiz_question in st.session_state
        and QuizStageNames.quiz_answer in st.session_state
        and QuizStageNames.quiz_evaluation not in st.session_state
    ):
        evaluation = st.write_stream(
            stream_llm_response_with_status(
                evaluate_answer_stream(
                    quiz_app, st.session_state[QuizStageNames.quiz_answer]
                ),
                "Evaluating your answer ...",
            )
        )
        st.session_state.quiz_evaluation = evaluation


def repeat_quiz_stage():
    """
    Logic to reset quiz
    """

    if (
        QuizStageNames.quiz_question in st.session_state
        and QuizStageNames.quiz_answer in st.session_state
        and QuizStageNames.quiz_evaluation in st.session_state
    ):
        st.button("Next Question", key="repeat_quiz")
    if "repeat_quiz" in st.session_state and st.session_state["repeat_quiz"]:
        del st.session_state[QuizStageNames.quiz_question]
        del st.session_state[QuizStageNames.quiz_answer]
        del st.session_state[QuizStageNames.quiz_evaluation]
        st.rerun()


st.header("Its quiz time fella! 🧙")

# Quiz flow
question_stage()
answer_stage()
evaluation_stage()
repeat_quiz_stage()
