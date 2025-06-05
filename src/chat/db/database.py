import datetime
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from chat.db.models import Base, ChatSource, Conversation, ConversationTitle
from utils.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

DATABASE_URL = "sqlite:///data/conversations.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine)


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


def load_conversation_titles() -> dict[str, str]:
    """Load all conversation titles from db"""
    with SessionLocal() as session:
        titles = session.query(ConversationTitle).all()
        return {title.conversation_id: title.title for title in titles}


def fetch_conversation_title(conv_id: str) -> ConversationTitle | None:
    """Load conversation title associated to id `conv_id`"""
    with SessionLocal() as session:
        title = (
            session.query(ConversationTitle)
            .filter(ConversationTitle.conversation_id == conv_id)
            .first()
        )
        return title


def save_conversation(conv_id: str, messages: list[tuple[str, str]]):
    """Save a conversation to the database"""
    conversation = Conversation(
        id=conv_id, messages=messages, date=datetime.datetime.now()
    )
    with SessionLocal() as session:
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    return conversation


def save_conversation_title(conv_id: str, title: str):
    """Save conversation title to database"""
    conv_title = ConversationTitle(conversation_id=conv_id, title=title)
    with SessionLocal() as session:
        session.add(conv_title)
        session.commit()
        session.refresh(conv_title)
    return conv_title


def update_conversation(conv_id: str, messages: list[tuple[str, str]]):
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


def delete_conversation(conv_id: str):
    """Deletes conversation from database"""
    with SessionLocal() as session:
        session.query(Conversation).filter(Conversation.id == conv_id).delete()
        session.query(ConversationTitle).filter(
            ConversationTitle.conversation_id == conv_id
        ).delete()
        session.commit()


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


def fetch_all_chat_source() -> list[ChatSource]:
    """Fetches all ChatSource stored in database"""
    with SessionLocal() as session:
        return session.query(ChatSource).all()


def add_chat_source(source_name: str, doc_type: str, n_related_documents: int):
    """Stores new chat datasource. Replace existing one if already exists

    Args:
        source_name (str): name of this datasource. Can be filename, url, etc
        doc_type (str): document type
        n_related_documents (int): number of extracted documents associated to this datasource
    """
    with SessionLocal() as session:
        chat_source = (
            session.query(ChatSource)
            .filter(ChatSource.source_name == source_name)
            .first()
        )
        if not chat_source:
            chat_source = ChatSource(
                source_name=source_name,
                doc_type=doc_type,
                n_related_documents=n_related_documents,
                date_added=datetime.datetime.now(),
            )
            session.add(chat_source)
            session.commit()
        else:
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
    with SessionLocal() as session:
        chat_source = (
            session.query(ChatSource)
            .filter(ChatSource.source_name == source_name)
            .first()
        )
        if not chat_source:
            return
        chat_source.n_times_retrieved += new_calls
        session.commit()
        session.refresh(chat_source)
