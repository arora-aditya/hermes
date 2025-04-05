from pydantic import BaseModel
import logging
from utils.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    query: str


class Search:
    def __init__(self):
        """Initialize the search service with PGVector."""
        try:
            logger.info("Initializing Search service")
            self.pgvector = get_vector_store()
            logger.info("Search service initialized successfully")
        except Exception as e:
            logger.error(
                f"Failed to initialize Search service: {str(e)}", exc_info=True
            )
            raise

    def search(self, query: str):
        """
        Perform similarity search using the vector store.

        Args:
            query: Search query string

        Returns:
            List of matching documents with similarity scores
        """
        try:
            logger.info(f"Performing similarity search with query: '{query}'")
            results = self.pgvector.similarity_search(query)
            logger.info(f"Search completed. Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}", exc_info=True)
            raise
