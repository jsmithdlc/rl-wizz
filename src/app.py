import streamlit as st

# Define the pages
main_page = st.Page("main_page.py", title="Main Page", icon=":material/home:")
page_2 = st.Page("chat_page.py", title="Chats", icon="📇")

pg = st.navigation([main_page, page_2])

pg.run()
