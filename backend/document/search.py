from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from pydantic import BaseModel
import os


class SearchRequest(BaseModel):
    query: str


class Search:
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
        print(self.connection)

    def search(self, query: SearchRequest):
        return self.pgvector.similarity_search(query.query)
