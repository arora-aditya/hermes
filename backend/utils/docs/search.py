from pydantic import BaseModel
import logging
from utils.vector_store import get_vector_store

# Set up logging
logging.basicConfig(level=logging.INFO)
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

            # Log the query embedding process
            logger.debug("Generating query embeddings")
            results = self.pgvector.similarity_search(query)

            # Log search results details
            logger.info(f"Search completed. Found {len(results)} results")
            if results:
                logger.debug("Top results metadata:")
                for i, result in enumerate(results[:3]):  # Log first 3 results
                    logger.debug(f"Result {i+1}:")
                    logger.debug(
                        f"  Document ID: {result.metadata.get('document_id', 'N/A')}"
                    )
                    logger.debug(f"  Page: {result.metadata.get('page', 'N/A')}")
                    logger.debug(f"  Content preview: {result.page_content[:100]}...")
            else:
                logger.warning("Search returned no results")

            return results
        except Exception as e:
            logger.error(f"Error during similarity search: {str(e)}", exc_info=True)
            raise
