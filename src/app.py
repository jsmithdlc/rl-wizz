"""
Application navigation
"""

import streamlit as st
import torch

# fixes issue with torch loading when using streamlit
torch.classes.__path__ = []


# Define the pages
main_page = st.Page("main_page.py", title="Welcome", icon=":material/home:")
chat_page = st.Page("chat/chat_page.py", title="Conversations", icon="📇")
chat_knowledge_page = st.Page("chat/chat_knowledge.py", title="RAG Sources", icon="🧐")
quiz_page = st.Page("quiz/quiz_page.py", title="Take Quiz", icon="🧠")
quiz_results = st.Page("quiz/quiz_results_page.py", title="View Results", icon="✅")

pg = st.navigation(
    {
        "": [main_page],
        "Chat": [chat_page, chat_knowledge_page],
        "Quiz": [quiz_page, quiz_results],
    }
)

st.set_page_config(
    page_title="RL Wizz",
    page_icon="assets/wizzard_penguin.ico",
    layout="wide",
)
pg.run()
