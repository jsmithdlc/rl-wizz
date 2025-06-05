import pandas as pd
import plotly.express as px
import streamlit as st

from chat.db.database import fetch_all_chat_source
from helpers import sqlalchemy_model_to_dict

# load datasources
chat_sources = fetch_all_chat_source()
if len(chat_sources) == 0:
    st.info("No sources have been added! Nothing to show here")
    st.stop()
chat_sources_df = pd.DataFrame(
    [sqlalchemy_model_to_dict(source) for source in chat_sources]
)
# process datasources
chat_sources_df.set_index("id", drop=True, inplace=True)

st.markdown(
    """
    ## Source Information

    This is an overview of the data contained in the vector store for RAG in chat conversations.
    """
)
st.dataframe(chat_sources_df)

st.markdown(
    """
    ### Document distribution per source
    """
)
fig = px.pie(
    chat_sources_df,
    values="n_related_documents",
    names="source_name",
    color="source_name",
)
st.plotly_chart(fig)

st.markdown(
    """
    ## User Interaction

    This section provides information related to user interaction
    with the documents in the vector store through the conversations.
    """
)
st.bar_chart(
    chat_sources_df,
    x="source_name",
    x_label="Source",
    y="n_times_retrieved",
    y_label="N. times retrieved",
    color=(255, 0, 0),
)
