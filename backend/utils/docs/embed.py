import os
from typing import List
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from uuid import uuid4
from utils.database import Database
import logging
from utils.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class Embeddings:
    def __init__(self):
        """Initialize the embeddings service with PGVector."""
        try:
            logger.info("Initializing Embeddings service")
            self.pgvector = get_vector_store()
            logger.info("Embeddings service initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize Embeddings service: {str(e)}", exc_info=True
            )
            raise

    def embed_docs(self, docs: List[Document]):
        """
        Embed documents and store them in the vector database.

        Args:
            docs: List of documents to embed

        Returns:
            List of document IDs for the embedded documents
        """
        try:
            logger.info(f"Starting document embedding for {len(docs)} documents")

            # Log document details before embedding
            for i, doc in enumerate(docs):
                logger.debug(
                    f"Document {i+1}: "
                    f"metadata={doc.metadata}, "
                    f"content_length={len(doc.page_content)}, "
                    f"user_id={doc.metadata.get('user_id', 'not_set')}"
                )

            # Add documents to vector store
            logger.debug("Adding documents to vector store")
            document_ids = self.pgvector.add_documents(docs)

            # Log embedding results
            logger.info(f"Embedding complete. Created {len(document_ids)} embeddings")
            logger.debug(f"Document IDs: {document_ids}")

            return document_ids

        except Exception as e:
            logger.error(f"Error during document embedding: {str(e)}", exc_info=True)
            raise
