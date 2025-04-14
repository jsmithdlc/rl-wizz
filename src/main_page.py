"""
Sort of like the home page for the RL Wizz web-app
"""

import streamlit as st

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
    "This is a mighty and powerful wizard that will guide you through "
    "the convoluted maze of reinforcement learning and help your through "
    "your experimentation and adventure into this fantastic realm."
)
