from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List


class Chunk:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )

    def chunk_docs(self, docs: List[Document]):
        return self.text_splitter.split_documents(docs)
