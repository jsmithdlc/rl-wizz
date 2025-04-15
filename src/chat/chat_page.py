"""
Page for chating with LLM. User can upload documents and interact with them through the LLM
"""

import os

import streamlit as st

from chat.chat_model import chat_stream, init_chat_app
from chat.vector_store import pdf_to_vector_store
from helpers import stream_llm_response

RAG_DOCUMENTS_DIR = "./data/rag"

os.makedirs(RAG_DOCUMENTS_DIR, exist_ok=True)

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


def on_new_conversation():
    st.session_state.n_conversations += 1
    st.session_state.chat_history[st.session_state.n_conversations] = []
    st.session_state.current_conversation = st.session_state.n_conversations


def load_pdfs(files):
    for uploaded_file in files:
        st.write(f"adding {uploaded_file.name} to database")
        file_path = os.path.join(RAG_DOCUMENTS_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        pdf_to_vector_store(file_path)


@st.dialog("Add material")
def add_material_dialog():
    selected_option = st.pills("Type", ["pdf", "website"])
    if selected_option == "pdf":
        files_container = st.empty()
        files = files_container.file_uploader("Upload pdf", accept_multiple_files=True)
        if len(files) > 0:
            confirm_container = st.empty()
            confirm = confirm_container.button("Confirm", args=[files])
            if confirm:
                files_container.empty()
                confirm_container.empty()
                st.markdown(
                    ":warning: Please **don't navigate away** while processing files"
                )
                with st.status("Processing files"):
                    load_pdfs(files)
                st.rerun()


def render_chat_buttons():
    """
    Render buttons for chat management (creating/choosing conversation, adding new material for RAG)
    """
    # buttons for adding new conversation and adding new files
    cols = st.sidebar.columns(3)
    cols[0].button(
        "New",
        help="Start a new conversation",
        type="primary",
        icon="📝",
        on_click=on_new_conversation,
    )
    cols[1].button(
        "Add",
        help="Add documents / media to enhance this bot's knowledge",
        type="primary",
        icon="📚",
        on_click=add_material_dialog,
    )
    # buttons to pick conversations
    for i in range(1, st.session_state.n_conversations + 1):
        st.sidebar.button(
            f"Conversation {i}",
            use_container_width=True,
            on_click=set_conversation,
            args=[i],
        )


def store_temperature_value():
    st.session_state["model_temperature"] = st.session_state["_model_temperature"]


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

render_chat_buttons()

# Layout for current conversation
if st.session_state.current_conversation is not None:
    render_chat_history()
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
                chat_stream(chat_app, prompt.text, current_conversation)
            )
        )
        st.text(" ")
        st.session_state.chat_history[current_conversation].extend(
            [("human", prompt.text), ("ai", llm_response)]
        )
