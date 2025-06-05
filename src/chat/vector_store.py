"""Module for managing vector storage of documents using Pinecone and LangChain."""

import logging
import os

import pinecone as pc
from dotenv import load_dotenv
from langchain.indexes import SQLRecordManager, index
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_unstructured import UnstructuredLoader
from unstructured.cleaners.core import clean_extra_whitespace

from chat.db.database import add_chat_source

load_dotenv()

# initialize pinecone index
pinecone_index = pc.Index(
    api_key=os.environ["PINECONE_API_KEY"], host=os.environ["PINECONE_INDEX_HOST"]
)

# initialize embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# initialize vector store
vector_store = PineconeVectorStore(index=pinecone_index, embedding=embeddings)

# record manager (keeps track of document index)
record_manager = SQLRecordManager(
    "pinecone/rl-wizz-rag", db_url="sqlite:///data/record_manager_cache.sql"
)
record_manager.create_schema()


# TODO: avoid adding duplicate content from same pdf with different sources.
def _add_documents_to_vector_store(documents: list[Document]):
    """Add documents to vector store"""
    prep_docs = []
    for doc in documents:
        if "links" in doc.metadata:
            del doc.metadata["links"]
        prep_docs.append(doc)

    index(
        prep_docs,
        record_manager=record_manager,
        vector_store=vector_store,
        cleanup="incremental",
        source_id_key="source",
    )
    logging.info("Added documents to pinecone DB")


def pdf_to_vector_store(pdf_path: str):
    """Load PDF and store in vector store"""
    loader = UnstructuredLoader(
        file_path=pdf_path, strategy="hi_res", post_processors=[clean_extra_whitespace]
    )
    docs = [doc for doc in loader.lazy_load() if doc.metadata.pop("coordinates", None)]
    logging.info("Retrieved: %s documents from pdf", len(docs))
    if len(docs) > 0:
        _add_documents_to_vector_store(docs)
        add_chat_source(
            source_name=pdf_path,
            doc_type="pdf",
            n_related_documents=len(docs),
        )
