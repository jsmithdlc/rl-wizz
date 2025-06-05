"""
Module for communicating to general SQLite database
"""

import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, PastQuestion

DATABASE_URL = "sqlite:///data/database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)


def add_question(question: str, solved: bool, answer: str, feedback: str):
    """Stores new quiz question in database

    Args:
        question (str): question to store
        solved (bool): whether user answered this question correctly
        answer (str): user's answer to the question
        feedback (str): feedback provided by LLM with respect to answer to the question
    """
    with SessionLocal() as session:
        user = PastQuestion(
            question=question,
            solved=solved,
            answer=answer,
            feedback=feedback,
            date=datetime.datetime.now(),
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
