"""
Page for chating with LLM. User can upload documents and interact with them through the LLM
"""

import os
import uuid

import streamlit as st

from chat.chat_db import (
    delete_conversation,
    fetch_conversation_title,
    load_conversations_as_dict,
    save_conversation,
    update_conversation,
)
from chat.chat_model import chat_stream, init_chat_app
from chat.vector_store import pdf_to_vector_store
from helpers import stream_llm_response_with_status

RAG_DOCUMENTS_DIR = "./data/rag"

os.makedirs(RAG_DOCUMENTS_DIR, exist_ok=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_conversations_as_dict()
    st.session_state.conversation_ids = list(st.session_state.chat_history.keys())
    st.session_state.conversations_titles = {}
    st.session_state.current_conversation = None


def render_human_msg(prompt_text: str):
    """
    Renders the user-generated text right-aligned in the chat interface
    """
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
            render_human_msg(msg)


def on_set_conversation(c_index: str):
    """Sets conversation with id: `c_index` as the current selected one"""
    st.session_state.current_conversation = c_index


def get_conversation_title(c_index: str) -> str | None:
    """Gets the conversation title, if any."""
    if c_index in st.session_state.conversations_titles:
        return st.session_state.conversations_titles[c_index]
    conv_title = fetch_conversation_title(c_index)
    if conv_title is None:
        return None
    st.session_state.conversations_titles[c_index] = conv_title.title
    return conv_title.title


@st.dialog("Confirm deletion")
def on_delete_conversation(c_index: str):
    """Prompts confirmation dialog for erasing conversation with id `c_index`"""
    st.markdown(
        "**This conversation will be deleted** from the database and will not be accessible later"
    )
    confirm = st.button("Confirm")
    if confirm:
        st.session_state.current_conversation = (
            None
            if st.session_state.current_conversation == c_index
            else st.session_state.current_conversation
        )
        if c_index in st.session_state.conversations_titles:
            del st.session_state.conversations_titles[c_index]
        del st.session_state.chat_history[c_index]
        st.session_state.conversation_ids.remove(c_index)
        delete_conversation(c_index)
        st.rerun()


def on_new_conversation():
    """Adds a new conversation with a random id"""
    new_id = str(uuid.uuid4())
    st.session_state.conversation_ids.append(new_id)
    st.session_state.chat_history[new_id] = []
    st.session_state.current_conversation = new_id
    save_conversation(new_id, [])


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
    for conv_id in st.session_state.conversation_ids:
        col1, col2 = st.sidebar.columns([0.9, 0.05])
        with col1:
            conv_title = get_conversation_title(conv_id)
            st.button(
                (f"Conversation {conv_id[-4:]}" if conv_title is None else conv_title),
                on_click=on_set_conversation,
                use_container_width=True,
                args=[conv_id],
                key=f"conv_selector_{conv_id}",
            )
        with col2:
            st.button(
                ":wastebasket:",
                key=f"conv_deletor_{conv_id}",
                on_click=on_delete_conversation,
                args=[conv_id],
                use_container_width=True,
                type="tertiary",
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
        coco_title = get_conversation_title(current_conversation)
        render_human_msg(prompt.text)
        llm_response = st.write_stream(
            stream_llm_response_with_status(
                chat_stream(
                    chat_app,
                    prompt.text,
                    current_conversation,
                    coco_title is not None,
                ),
                "Generating",
            )
        )
        st.text(" ")
        new_messages = [("human", prompt.text), ("ai", llm_response)]
        # update session state with new messages
        st.session_state.chat_history[current_conversation].extend(new_messages)
        update_conversation(
            current_conversation, st.session_state.chat_history[current_conversation]
        )
        if (
            coco_title is None
            and get_conversation_title(current_conversation) is not None
        ):
            st.rerun()
else:
    _, col2, _ = st.columns((0.2, 0.6, 0.2), vertical_alignment="center")
    container = col2.container(border=True)
    container.markdown("""Hi there 👋 here you can:""")
    container.button(
        "Start a new conversation.",
        type="secondary",
        icon="📝",
        on_click=on_new_conversation,
    )
    container.button(
        "Add new sources to the chatbot's knowledge base.",
        type="secondary",
        icon="📚",
        on_click=add_material_dialog,
    )
