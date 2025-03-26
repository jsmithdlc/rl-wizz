from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PastQuestion(Base):
    __tablename__ = "past_questions"
    id = Column(Integer, primary_key=True)
    question = Column(String)
    solved = Column(Boolean)
    date = Column(DateTime, unique=True)
