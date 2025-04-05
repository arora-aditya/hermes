from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_embeddings_model() -> OpenAIEmbeddings:
    """
    Initialize and return OpenAI embeddings model.

    Returns:
        OpenAIEmbeddings: Configured embeddings model

    Raises:
        ValueError: If OpenAI API key is not configured
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        raise ValueError("OpenAI API key not configured")

    model = os.environ.get("OPENAI_TEXT_EMBEDDING_MODEL", "text-embedding-3-small")
    logger.debug(f"Initializing OpenAI embeddings with model: {model}")

    return OpenAIEmbeddings(
        api_key=api_key,
        model=model,
    )


def get_vector_store(
    collection_name: str = "my_docs",
    embeddings: Optional[OpenAIEmbeddings] = None,
) -> PGVector:
    """
    Initialize and return PGVector store instance.

    Args:
        collection_name: Name of the vector collection
        embeddings: Optional pre-configured embeddings model

    Returns:
        PGVector: Configured vector store

    Raises:
        ValueError: If database configuration is missing
    """
    try:
        logger.info(f"Initializing vector store for collection: {collection_name}")

        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("Database URL not found in environment variables")
            raise ValueError("Database URL not configured")

        # Use provided embeddings or create new ones
        embeddings_model = embeddings or get_embeddings_model()

        vector_store = PGVector(
            embeddings=embeddings_model,
            collection_name=collection_name,
            connection=db_url,
            use_jsonb=True,
        )

        logger.info("Vector store initialized successfully")
        return vector_store

    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)
        raise
