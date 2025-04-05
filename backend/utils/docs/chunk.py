from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List


class Chunk:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )

    def chunk_docs(self, docs: List[Document]) -> List[Document]:
        chunks = self.text_splitter.split_documents(docs)
        # Ensure each chunk preserves the document_id from its parent document
        for chunk in chunks:
            if hasattr(chunk, "metadata"):
                # Get document_id from parent document's metadata if it exists
                parent_metadata = chunk.metadata
                if "document_id" in parent_metadata:
                    chunk.metadata["document_id"] = parent_metadata["document_id"]
        return chunks
