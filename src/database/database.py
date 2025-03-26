import datetime
import os

import streamlit as st
from models import Base, PastQuestion
from sqlalchemy import Column, Integer, String, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///data/database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# Set SQLite PRAGMA for improved persistence & concurrency
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=EXTRA;")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)


# Functions to interact with DB
def add_question(question, solved):
    with SessionLocal() as session:
        user = PastQuestion(
            question=question, solved=solved, date=datetime.datetime.now()
        )
        session.add(user)
        session.commit()


def fetch_past_questions():
    with SessionLocal() as session:
        return session.query(PastQuestion).all()
