import json
import os
from typing import Any

import pandas as pd
import streamlit as st

from database.database import fetch_past_questions
from helpers import sqlalchemy_model_to_dict
from quiz.quiz_summary_model import QuizSummary, init_quiz_summary_wf

# Display data
st.header("Past Questions")

# Past Questions table
past_questions = fetch_past_questions()
past_questions_df = pd.DataFrame(
    [sqlalchemy_model_to_dict(source) for source in past_questions]
)
# process datasources
past_questions_df.set_index("id", drop=True, inplace=True)
past_questions_df.sort_values(by="date", ascending=False, inplace=True)
past_questions_df.rename(
    columns={"question": "Question", "solved": "Was Solved?", "date": "Date"},
    inplace=True,
)

st.dataframe(
    past_questions_df,
    column_order=["Question", "Date", "Was Solved?"],
    hide_index=True,
)


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
gen_new = gen_new_container.button("New AI Evaluation")
if gen_new:
    gen_new_container.empty()
    status = st.status("Generating evaluation report ...")
    quiz_summary_wf = init_quiz_summary_wf("gpt-4o-mini")
    result = quiz_summary_wf.invoke({})
    status.update(label="Report generated", state="complete")
    st.rerun()
