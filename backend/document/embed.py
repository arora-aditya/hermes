import os
from typing import List
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import DeterministicFakeEmbedding


class Embeddings:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            api_key=os.environ["OPENAI_API_KEY"],
            model=os.environ.get(
                "OPENAI_TEXT_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
        )

    def embed_docs(self, docs: List[Document]):
        contents = [doc.page_content for doc in docs]
        embeddings = [self.embeddings.embed_documents(content) for content in contents]
        return [len(embedding) for embedding in embeddings]
