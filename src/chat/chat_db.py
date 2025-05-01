import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Integer, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from utils.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

DATABASE_URL = "sqlite:///data/conversations.db"

Base = declarative_base()

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)


class Conversation(Base):
    """A conversation between a user and an AI"""

    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.datetime.now)
    messages = Column(JSON)


def init_db():
    """Initialize the database and create tables if they don't exist"""
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")

        # Verify table exists
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
                )
            )
            if result.fetchone() is None:
                raise SQLAlchemyError("Table 'conversations' was not created")
            logger.info("Verified 'conversations' table exists")
    except SQLAlchemyError as e:
        logger.error("Error initializing database: %s", str(e))
        raise


# Initialize database on module import
init_db()


def load_conversations_as_dict() -> list[dict[str, Any]]:
    """Load all conversations from the database"""
    with SessionLocal() as session:
        conversations = session.query(Conversation).all()
        return {conv.id: conv.messages for conv in conversations}


def save_conversation(conv_id: int, messages: list[tuple[str, str]]):
    """Save a conversation to the database"""
    conversation = Conversation(
        id=conv_id, messages=messages, date=datetime.datetime.now()
    )
    with SessionLocal() as session:
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    return conversation


def update_conversation(conv_id: int, messages: list[tuple[str, str]]):
    """Update a conversation in the database"""
    with SessionLocal() as session:
        conversation = (
            session.query(Conversation).filter(Conversation.id == conv_id).first()
        )
        if conversation:
            conversation.messages = messages
            session.commit()
            session.refresh(conversation)
            return conversation
        return None
