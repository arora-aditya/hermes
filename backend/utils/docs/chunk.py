from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
import logging

logger = logging.getLogger(__name__)


class Chunk:
    def __init__(self):
        """Initialize the text splitter with specific configuration."""
        logger.info("Initializing Chunk service")
        try:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200, add_start_index=True
            )
            logger.debug("Text splitter initialized with chunk_size=1000, overlap=200")
        except Exception as e:
            logger.error(f"Failed to initialize Chunk service: {str(e)}", exc_info=True)
            raise

    def chunk_docs(self, docs: List[Document]) -> List[Document]:
        """
        Split documents into chunks for processing.

        Args:
            docs: List of documents to chunk

        Returns:
            List of chunked documents
        """
        try:
            logger.info(f"Starting document chunking for {len(docs)} documents")

            # Log document details before chunking
            for i, doc in enumerate(docs):
                logger.debug(
                    f"Document {i+1}: "
                    f"metadata={doc.metadata}, "
                    f"content_length={len(doc.page_content)}"
                )

            chunks = self.text_splitter.split_documents(docs)

            # Log chunking results
            logger.info(f"Chunking complete. Created {len(chunks)} chunks")
            logger.debug(
                f"Average chunk size: {sum(len(c.page_content) for c in chunks) / len(chunks):.0f} characters"
            )

            # Ensure each chunk preserves both document_id and user_id from its parent document
            for i, chunk in enumerate(chunks):
                if hasattr(chunk, "metadata"):
                    parent_metadata = chunk.metadata
                    # Preserve document_id
                    if "document_id" in parent_metadata:
                        chunk.metadata["document_id"] = parent_metadata["document_id"]
                        logger.debug(
                            f"Chunk {i+1}: Preserved document_id={parent_metadata['document_id']}"
                        )
                    # Preserve user_id
                    if "user_id" in parent_metadata:
                        chunk.metadata["user_id"] = parent_metadata["user_id"]
                        logger.debug(
                            f"Chunk {i+1}: Preserved user_id={parent_metadata['user_id']}"
                        )

            return chunks

        except Exception as e:
            logger.error(f"Error during document chunking: {str(e)}", exc_info=True)
            raise
