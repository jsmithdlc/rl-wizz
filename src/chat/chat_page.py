import time

import streamlit as st

from chat.chat_model import init_chat_app, query_workflow_stream
from chat.vector_store import *
from helpers import stream_llm_response

st.set_page_config(
    page_title="Main",
    page_icon="assets/wizzard_penguin.ico",
    layout="wide",
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
    st.session_state.n_conversations = 0
    st.session_state.current_conversation = None


def render_human_prompt(prompt_text):
    st.markdown(
        f"""
    <div style='
        display: inline-block;
        float: right;
        padding: 0.5em;
        border-radius: 15px;
        text-align: right;
        color: {st.get_option("theme.textColor")};
        background-color: {st.get_option("theme.secondaryBackgroundColor")};
    '>
        {prompt_text}
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_chat_history():
    if st.session_state.current_conversation is not None:
        for role, msg in st.session_state.chat_history[
            st.session_state.current_conversation
        ]:
            if role == "ai":
                st.text(" ")
                st.markdown(msg)
                st.text(" ")
            else:
                render_human_prompt(msg)


def set_conversation(c_index):
    st.session_state.current_conversation = c_index


def render_chat_buttons():
    for i in range(1, st.session_state.n_conversations + 1):
        st.sidebar.button(
            f"Conversation {i}",
            use_container_width=True,
            on_click=set_conversation,
            args=[i],
        )


def store_temperature_value():
    st.session_state["model_temperature"] = st.session_state["_model_temperature"]


def on_new_conversation():
    st.session_state.n_conversations += 1
    st.session_state.chat_history[st.session_state.n_conversations] = []
    st.session_state.current_conversation = st.session_state.n_conversations


model_name = st.sidebar.selectbox("Chat model", ("gpt-4o-mini"))

chat_app = init_chat_app(
    model_name,
    temperature=(
        st.session_state["model_temperature"]
        if "model_temperature" in st.session_state
        else None
    ),
)


# save temperature in session
temperature = st.sidebar.slider(
    "Model temperature",
    0.0,
    1.0,
    value=(
        st.session_state["model_temperature"]
        if "model_temperature" in st.session_state
        else None
    ),
    key="_model_temperature",
    on_change=store_temperature_value,
)

st.sidebar.button(
    "New",
    help="Start a new conversation",
    type="primary",
    icon="📝",
    on_click=on_new_conversation,
)

render_chat_history()

render_chat_buttons()


if st.session_state.current_conversation is not None:
    prompt = st.chat_input(
        "Ask the RL Wizz to do its magic",
        accept_file=True,
        file_type=["jpg", "jpeg", "png"],
    )

    if prompt:
        current_conversation = st.session_state.current_conversation
        render_human_prompt(prompt.text)
        st.text(" ")
        llm_response = st.write_stream(
            stream_llm_response(
                query_workflow_stream(chat_app, prompt.text, current_conversation)
            )
        )
        st.text(" ")
        st.session_state.chat_history[current_conversation].extend(
            [("human", prompt.text), ("ai", llm_response)]
        )
