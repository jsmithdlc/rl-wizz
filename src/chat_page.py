import time

import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from chat_model import init_chat_app, query_workflow_stream, stream_llm_response

st.set_page_config(
    page_title="Main",
    page_icon="assets/wizzard_penguin.ico",
    layout="wide",
)


# TODO: replace by LangChain stream response format
def stream_response(response_text: str):
    for word in response_text.split(" "):
        yield word + " "
        time.sleep(0.1)


def store_temperature_value():
    st.session_state["model_temperature"] = st.session_state["_model_temperature"]


def print_human_prompt(prompt_text):
    st.markdown(
        f"""
    <div style='
        display: inline-block;
        float: right;
        padding: 1em;
        border-radius: 20px;
        text-align: right;
        color: {st.get_option("theme.textColor")};
        background-color: {st.get_option("theme.secondaryBackgroundColor")};
    '>
        {prompt_text}
    </div>
    """,
        unsafe_allow_html=True,
    )


model_name = st.sidebar.selectbox("Chat model", ("gpt-4o-mini"))
chat_app = init_chat_app(model_name)


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


# TODO: retrieve from db
c = st.sidebar.container()
for i in range(4):
    st.sidebar.button(
        f"Convesation: {i}",
        use_container_width=True,
        type="secondary",
    )

prompt = st.chat_input(
    "Ask the RL Wizz to do its magic",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if prompt:
    print_human_prompt(prompt.text)
    st.write_stream(
        stream_llm_response(query_workflow_stream(chat_app, prompt.text, "0"))
    )
