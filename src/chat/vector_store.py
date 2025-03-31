import os
from uuid import uuid4

import pinecone as pc
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

load_dotenv()

print("INITIALIZING EVERYTHING")
# initialize pinecone index
pinecone_index = pc.Index("rl-wizz-rag", host=os.environ["PINECONE_INDEX_HOST"])

# initialize embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# initialize vector store
vector_store = PineconeVectorStore(index=pinecone_index, embedding=embeddings)


def add_documents(documents: list[Document]):
    uuids = [str(uuid4()) for _ in range(len(documents))]
    vector_store.add_documents(documents=documents, ids=uuids)


def add_pdf():
    ...
