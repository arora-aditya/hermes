import os
from typing import List
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from uuid import uuid4
from utils.database import Database


class Embeddings:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=os.environ["OPENAI_API_KEY"],
            model=os.environ.get(
                "OPENAI_TEXT_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
        )
        self.db = Database()
        self.pgvector = PGVector(
            embeddings=self.embeddings,
            collection_name="my_docs",
            connection=self.db.get_db_url(),
            use_jsonb=True,
        )

    def embed_docs(self, docs: List[Document]):
        document_ids = self.pgvector.add_documents(docs)
        return [document_ids]
