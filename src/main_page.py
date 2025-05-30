"""
Sort of like the home page for the RL Wizz web-app
"""

import time

import streamlit as st

st.header("Reinforcement Learning Wizz")

media_col, _, _ = st.columns([0.6, 0.2, 0.2])
container = media_col.empty()
container.image(
    "assets/rl_wizz.webp",
    caption="The RL wizz exploring a virgin landscape. *Created with ChatGPT and Sora",
)
st.markdown(
    "This is a mighty and powerful wizard that will guide you through "
    "the convoluted maze of reinforcement learning and help your through "
    "your experimentation and adventure into this fantastic realm."
)
but = st.button("Start Journey", icon="💫")
if but:
    container.empty()
    vid = container.video(
        "assets/whimsical_wizzard_journey.mp4", autoplay=True, muted=True
    )
    time.sleep(5)
    st.switch_page("chat/chat_page.py")
