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
    """Adds a list of langchain documents into the specified vector store

    Args:
        documents (list[Document]): list of documents to add
    """
    index(
        documents,
        record_manager=record_manager,
        vector_store=vector_store,
        cleanup="incremental",
        source_id_key="source",
    )
    logging.info("successfully added documents to pinecone vector database")


def pdf_to_vector_store(pdf_path: str):
    """Loads a pdf, collects documents from it and stores them into the vector store

    Args:
        pdf_path (str): _description_
    """
    loader_local = UnstructuredLoader(
        file_path=pdf_path, strategy="hi_res", post_processors=[clean_extra_whitespace]
    )
    docs = []
    for doc in loader_local.lazy_load():
        del doc.metadata["coordinates"]
        docs.append(doc)
    logging.info("Retrieved: %s documents from pdf", len(docs))
    _add_documents_to_vector_store(docs)
