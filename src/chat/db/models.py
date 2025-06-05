import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Conversation(Base):
    """A conversation between a user and LLM"""

    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.now)
    messages = Column(JSON)


class ConversationTitle(Base):
    """A title for a conversation between user and LLM"""

    __tablename__ = "conversations_titles"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, ForeignKey(Conversation.id))
    title = Column(String)


class ChatSource(Base):
    """
    Source uploaded by user to be used in Chatbot RAG
    """

    __tablename__ = "chat_source"
    id = Column(Integer, primary_key=True)
    source_name = Column(String, unique=True)
    doc_type = Column(String)
    n_related_documents = Column(Integer)
    date_added = Column(DateTime)
    n_times_retrieved = Column(Integer, default=0)
