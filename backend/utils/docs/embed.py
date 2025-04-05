import os
from typing import List
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from uuid import uuid4
from utils.database import Database
import logging

logger = logging.getLogger(__name__)


class Embeddings:
    def __init__(self):
        """Initialize the embeddings service with OpenAI and PGVector."""
        try:
            logger.info("Initializing Embeddings service")

            # Initialize OpenAI embeddings
            api_key = os.environ.get("OPENAI_API_KEY")
            model = os.environ.get(
                "OPENAI_TEXT_EMBEDDING_MODEL", "text-embedding-3-small"
            )

            if not api_key:
                logger.error("OpenAI API key not found in environment variables")
                raise ValueError("OpenAI API key not configured")

            logger.debug(f"Initializing OpenAI embeddings with model: {model}")
            self.embeddings = OpenAIEmbeddings(
                api_key=api_key,
                model=model,
            )

            # Initialize database connection
            logger.debug("Initializing database connection")
            self.db = Database()

            # Initialize PGVector
            logger.debug("Initializing PGVector")
            self.pgvector = PGVector(
                embeddings=self.embeddings,
                collection_name="my_docs",
                connection=self.db.get_db_url(),
                use_jsonb=True,
            )

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
                    f"content_length={len(doc.page_content)}"
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
