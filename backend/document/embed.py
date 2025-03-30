import os
from typing import List
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_postgres import PGVector
from uuid import uuid4


class Embeddings:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=os.environ["OPENAI_API_KEY"],
            model=os.environ.get(
                "OPENAI_TEXT_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
        )
        self.connection = f"postgresql+psycopg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
        self.pgvector = PGVector(
            embeddings=self.embeddings,
            collection_name="my_docs",
            connection=self.connection,
            use_jsonb=True,
        )

    def embed_docs(self, docs: List[Document]):
        document_ids = self.pgvector.add_documents(
            docs, ids=[str(uuid4()) for _ in docs]
        )
        return [document_ids]
