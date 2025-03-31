import streamlit as st
import torch

# fixes issue with torch loading when using streamlit
torch.classes.__path__ = []


# Define the pages
main_page = st.Page("main_page.py", title="Main Page", icon=":material/home:")
chat_page = st.Page("chat/chat_page.py", title="Chats", icon="📇")
quiz_page = st.Page("quiz/quiz_page.py", title="Knowledge Quiz", icon="🧠")

pg = st.navigation([main_page, chat_page, quiz_page])


pg.run()
