import streamlit as st

from helpers import stream_llm_response
from quiz_model import ask_question_stream, evaluate_answer_stream, init_quiz_app

st.set_page_config(
    page_title="Quiz",
    page_icon="assets/wizzard_penguin.ico",
    layout="wide",
)

quiz_app = init_quiz_app("gpt-4o-mini")


class QuizStages:
    quiz_question: str = "quiz_question"
    quiz_answer: str = "quiz_answer"
    quiz_evaluation: str = "quiz_evaluation"


styles = {
    QuizStages.quiz_question: None,
    QuizStages.quiz_answer: "blue",
    QuizStages.quiz_evaluation: None,
}


def render_static_component(component):
    if styles[component] is None:
        st.markdown(f"{st.session_state[component]}")
        return
    st.markdown(f":{styles[component]}[{st.session_state[component]}]")


# Each step is defined here
def question_stage():
    if QuizStages.quiz_question in st.session_state:
        render_static_component(QuizStages.quiz_question)
    else:
        full_question = st.write_stream(
            stream_llm_response(ask_question_stream(quiz_app))
        )
        st.session_state[QuizStages.quiz_question] = full_question


def answer_stage():
    if QuizStages.quiz_answer in st.session_state:
        render_static_component(QuizStages.quiz_answer)
    elif (
        QuizStages.quiz_answer not in st.session_state
        and QuizStages.quiz_evaluation not in st.session_state
    ):
        text_input_container = st.empty()
        answer = text_input_container.text_input("Your answer here", value=None)
        if answer is not None:
            text_input_container.empty()
            st.session_state[QuizStages.quiz_answer] = answer
            render_static_component(QuizStages.quiz_answer)


def evaluation_stage():
    if QuizStages.quiz_evaluation in st.session_state:
        render_static_component(QuizStages.quiz_evaluation)

    elif (
        QuizStages.quiz_question in st.session_state
        and QuizStages.quiz_answer in st.session_state
        and QuizStages.quiz_evaluation not in st.session_state
    ):
        evaluation = st.write_stream(
            stream_llm_response(
                evaluate_answer_stream(
                    quiz_app, st.session_state[QuizStages.quiz_answer]
                )
            )
        )
        st.session_state.quiz_evaluation = evaluation


def repeat_quiz_stage():
    if (
        QuizStages.quiz_question in st.session_state
        and QuizStages.quiz_answer in st.session_state
        and QuizStages.quiz_evaluation in st.session_state
    ):
        st.button("Repeat", key="repeat_quiz")
    if "repeat_quiz" in st.session_state and st.session_state["repeat_quiz"]:
        del st.session_state[QuizStages.quiz_question]
        del st.session_state[QuizStages.quiz_answer]
        del st.session_state[QuizStages.quiz_evaluation]
        st.rerun()


st.header("Its quiz time fella! 🧙")

# Quiz flow
question_stage()
answer_stage()
evaluation_stage()
repeat_quiz_stage()
