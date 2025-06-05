import json
import os

import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from quiz.db import PastQuestion, fetch_past_questions
from quiz.quiz_summary_model import QuizSummary, init_quiz_summary_wf

# Display data
st.header("Past Questions")

N_QUESTIONS_SHOWN = 10

# Past questions table
past_questions = fetch_past_questions()
past_questions = sorted(past_questions, key=lambda q: q.date, reverse=True)
labels = [
    (i, min(i + N_QUESTIONS_SHOWN, len(past_questions)))
    for i in range(0, len(past_questions), N_QUESTIONS_SHOWN)
]

if "question_selections" not in st.session_state:
    st.session_state.question_selections = [
        0,
        min(len(past_questions), N_QUESTIONS_SHOWN),
    ]


def format_question_selector(label: tuple[int, int]) -> str:
    """Format question selector (from, to) into displayed text from-to

    Args:
        label (tuple[int, int]): ids from question to question

    Returns:
        str: how selector is displayed
    """
    return f"{label[0]} - {label[1]}"


@st.dialog("Past Quiz", width="large")
def on_select_past_question(question: PastQuestion):
    """Display answer and feedback when past question is selected

    Args:
        question (PastQuestion): past question
    """
    cont = st.container(border=True)
    cont.write(f"*{question.question}*")
    st.subheader(":speech_balloon: User's Answer")
    st.write(f":blue[{question.answer}]")
    st.subheader(":table_tennis_paddle_and_ball: Feedback")
    st.write(question.feedback)


def on_select_question_range(selection_range: tuple[int, int]):
    """
    Set selected past questions
    """
    st.session_state.question_selections = selection_range


for i in range(
    st.session_state.question_selections[0], st.session_state.question_selections[1]
):
    past_question = past_questions[i]
    with stylable_container(
        key=f"question_{i}",
        css_styles="""
        button{
            text-align: left;
        }
        """,
    ):
        passed_text = (
            ":green-background[Passed]"
            if past_question.solved
            else ":red-background[Failed]"
        )
        st.button(
            label=(
                f"{past_question.question} "
                f":blue-background[{past_question.date.strftime('%Y-%m-%d')}] "
                f"{passed_text}"
            ),
            type="tertiary",
            on_click=on_select_past_question,
            args=[past_question],
        )
col1, _ = st.columns((0.15, 0.85))
col1.selectbox(
    " ",
    options=labels,
    format_func=format_question_selector,
    on_change=on_select_question_range,
)


### QUIZ EVALUATION SECTION
st.header("AI Evaluation Reports")
st.markdown(
    (
        "*The following summaries are provided by AI with respect to answers to quiz questions.*"
    )
)

PERFORMANCE_TO_ICON = {"Bad": "😔", "Average": "🙂", "Good": "🥳"}


def load_quiz_summaries() -> list[QuizSummary]:
    summaries_path = "data/quiz_ai_summaries.json"
    if not os.path.exists(summaries_path):
        return []
    with open(summaries_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    data_models = [QuizSummary(**summ) for summ in data]
    return data_models


def display_quiz_summaries(summaries: list[QuizSummary]):
    for summary in summaries[::-1]:
        section = st.expander(
            label=f"Evaluation report on {summary.date}",
            icon=PERFORMANCE_TO_ICON[summary.overall_performance],
        )
        improvement_topics = " ".join(
            f":orange-badge[{area}]" for area in summary.areas_improvement
        )
        met1, met2 = section.columns(2)
        met1.metric(
            ":green[Correct Answers]",
            summary.n_correct_questions,
        )
        met2.metric(":red[Incorrect answers]", summary.n_incorrect_questions)

        section.markdown(
            f"""
            ##### Areas to improve
            {improvement_topics}

            ##### Suggestions
            {summary.suggestion}
            """
        )


summaries = load_quiz_summaries()
display_quiz_summaries(summaries)

gen_new_container = st.empty()
if len(past_questions) == 0:
    st.info("No past questions available to run evaluation")
    st.stop()
gen_new = gen_new_container.button("New AI Evaluation")
if gen_new:
    gen_new_container.empty()
    status = st.status("Generating evaluation report ...")
    quiz_summary_wf = init_quiz_summary_wf("gpt-4o-mini")
    result = quiz_summary_wf.invoke({})
    status.update(label="Report generated", state="complete")
    st.rerun()
