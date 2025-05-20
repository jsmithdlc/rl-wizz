"""
Models for SQLite Database
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PastQuestion(Base):
    """
    Question information from Quiz
    """

    __tablename__ = "past_questions"
    id = Column(Integer, primary_key=True)
    question = Column(String)
    solved = Column(Boolean)
    date = Column(DateTime, unique=True)


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
