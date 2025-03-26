import streamlit as st

from chat_model import stream_llm_response
from quiz_model import ask_question_stream, evaluate_answer_stream, init_quiz_app

st.set_page_config(
    page_title="Home",
    page_icon="assets/wizzard_penguin.ico",
    layout="wide",
)

st.header("Reinforcement Learning Wizz")

container = st.container()
container.image(
    "assets/rl_wizz.webp",
    width=600,
    caption="The RL wizz exploring a virgin landscape",
)
container.markdown(
    "This is a mighty and powerful wizard that will guide you through the convoluted maze of reinforcement learning "
    "and help your through your experimentation and adventure into this fantastic realm."
)
