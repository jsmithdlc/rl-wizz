"""
Module for communicating to general SQLite database
"""

import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, ChatSource, PastQuestion

DATABASE_URL = "sqlite:///data/database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)


def add_question(question: str, solved: bool):
    """Stores new quiz question in database

    Args:
        question (str): question to store
        solved (bool): whether user answered this question correctly
    """
    with SessionLocal() as session:
        user = PastQuestion(
            question=question, solved=solved, date=datetime.datetime.now()
        )
        session.add(user)
        session.commit()


def fetch_past_questions() -> list[PastQuestion]:
    """Fetch all past questions
    Returns:
        list[PastQuestion]: list of stored questions
    """

    with SessionLocal() as session:
        return session.query(PastQuestion).order_by(PastQuestion.date.desc()).all()


def fetch_chat_source_by_name(source_name: str) -> ChatSource | None:
    """Fetch chat source by its name

    Args:
        source_name (str): name of the data source to fetch

    Returns:
        ChatSource | None: the retrieved data source, if any
    """
    with SessionLocal() as session:
        return (
            session.query(ChatSource)
            .filter(ChatSource.source_name == source_name)
            .first()
        )


def add_chat_source(source_name: str, doc_type: str, n_related_documents: int):
    """Stores new chat datasource. Replace existing one if already exists

    Args:
        source_name (str): name of this datasource. Can be filename, url, etc
        doc_type (str): document type
        n_related_documents (int): number of extracted documents associated to this datasource
    """
    chat_source = fetch_chat_source_by_name(source_name)
    if not chat_source:
        with SessionLocal() as session:
            chat_source = ChatSource(
                source_name=source_name,
                doc_type=doc_type,
                n_related_documents=n_related_documents,
                date_added=datetime.datetime.now(),
            )
            session.add(chat_source)
            session.commit()
    else:
        with SessionLocal() as session:
            chat_source.doc_type = doc_type
            chat_source.n_related_documents = n_related_documents
            chat_source.date_added = datetime.datetime.now()
            session.commit()
            session.refresh(chat_source)


def update_chat_source_n_retrieved(source_name: str, new_calls: int):
    """Updates the number of retrieval of source by summing new calls

    Args:
        source_name (str): data source name
        new_calls (int): count of new retrievals for this data source
    """
    chat_source = fetch_chat_source_by_name(source_name)
    if not chat_source:
        return
    with SessionLocal() as session:
        chat_source.n_times_retrieved += new_calls
        session.commit()
        session.refresh(chat_source)
