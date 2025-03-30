from langchain_community.document_loaders import PyPDFLoader
from pydantic import BaseModel
from pydantic import Field


class IngestRequest(BaseModel):
    url: str = Field(
        default="/Users/adityaarora/github/arora-aditya.github.io/public/files/Resume.pdf"
    )


class Ingest:
    def __init__(self):
        pass

    def ingest_docs(self, file_path: str):
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return docs
