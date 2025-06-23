"""Module for managing vector storage of documents using Pinecone and LangChain."""

import logging
import os
from typing import Literal

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
def _add_documents_to_vector_store(
    documents: list[Document], source_type: Literal["pdf", "website"]
):
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
        source_id_key="source" if source_type == "pdf" else "url",
    )
    logging.info("Added documents to pinecone DB")


def source_to_vector_store(source_path: str, source_type: Literal["pdf", "website"]):
    """
    Processes and adds a source into the vector store

    Args:
        source_path (str): path to source file or url
        source_type (Literal[str]): type of source. Can be pdf or website for now.
    """
    if source_type == "pdf":
        loader = UnstructuredLoader(
            file_path=source_path,
            strategy="hi_res",
            post_processors=[clean_extra_whitespace],
        )
        docs = [
            doc for doc in loader.lazy_load() if doc.metadata.pop("coordinates", None)
        ]
    elif source_type == "website":
        loader = UnstructuredLoader(web_url=source_path)
        docs = list(loader.lazy_load())
    else:
        raise ValueError("Unrecognized source_type %s", source_type)
    logging.info("Retrieved: %s documents from pdf", len(docs))
    print(f"Docs: {docs}")
    if len(docs) > 0:
        _add_documents_to_vector_store(docs, source_type)
        add_chat_source(
            source_name=source_path,
            doc_type="pdf",
            n_related_documents=len(docs),
        )
